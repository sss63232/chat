import json
from collections.abc import AsyncIterator

from fastapi import UploadFile

from app.db import get_database
from app.models import MessageRole, SendMessageResponse, utc_now
from app.services.chat_sessions import chat_session_service
from app.services.minio_service import minio_service
from app.services.ollama_client import ollama_client


class ChatService:
    async def send_message(self, session_id: str, content: str, file: UploadFile | None) -> SendMessageResponse:
        content = content.strip()
        await chat_session_service.get_session_or_throw(session_id)

        attachment_urls = await self._upload_attachments(file)
        user_message = await self._save_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            attachment_urls=attachment_urls,
        )

        history = await self._build_history(session_id)
        assistant_content = await ollama_client.chat(history)
        assistant_message = await self._save_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            attachment_urls=[],
        )

        return SendMessageResponse(
            sessionId=session_id,
            userMessageId=user_message["id"],
            assistantMessageId=assistant_message["id"],
            assistantContent=assistant_content,
            attachmentUrls=attachment_urls,
        )

    async def stream_message(
        self,
        session_id: str,
        content: str,
        file: UploadFile | None,
    ) -> AsyncIterator[str]:
        content = content.strip()
        await chat_session_service.get_session_or_throw(session_id)

        attachment_urls = await self._upload_attachments(file)
        user_message = await self._save_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            attachment_urls=attachment_urls,
        )

        try:
            history = await self._build_history(session_id)
            assistant_parts: list[str] = []

            async for delta in ollama_client.stream_chat(history):
                assistant_parts.append(delta)
                yield self._format_sse("delta", delta)

            assistant_content = "".join(assistant_parts)
            if not assistant_content:
                raise RuntimeError("Ollama returned an empty response")

            assistant_message = await self._save_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                attachment_urls=[],
            )

            done_payload = SendMessageResponse(
                sessionId=session_id,
                userMessageId=user_message["id"],
                assistantMessageId=assistant_message["id"],
                assistantContent=assistant_content,
                attachmentUrls=attachment_urls,
            )
            yield self._format_sse("done", done_payload.model_dump_json())
        except Exception as exc:
            yield self._format_sse("error", json.dumps({"detail": str(exc)}))

    async def _upload_attachments(self, file: UploadFile | None) -> list[str]:
        if file is None or not file.filename:
            return []
        content = await file.read()
        if not content:
            return []
        object_name = await minio_service.upload_file(file.filename, file.content_type, content)
        return [object_name]

    async def _save_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        attachment_urls: list[str],
    ) -> dict[str, str]:
        database = get_database()
        document = {
            "sessionId": session_id,
            "role": role.value,
            "content": content,
            "attachmentUrls": attachment_urls,
            "createdAt": utc_now(),
        }
        result = await database.chat_messages.insert_one(document)
        return {"id": str(result.inserted_id)}

    async def _build_history(self, session_id: str) -> list[dict[str, str]]:
        messages = await chat_session_service.get_messages_by_session(session_id)
        history: list[dict[str, str]] = []
        for message in messages:
            combined_content = message.content or ""
            if message.attachmentUrls:
                attachments = "\n".join(f"- {item}" for item in message.attachmentUrls)
                combined_content = f"{combined_content}\n\nAttachments:\n{attachments}".strip()
            role = message.role.value if isinstance(message.role, MessageRole) else str(message.role)
            history.append({"role": role, "content": combined_content})
        return history

    @staticmethod
    def _format_sse(event: str, data: str) -> str:
        payload = data.replace("\r\n", "\n").replace("\r", "\n")
        lines = payload.split("\n")
        serialized = "\n".join(f"data: {line}" for line in lines)
        return f"event: {event}\n{serialized}\n\n"


chat_service = ChatService()
