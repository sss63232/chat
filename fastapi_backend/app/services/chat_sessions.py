from bson import ObjectId
from fastapi import HTTPException, status

from app.db import get_database
from app.models import ChatMessage, ChatSession, message_from_document, session_from_document, utc_now


class ChatSessionService:
    async def create_session(self, user_id: str, title: str) -> ChatSession:
        database = get_database()
        document = {
            "userId": user_id,
            "title": title,
            "createdAt": utc_now(),
        }
        result = await database.chat_sessions.insert_one(document)
        document["_id"] = result.inserted_id
        return session_from_document(document)

    async def get_sessions_by_user(self, user_id: str) -> list[ChatSession]:
        database = get_database()
        documents = await database.chat_sessions.find(
            {"userId": user_id}
        ).sort("createdAt", -1).to_list(length=None)
        return [session_from_document(document) for document in documents]

    async def get_messages_by_session(self, session_id: str) -> list[ChatMessage]:
        database = get_database()
        documents = await database.chat_messages.find(
            {"sessionId": session_id}
        ).sort("createdAt", 1).to_list(length=None)
        return [message_from_document(document) for document in documents]

    async def get_session_or_throw(self, session_id: str) -> ChatSession:
        database = get_database()
        if not ObjectId.is_valid(session_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session not found: {session_id}")

        document = await database.chat_sessions.find_one({"_id": ObjectId(session_id)})
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session not found: {session_id}")
        return session_from_document(document)


chat_session_service = ChatSessionService()

