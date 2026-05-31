from datetime import datetime, timezone
from enum import Enum
from typing import Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class AppModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class ChatSession(AppModel):
    id: str
    userId: str
    title: str
    createdAt: datetime


class ChatMessage(AppModel):
    id: str
    sessionId: str
    role: MessageRole
    content: str
    attachmentUrls: list[str] = Field(default_factory=list)
    createdAt: datetime


class CreateSessionRequest(AppModel):
    userId: str = Field(min_length=1)
    title: str = Field(min_length=1)


class SendMessageResponse(AppModel):
    sessionId: str
    userMessageId: str
    assistantMessageId: str
    assistantContent: str
    attachmentUrls: list[str] = Field(default_factory=list)


class CreateTaskRequest(AppModel):
    userId: str = Field(min_length=1)
    taskType: str = Field(min_length=1, examples=["summary"])
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskRecord(AppModel):
    id: str
    userId: str
    taskType: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    result: Any | None = None
    error: str | None = None
    createdAt: datetime
    updatedAt: datetime


def serialize_id(value: Any) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    return str(value)


def session_from_document(document: dict[str, Any]) -> ChatSession:
    return ChatSession(
        id=serialize_id(document["_id"]),
        userId=document["userId"],
        title=document["title"],
        createdAt=document["createdAt"],
    )


def message_from_document(document: dict[str, Any]) -> ChatMessage:
    return ChatMessage(
        id=serialize_id(document["_id"]),
        sessionId=document["sessionId"],
        role=document["role"],
        content=document.get("content", ""),
        attachmentUrls=document.get("attachmentUrls", []),
        createdAt=document["createdAt"],
    )


def task_from_document(document: dict[str, Any]) -> TaskRecord:
    return TaskRecord(
        id=serialize_id(document["_id"]),
        userId=document["userId"],
        taskType=document["taskType"],
        status=document["status"],
        progress=document.get("progress", 0),
        message=document.get("message"),
        payload=document.get("payload", {}),
        result=document.get("result"),
        error=document.get("error"),
        createdAt=document["createdAt"],
        updatedAt=document["updatedAt"],
    )
