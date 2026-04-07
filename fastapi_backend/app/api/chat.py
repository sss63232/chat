from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.models import SendMessageResponse
from app.services.chat import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/{session_id}/send", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    content: str = Form(..., min_length=1),
    file: UploadFile | None = File(default=None),
) -> SendMessageResponse:
    if not content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="content must not be blank")
    return await chat_service.send_message(session_id, content, file)


@router.post("/{session_id}/stream")
async def stream_message(
    session_id: str,
    content: str = Form(..., min_length=1),
    file: UploadFile | None = File(default=None),
) -> StreamingResponse:
    if not content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="content must not be blank")
    generator = chat_service.stream_message(session_id, content, file)
    return StreamingResponse(generator, media_type="text/event-stream")
