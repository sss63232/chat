from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import Settings, get_settings
from app.db import get_database
from app.models import SendMessageResponse
from app.services.chat import send_message as send_chat_message
from app.services.chat import stream_message as stream_chat_message

router = APIRouter(prefix="/api/chat", tags=["chat"])
DatabaseDep = Annotated[AsyncIOMotorDatabase, Depends(get_database)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/{session_id}/send", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    database: DatabaseDep,
    settings: SettingsDep,
    content: str = Form(..., min_length=1),
    file: UploadFile | None = File(default=None),
) -> SendMessageResponse:
    if not content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="content must not be blank")
    return await send_chat_message(database, settings, session_id, content, file)


@router.post("/{session_id}/stream")
async def stream_message(
    session_id: str,
    database: DatabaseDep,
    settings: SettingsDep,
    content: str = Form(..., min_length=1),
    file: UploadFile | None = File(default=None),
) -> StreamingResponse:
    if not content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="content must not be blank")
    generator = stream_chat_message(database, settings, session_id, content, file)
    return StreamingResponse(generator, media_type="text/event-stream")
