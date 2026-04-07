from fastapi import APIRouter

from app.models import ChatMessage, ChatSession, CreateSessionRequest
from app.services.chat_sessions import chat_session_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=ChatSession)
async def create_session(request: CreateSessionRequest) -> ChatSession:
    return await chat_session_service.create_session(request.userId, request.title)


@router.get("", response_model=list[ChatSession])
async def get_sessions(userId: str) -> list[ChatSession]:
    return await chat_session_service.get_sessions_by_user(userId)


@router.get("/{session_id}/messages", response_model=list[ChatMessage])
async def get_messages(session_id: str) -> list[ChatMessage]:
    return await chat_session_service.get_messages_by_session(session_id)

