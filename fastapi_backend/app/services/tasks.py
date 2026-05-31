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
    task_type: str,
    payload: dict[str, Any],
) -> TaskRecord:
    now = utc_now()
    document = {
        "userId": user_id,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task not found: {task_id}")
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
            print('document: ', document)
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
                    updated_document = await database.background_tasks.find_one({"_id": object_id})
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


def parse_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid task id: {value}") from exc


def serialize_task_event(task: TaskRecord) -> str:
    event = task.status.value if isinstance(task.status, TaskStatus) else str(task.status)
    return format_sse(event=event, data=task.model_dump_json(), event_id=event_id_for_task(task))


def event_id_for_task(task: TaskRecord) -> str:
    return f"{task.id}:{task.updatedAt.isoformat()}"


def format_sse(event: str, data: str, event_id: str | None = None) -> str:
    payload = data.replace("\r\n", "\n").replace("\r", "\n")
    lines = payload.split("\n")
    serialized = "\n".join(f"data: {line}" for line in lines)
    id_line = f"id: {event_id}\n" if event_id else ""
    return f"{id_line}event: {event}\n{serialized}\n\n"
