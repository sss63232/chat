from typing import Annotated

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.models import ChatMessage, ChatSession, CreateSessionRequest
from app.services.chat_sessions import create_session, get_messages_by_session, get_sessions_by_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
DatabaseDep = Annotated[AsyncIOMotorDatabase, Depends(get_database)]


@router.post("", response_model=ChatSession)
async def create_session_route(request: CreateSessionRequest, database: DatabaseDep) -> ChatSession:
    return await create_session(database, request.userId, request.title)


@router.get("", response_model=list[ChatSession])
async def get_sessions(userId: str, database: DatabaseDep) -> list[ChatSession]:
    return await get_sessions_by_user(database, userId)


@router.get("/{session_id}/messages", response_model=list[ChatMessage])
async def get_messages(session_id: str, database: DatabaseDep) -> list[ChatMessage]:
    return await get_messages_by_session(database, session_id)
