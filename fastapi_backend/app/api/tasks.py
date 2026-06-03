from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi import status as http_status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.models import CreateTaskRequest, TaskRecord
from app.services.tasks import create_task as create_background_task
from app.services.tasks import (
    get_task_or_throw,
    stream_notebook_task_events,
    stream_task_events,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
DatabaseDep = Annotated[AsyncIOMotorDatabase, Depends(get_database)]


@router.post("", response_model=TaskRecord, status_code=202)
async def create_task(request: CreateTaskRequest, database: DatabaseDep) -> TaskRecord:
    return await create_background_task(
        database, request.userId, request.notebookId, request.taskType, request.payload
    )


@router.get("/{task_id}", response_model=TaskRecord)
async def get_task(task_id: str, database: DatabaseDep) -> TaskRecord:
    return await get_task_or_throw(database, task_id)


@router.get("/{task_id}/events")
async def task_events(
    task_id: str,
    request: Request,
    database: DatabaseDep,
    heartbeatInterval: float = Query(default=5.0, ge=5.0, le=120.0),
) -> StreamingResponse:
    await get_task_or_throw(database, task_id)
    generator = stream_task_events(
        database, request, task_id, heartbeat_interval=heartbeatInterval
    )
    return task_streaming_response(generator)


@router.get("/notebooks/{notebook_id}/events")
async def notebook_task_events(
    request: Request,
    database: DatabaseDep,
    notebook_id: str = Path(min_length=1),
    heartbeatInterval: float = Query(default=5.0, ge=5.0, le=120.0),
) -> StreamingResponse:
    exists = await database.background_tasks.find_one(
        {"notebookId": notebook_id}, projection={"_id": 1}
    )
    if exists is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Notebook not found: {notebook_id}",
        )
    generator = stream_notebook_task_events(
        database, request, notebook_id, heartbeat_interval=heartbeatInterval
    )
    return task_streaming_response(generator)


def task_streaming_response(generator) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
