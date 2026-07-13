from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models import (
    ChatMessage,
    ChatSession,
    message_from_document,
    session_from_document,
    utc_now,
)


async def create_session(database: AsyncIOMotorDatabase, user_id: str, title: str) -> ChatSession:
    document = {
        "userId": user_id,
        "title": title,
        "createdAt": utc_now(),
    }
    result = await database.chat_sessions.insert_one(document)
    document["_id"] = result.inserted_id
    return session_from_document(document)


async def get_sessions_by_user(database: AsyncIOMotorDatabase, user_id: str) -> list[ChatSession]:
    documents = await database.chat_sessions.find({"userId": user_id}).sort("createdAt", -1).to_list(length=None)
    return [session_from_document(document) for document in documents]


async def get_messages_by_session(database: AsyncIOMotorDatabase, session_id: str) -> list[ChatMessage]:
    documents = await database.chat_messages.find({"sessionId": session_id}).sort("createdAt", 1).to_list(length=None)
    return [message_from_document(document) for document in documents]


async def get_session_or_throw(database: AsyncIOMotorDatabase, session_id: str) -> ChatSession:
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session not found: {session_id}")

    document = await database.chat_sessions.find_one({"_id": ObjectId(session_id)})
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session not found: {session_id}")
    return session_from_document(document)


async def get_all_users(database: AsyncIOMotorDatabase) -> list[str]:
    """Return all distinct userId values from chat_sessions, sorted ascending."""
    user_ids: list[str] = await database.chat_sessions.distinct("userId")
    return sorted(user_ids)
