import json
from collections.abc import AsyncIterator
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.models import TaskRecord, TaskStatus, task_from_document, utc_now

TERMINAL_STATUSES = {
    TaskStatus.SUCCEEDED.value,
    TaskStatus.FAILED.value,
    TaskStatus.CANCELED.value,
}


async def create_task(
    database: AsyncIOMotorDatabase,
    user_id: str,
    notebook_id: str,
    task_type: str,
    payload: dict[str, Any],
) -> TaskRecord:
    now = utc_now()
    document = {
        "userId": user_id,
        "notebookId": notebook_id,
        "taskType": task_type,
        "payload": payload,
        "status": TaskStatus.QUEUED.value,
        "progress": 0,
        "message": "queued",
        "result": None,
        "error": None,
        "createdAt": now,
        "updatedAt": now,
    }
    result = await database.background_tasks.insert_one(document)
    document["_id"] = result.inserted_id
    return task_from_document(document)


async def get_task_or_throw(database: AsyncIOMotorDatabase, task_id: str) -> TaskRecord:
    object_id = parse_object_id(task_id)
    document = await database.background_tasks.find_one({"_id": object_id})
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task not found: {task_id}"
        )
    return task_from_document(document)


async def stream_task_events(
    database: AsyncIOMotorDatabase,
    request: Request,
    task_id: str,
    heartbeat_interval: float = 15.0,
) -> AsyncIterator[str]:
    object_id = parse_object_id(task_id)
    pipeline = [
        {
            "$match": {
                "documentKey._id": object_id,
                "operationType": {"$in": ["replace", "update", "delete"]},
            }
        }
    ]

    try:
        async with database.background_tasks.watch(
            pipeline,
            full_document="updateLookup",
            max_await_time_ms=int(heartbeat_interval * 1000),
        ) as change_stream:
            document = await database.background_tasks.find_one({"_id": object_id})
            if document is None:
                yield format_sse("deleted", json.dumps({"taskId": task_id}))
                return

            task = task_from_document(document)
            yield serialize_task_event(task)
            if task.status in TERMINAL_STATUSES:
                return

            while change_stream.alive:
                if await request.is_disconnected():
                    return

                change = await change_stream.try_next()
                if change is None:
                    yield format_sse("heartbeat", json.dumps({"taskId": task_id}))
                    continue

                if change["operationType"] == "delete":
                    yield format_sse("deleted", json.dumps({"taskId": task_id}))
                    return

                updated_document = change.get("fullDocument")
                if updated_document is None:
                    updated_document = await database.background_tasks.find_one(
                        {"_id": object_id}
                    )
                if updated_document is None:
                    yield format_sse("deleted", json.dumps({"taskId": task_id}))
                    return

                task = task_from_document(updated_document)
                yield serialize_task_event(task)
                if task.status in TERMINAL_STATUSES:
                    return
    except PyMongoError as exc:
        yield format_sse(
            "error",
            json.dumps(
                {
                    "detail": "MongoDB change streams are unavailable. Run MongoDB as a replica set or sharded cluster.",
                    "error": str(exc),
                }
            ),
        )


async def stream_notebook_task_events(
    database: AsyncIOMotorDatabase,
    request: Request,
    notebook_id: str,
    heartbeat_interval: float = 5.0,
) -> AsyncIterator[str]:
    pipeline = [
        {
            "$match": {
                "operationType": {"$in": ["insert", "replace", "update", "delete"]},
                "fullDocument.notebookId": notebook_id,
            }
        }
    ]

    try:
        async with database.background_tasks.watch(
            pipeline,
            full_document="updateLookup",
            max_await_time_ms=int(heartbeat_interval * 1000),
        ) as change_stream:
            summary = await build_notebook_task_summary(database, notebook_id)
            yield serialize_notebook_task_event(summary)
            if summary["allCompleted"]:
                return

            while change_stream.alive:
                if await request.is_disconnected():
                    return

                change = await change_stream.try_next()
                if change is None:
                    yield format_sse(
                        "heartbeat",
                        json.dumps({"notebookId": notebook_id}),
                    )
                    continue

                summary = await build_notebook_task_summary(database, notebook_id)
                yield serialize_notebook_task_event(summary)
                if summary["allCompleted"]:
                    return
    except PyMongoError as exc:
        yield format_sse(
            "error",
            json.dumps(
                {
                    "detail": "MongoDB change streams are unavailable. Run MongoDB as a replica set or sharded cluster.",
                    "error": str(exc),
                }
            ),
        )


async def build_notebook_task_summary(
    database: AsyncIOMotorDatabase,
    notebook_id: str,
) -> dict[str, Any]:
    documents = (
        await database.background_tasks.find({"notebookId": notebook_id})
        .sort("createdAt", 1)
        .to_list(length=None)
    )
    tasks = [task_from_document(document) for document in documents]
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.status in TERMINAL_STATUSES)
    overall_progress = calculate_overall_progress(tasks)
    all_completed = total_tasks > 0 and completed_tasks == total_tasks
    latest_updated_at = max((task.updatedAt for task in tasks), default=None)
    return {
        "notebookId": notebook_id,
        "totalTasks": total_tasks,
        "completedTasks": completed_tasks,
        "overallProgress": overall_progress,
        "allCompleted": all_completed,
        "latestUpdatedAt": latest_updated_at.isoformat() if latest_updated_at else None,
        "tasks": [task.model_dump(mode="json") for task in tasks],
    }


def parse_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid task id: {value}"
        ) from exc


def serialize_task_event(task: TaskRecord) -> str:
    event = (
        task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
    )
    return format_sse(
        event=event, data=task.model_dump_json(), event_id=event_id_for_task(task)
    )


def serialize_notebook_task_event(summary: dict[str, Any]) -> str:
    event = "done" if summary["allCompleted"] else "progress"
    latest_updated_at = summary["latestUpdatedAt"] or "none"
    return format_sse(
        event=event,
        data=json.dumps(summary),
        event_id=f"{summary['notebookId']}:{latest_updated_at}",
    )


def calculate_overall_progress(tasks: list[TaskRecord]) -> int:
    if not tasks:
        return 0
    return round(sum(task.progress for task in tasks) / len(tasks))


def event_id_for_task(task: TaskRecord) -> str:
    return f"{task.id}:{task.updatedAt.isoformat()}"


def format_sse(event: str, data: str, event_id: str | None = None) -> str:
    payload = data.replace("\r\n", "\n").replace("\r", "\n")
    lines = payload.split("\n")
    serialized = "\n".join(f"data: {line}" for line in lines)
    id_line = f"id: {event_id}\n" if event_id else ""
    return f"{id_line}event: {event}\n{serialized}\n\n"
