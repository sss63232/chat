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
