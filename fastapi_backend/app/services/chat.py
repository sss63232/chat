import json
from collections.abc import AsyncIterator

from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import Settings
from app.models import MessageRole, SendMessageResponse, utc_now
from app.services.chat_sessions import get_messages_by_session, get_session_or_throw
from app.services.minio_service import upload_file
from app.services.ollama_client import chat as ollama_chat
from app.services.ollama_client import stream_chat as ollama_stream_chat


async def send_message(
    database: AsyncIOMotorDatabase,
    settings: Settings,
    session_id: str,
    content: str,
    file: UploadFile | None,
) -> SendMessageResponse:
    normalized_content = content.strip()
    await get_session_or_throw(database, session_id)

    attachment_urls = await upload_attachments(settings, file)
    user_message_id = await save_message(
        database=database,
        session_id=session_id,
        role=MessageRole.USER,
        content=normalized_content,
        attachment_urls=attachment_urls,
    )

    history = await build_history(database, session_id)
    assistant_content = await ollama_chat(settings, history)
    assistant_message_id = await save_message(
        database=database,
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=assistant_content,
        attachment_urls=[],
    )

    return SendMessageResponse(
        sessionId=session_id,
        userMessageId=user_message_id,
        assistantMessageId=assistant_message_id,
        assistantContent=assistant_content,
        attachmentUrls=attachment_urls,
    )


async def stream_message(
    database: AsyncIOMotorDatabase,
    settings: Settings,
    session_id: str,
    content: str,
    file: UploadFile | None,
) -> AsyncIterator[str]:
    normalized_content = content.strip()
    await get_session_or_throw(database, session_id)

    attachment_urls = await upload_attachments(settings, file)
    user_message_id = await save_message(
        database=database,
        session_id=session_id,
        role=MessageRole.USER,
        content=normalized_content,
        attachment_urls=attachment_urls,
    )

    try:
        history = await build_history(database, session_id)
        assistant_parts: list[str] = []

        async for delta in ollama_stream_chat(settings, history):
            assistant_parts.append(delta)
            yield format_sse("delta", delta)

        assistant_content = "".join(assistant_parts)
        if not assistant_content:
            raise RuntimeError("Ollama returned an empty response")

        assistant_message_id = await save_message(
            database=database,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            attachment_urls=[],
        )

        done_payload = SendMessageResponse(
            sessionId=session_id,
            userMessageId=user_message_id,
            assistantMessageId=assistant_message_id,
            assistantContent=assistant_content,
            attachmentUrls=attachment_urls,
        )
        yield format_sse("done", done_payload.model_dump_json())
    except Exception as exc:
        yield format_sse("error", json.dumps({"detail": str(exc)}))


async def upload_attachments(settings: Settings, file: UploadFile | None) -> list[str]:
    if file is None or not file.filename:
        return []
    content = await file.read()
    if not content:
        return []
    object_name = await upload_file(settings, file.filename, file.content_type, content)
    return [object_name]


async def save_message(
    database: AsyncIOMotorDatabase,
    session_id: str,
    role: MessageRole,
    content: str,
    attachment_urls: list[str],
) -> str:
    document = {
        "sessionId": session_id,
        "role": role.value,
        "content": content,
        "attachmentUrls": attachment_urls,
        "createdAt": utc_now(),
    }
    result = await database.chat_messages.insert_one(document)
    return str(result.inserted_id)


async def build_history(database: AsyncIOMotorDatabase, session_id: str) -> list[dict[str, str]]:
    messages = await get_messages_by_session(database, session_id)
    history: list[dict[str, str]] = []
    for message in messages:
        combined_content = message.content or ""
        if message.attachmentUrls:
            attachments = "\n".join(f"- {item}" for item in message.attachmentUrls)
            combined_content = f"{combined_content}\n\nAttachments:\n{attachments}".strip()
        role = message.role.value if isinstance(message.role, MessageRole) else str(message.role)
        history.append({"role": role, "content": combined_content})
    return history


def format_sse(event: str, data: str) -> str:
    payload = data.replace("\r\n", "\n").replace("\r", "\n")
    lines = payload.split("\n")
    serialized = "\n".join(f"data: {line}" for line in lines)
    return f"event: {event}\n{serialized}\n\n"
