"""
Standalone MCP server that wraps the FastAPI backend service functions.

Run (from the ``fastapi_backend/`` directory)::

    python -m mcp_server.server

Or via uvicorn directly::

    uvicorn mcp_server.server:app --host 0.0.0.0 --port 8001

Requires the same environment variables / ``.env`` file as the FastAPI app.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from app.config import get_settings
from app.db import connect_to_mongo, disconnect_from_mongo, get_database
from app.models import TaskStatus
from app.services.chat import send_message as _send_message
from app.services.chat import stream_message as _stream_message
from app.services.chat_sessions import (
    create_session as _create_session,
)
from app.services.chat_sessions import (
    get_messages_by_session,
    get_sessions_by_user,
)
from app.services.minio_service import ensure_bucket
from app.services.ollama_client import close_httpx_client
from app.services.tasks import (
    build_notebook_task_summary,
    get_task_or_throw,
)
from app.services.tasks import (
    create_task as _create_background_task,
)
from fastapi import HTTPException, UploadFile
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

_TERMINAL_STATUSES = {
    TaskStatus.SUCCEEDED.value,
    TaskStatus.FAILED.value,
    TaskStatus.CANCELED.value,
}

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Auth placeholder  —  extension point for future authentication
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class AuthContext:
    """Placeholder authentication context.

    TODO: Populate with real *user_id* / *role* / token claims once
    authentication is added (OAuth2, API key, mTLS, etc.).
    """

    user_id: str = "anonymous"
    is_authenticated: bool = False
    metadata: dict = field(default_factory=dict)


async def authenticate() -> AuthContext:
    """Extract authentication context from the incoming request.

    Currently a no-op returning an anonymous context.

    Extension point:
    Uncomment the import below and use the Starlette ``Request`` object
    (via ``fastmcp.server.dependencies.get_http_request`` or similar) to
    inspect headers / cookies / JWT / API key and return a populated
    ``AuthContext``.

    .. code::

        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        api_key = request.headers.get("x-api-key", "")
        # ... validate and return AuthContext(...)
    """
    return AuthContext()


# ══════════════════════════════════════════════════════════════════════════════
# Origin validation  —  prevent DNS rebinding even on internal networks
# ══════════════════════════════════════════════════════════════════════════════

_ORIGIN_ALLOW_LIST = [
    o.strip()
    for o in os.environ.get(
        "MCP_ALLOWED_ORIGINS",
        "http://localhost:*,http://127.0.0.1:*",
    ).split(",")
    if o.strip()
]


def _origin_allowed(origin: str) -> bool:
    for pattern in _ORIGIN_ALLOW_LIST:
        if pattern == "*":
            return True
        # Match "scheme://host:*" → any port
        if pattern.endswith(":*"):
            prefix = pattern[:-2]
            if origin.startswith(prefix) and (
                len(origin) == len(prefix) or origin[len(prefix)] == ":"
            ):
                return True
        # Match "*.example.com" → any subdomain
        if pattern.startswith("*.") and origin.endswith(pattern[1:]):
            return True
        if origin == pattern:
            return True
    return False


class OriginCheckMiddleware:
    """Rejects HTTP requests with an ``Origin`` header not on the allow list.

    Applied as raw ASGI middleware so it works correctly with the SSE-based
    Streamable HTTP transport.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode()
            if origin and not _origin_allowed(origin):
                logger.warning("blocked request from disallowed origin: %s", origin)
                from starlette.responses import PlainTextResponse

                response = PlainTextResponse("origin not allowed", 403)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


# ══════════════════════════════════════════════════════════════════════════════
# Lifespan
# ══════════════════════════════════════════════════════════════════════════════


@asynccontextmanager
async def mcp_lifespan(app):
    """Connect Mongo + ensure MinIO bucket on startup; clean up on shutdown.

    Runs exactly once per process, just like ``app/main.py``'s lifespan.
    """
    settings = get_settings()
    await connect_to_mongo()
    await ensure_bucket(settings)
    logger.info("MCP lifespan started — Mongo + MinIO ready")
    try:
        yield {}
    finally:
        await disconnect_from_mongo()
        await close_httpx_client()
        logger.info("MCP lifespan shut down")


# ══════════════════════════════════════════════════════════════════════════════
# FastMCP instance
# ══════════════════════════════════════════════════════════════════════════════

mcp = FastMCP(
    "chatgpt-mcp",
    lifespan=mcp_lifespan,
)


# ══════════════════════════════════════════════════════════════════════════════
# Error helper
# ══════════════════════════════════════════════════════════════════════════════


def _to_tool_error(exc: Exception) -> ToolError:
    """Wrap a service-layer exception into an LLM-friendly ``ToolError``.

    Strips stack traces and translates HTTP semantics into plain messages.
    """
    if isinstance(exc, HTTPException):
        return ToolError(f"[{exc.status_code}] {exc.detail}")
    return ToolError(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# Resources
# ══════════════════════════════════════════════════════════════════════════════


@mcp.resource(
    "users://{user_id}/sessions",
    description="Returns a list of chat session objects for a given user.",
    mime_type="application/json",
)
async def list_sessions(user_id: str) -> str:
    """取得指定使用者的所有聊天 session 列表。

    Each session includes ``id``, ``userId``, ``title``, and ``createdAt``.
    Sorted by ``createdAt`` descending (newest first).
    """
    _ = await authenticate()
    if not user_id.strip():
        raise ToolError("user_id 不能為空白")
    try:
        database = get_database()
        sessions = await get_sessions_by_user(database, user_id)
        return json.dumps(
            [s.model_dump(mode="json") for s in sessions],
            ensure_ascii=False,
        )
    except Exception as exc:
        raise _to_tool_error(exc)


# ══════════════════════════════════════════════════════════════════════════════
# Tools
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool(
    description=(
        "⚠️ Side effect: creates a new object in the database. "
        "建立新的聊天 session。回傳 JSON 包含 id / userId / title / createdAt。"
    ),
)
async def create_session(user_id: str, title: str) -> str:
    """建立新的聊天 session。

    Args:
        user_id: 使用者識別碼（例如 "u1" 或完整 email）。
        title:   此聊天 session 的標題或主題名稱。

    Returns:
        JSON string with id, userId, title, createdAt.
    """
    _ = await authenticate()
    if not user_id.strip() or not title.strip():
        raise ToolError("user_id 和 title 不能為空白")
    try:
        database = get_database()
        session = await _create_session(database, user_id, title)
        return json.dumps(session.model_dump(mode="json"), ensure_ascii=False)
    except Exception as exc:
        raise _to_tool_error(exc)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: consume SSE stream from stream_message and return the final event
# ──────────────────────────────────────────────────────────────────────────────


async def _consume_sse_stream(
    sse_generator: AsyncIterator[str],
) -> dict[str, Any]:
    """Iterate through the SSE generator from ``stream_message``.

    Returns the parsed ``SendMessageResponse``-like dict from the ``done``
    event, or raises ``ToolError`` on an ``error`` event.
    """
    final: dict[str, Any] | None = None
    async for chunk in sse_generator:
        # Each chunk is one complete SSE event: ``event: <type>\ndata: <json>\n\n``
        lines = chunk.strip().splitlines()
        evt = ""
        data_lines: list[str] = []
        for line in lines:
            if line.startswith("event: "):
                evt = line[7:]
            elif line.startswith("data: "):
                data_lines.append(line[6:])
        data_str = "\n".join(data_lines)
        if evt == "done":
            final = json.loads(data_str)
        elif evt == "error":
            err_detail = json.loads(data_str).get("detail", str(data_str))
            raise ToolError(f"stream error: {err_detail}")
    if final is None:
        raise ToolError("stream ended without a 'done' event")
    return final


# ══════════════════════════════════════════════════════════════════════════════
# Resources
# ══════════════════════════════════════════════════════════════════════════════


@mcp.resource(
    "sessions://{session_id}/messages",
    description="Returns all chat messages for a given session.",
    mime_type="application/json",
)
async def list_messages(session_id: str) -> str:
    """取得指定 session 的完整聊天歷史訊息。

    Each message includes ``id``, ``sessionId``, ``role`` (user/assistant),
    ``content``, ``attachmentUrls``, and ``createdAt``.
    Sorted by ``createdAt`` ascending (oldest first).
    """
    _ = await authenticate()
    if not session_id.strip():
        raise ToolError("session_id 不能為空白")
    try:
        database = get_database()
        messages = await get_messages_by_session(database, session_id)
        return json.dumps(
            [m.model_dump(mode="json") for m in messages],
            ensure_ascii=False,
        )
    except Exception as exc:
        raise _to_tool_error(exc)


# ══════════════════════════════════════════════════════════════════════════════
# Tools
# ══════════════════════════════════════════════════════════════════════════════


def _build_attachment(
    attachment_base64: str | None,
    attachment_filename: str | None,
) -> UploadFile | None:
    """Decode base64 attachment into a FastAPI ``UploadFile``.

    Returns ``None`` if both fields are ``None``.  Raises ``ToolError`` for
    malformed input or oversized payload.
    """
    if attachment_base64 is None and attachment_filename is None:
        return None
    if attachment_base64 is None or attachment_filename is None:
        raise ToolError(
            "attachment_base64 和 attachment_filename 必須同時提供或同時省略"
        )

    try:
        file_bytes = base64.b64decode(attachment_base64)
    except (ValueError, base64.binascii.Error) as exc:
        raise ToolError(f"attachment_base64 解碼失敗: {exc}") from exc

    MAX_SIZE = 10 * 1024 * 1024  # 10 MiB
    if len(file_bytes) > MAX_SIZE:
        raise ToolError(f"附件大小超過 {MAX_SIZE // 1024 // 1024} MiB 限制")

    return UploadFile(
        filename=attachment_filename,
        file=BytesIO(file_bytes),
    )


@mcp.tool(
    description=(
        "⚠️ Side effect: saves messages to database and calls Ollama LLM. "
        "送出訊息並等待回覆（非串流）。會自動儲存 user 與 assistant 訊息到資料庫。 "
        "可選附件（base64 + filename）。回傳 SendMessageResponse JSON。"
    ),
)
async def send_message(
    session_id: str,
    content: str,
    attachment_base64: str | None = None,
    attachment_filename: str | None = None,
) -> str:
    """Send a message in a chat session and wait for the full LLM reply.

    This is the **non-streaming** variant.  The tool blocks until Ollama
    finishes, then returns the complete response.

    Args:
        session_id: 目標聊天 session 的 id。
        content:    使用者發送的訊息文字。
        attachment_base64:  (optional) 附件檔案 base64 編碼字串。
        attachment_filename: (optional) 附件檔案名稱（含副檔名）。

    Returns:
        JSON string with sessionId, userMessageId, assistantMessageId,
        assistantContent, attachmentUrls.
    """
    _ = await authenticate()
    if not session_id.strip() or not content.strip():
        raise ToolError("session_id 和 content 不能為空白")
    attachment = _build_attachment(attachment_base64, attachment_filename)
    try:
        database = get_database()
        settings = get_settings()
        response = await _send_message(
            database, settings, session_id, content, attachment
        )
        return json.dumps(response.model_dump(mode="json"), ensure_ascii=False)
    except HTTPException as exc:
        raise _to_tool_error(exc)
    except ToolError:
        raise
    except Exception as exc:
        raise _to_tool_error(exc)


@mcp.tool(
    description=(
        "⚠️ Side effect: saves messages to database and calls Ollama LLM. "
        "送出訊息並等待串流回覆結束。內部會消費 SSE 串流，最後回傳完整回覆。 "
        "可選附件（base64 + filename）。同 send_message 但背後使用 Ollama streaming API。"
    ),
)
async def send_message_streaming(
    session_id: str,
    content: str,
    attachment_base64: str | None = None,
    attachment_filename: str | None = None,
) -> str:
    """Send a message using the Ollama **streaming** API.

    The tool internally consumes the entire SSE stream and returns the
    assembled final response.  From the caller's perspective it behaves
    identically to ``send_message`` but uses the backend's streaming path,
    which may yield lower latency for long replies.

    Args:
        session_id: 目標聊天 session 的 id。
        content:    使用者發送的訊息文字。
        attachment_base64:  (optional) 附件檔案 base64 編碼字串。
        attachment_filename: (optional) 附件檔案名稱（含副檔名）。

    Returns:
        JSON string with sessionId, userMessageId, assistantMessageId,
        assistantContent, attachmentUrls.
    """
    _ = await authenticate()
    if not session_id.strip() or not content.strip():
        raise ToolError("session_id 和 content 不能為空白")
    attachment = _build_attachment(attachment_base64, attachment_filename)
    try:
        database = get_database()
        settings = get_settings()
        sse_gen = _stream_message(database, settings, session_id, content, attachment)
        result = await _consume_sse_stream(sse_gen)
        return json.dumps(result, ensure_ascii=False)
    except HTTPException as exc:
        raise _to_tool_error(exc)
    except ToolError:
        raise
    except Exception as exc:
        raise _to_tool_error(exc)


@mcp.tool(
    description=(
        "⚠️ Side effect: creates a record in the background_tasks collection. "
        "建立一個非同步背景任務並回傳 TaskRecord。payload 接受 JSON 字串，"
        '例如 {"sessionId": "...", "sourceText": "..."}。'
    ),
)
async def create_background_task(
    user_id: str,
    notebook_id: str,
    task_type: str,
    payload: str = "{}",
) -> str:
    """Submit an asynchronous background task.

    The task is queued in MongoDB with status ``queued`` and progress ``0``.
    Use ``get_task_status()`` to poll for completion.

    Args:
        user_id:    使用者識別碼。
        notebook_id: 筆記本／任務群組識別碼（所有同 notebook 的任務可一起追蹤）。
        task_type:  任務類型（例如 ``"summary"``, ``"translate"``）。
        payload:    JSON 字串，任務參數。預設 ``{}``。

    Returns:
        JSON string with the full TaskRecord.
    """
    _ = await authenticate()
    if not user_id.strip() or not notebook_id.strip() or not task_type.strip():
        raise ToolError("user_id, notebook_id, task_type 不能為空白")
    try:
        payload_dict: dict[str, Any] = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ToolError(f"payload 不是合法的 JSON: {exc}") from exc

    try:
        database = get_database()
        task = await _create_background_task(
            database, user_id, notebook_id, task_type, payload_dict
        )
        return json.dumps(task.model_dump(mode="json"), ensure_ascii=False)
    except HTTPException as exc:
        raise _to_tool_error(exc)
    except Exception as exc:
        raise _to_tool_error(exc)


@mcp.tool(
    description=(
        "查詢單一背景任務的狀態。設定 wait_for_completion=True 會輪詢直到任務結束"
        "（succeeded / failed / canceled）再回傳，適合不想自己寫輪詢邏輯的情境。"
    ),
)
async def get_task_status(
    task_id: str,
    wait_for_completion: bool = False,
    timeout_seconds: float = 60.0,
    poll_interval: float = 1.0,
) -> str:
    """Get the current status of a background task.

    By default (``wait_for_completion=False``) returns the current snapshot
    immediately.  Pass ``wait_for_completion=True`` to poll MongoDB until
    the task reaches a terminal state or the timeout fires.

    Args:
        task_id:            背景任務的 MongoDB ObjectId 字串。
        wait_for_completion: 是否輪詢至任務結束。預設 ``False``。
        timeout_seconds:     輪詢超時秒數。預設 60。
        poll_interval:       每次查詢間隔秒數。預設 1.0。

    Returns:
        JSON string with the full TaskRecord.
    """
    _ = await authenticate()
    if not task_id.strip():
        raise ToolError("task_id 不能為空白")
    try:
        database = get_database()
        deadline = asyncio.get_running_loop().time() + timeout_seconds

        while True:
            task = await get_task_or_throw(database, task_id)
            if not wait_for_completion or task.status in _TERMINAL_STATUSES:
                return json.dumps(task.model_dump(mode="json"), ensure_ascii=False)
            if asyncio.get_running_loop().time() >= deadline:
                raise ToolError(
                    f"task {task_id} 在 {timeout_seconds}s 內未完成（當前狀態: {task.status}）"
                )
            await asyncio.sleep(poll_interval)
    except HTTPException as exc:
        raise _to_tool_error(exc)
    except ToolError:
        raise
    except Exception as exc:
        raise _to_tool_error(exc)


@mcp.tool(
    description=(
        "查詢整個 notebook（任務群組）的進度摘要。設定 wait_for_completion=True"
        "會輪詢直到所有任務都結束再回傳。"
    ),
)
async def get_notebook_progress(
    notebook_id: str,
    wait_for_completion: bool = False,
    timeout_seconds: float = 120.0,
    poll_interval: float = 2.0,
) -> str:
    """Get the aggregate progress summary for all tasks in a notebook.

    Returns totalTasks, completedTasks, overallProgress, allCompleted, and
    the full list of individual TaskRecords.

    Args:
        notebook_id:         筆記本識別碼。
        wait_for_completion:  是否輪詢直到所有任務都結束。預設 ``False``。
        timeout_seconds:      輪詢超時秒數。預設 120。
        poll_interval:        每次查詢間隔秒數。預設 2.0。

    Returns:
        JSON string with notebookId, totalTasks, completedTasks,
        overallProgress, allCompleted, tasks.
    """
    _ = await authenticate()
    if not notebook_id.strip():
        raise ToolError("notebook_id 不能為空白")
    try:
        database = get_database()
        deadline = asyncio.get_running_loop().time() + timeout_seconds

        while True:
            summary = await build_notebook_task_summary(database, notebook_id)
            if not wait_for_completion or summary.get("allCompleted", False):
                return json.dumps(summary, ensure_ascii=False)
            if asyncio.get_running_loop().time() >= deadline:
                raise ToolError(
                    f"notebook {notebook_id} 在 {timeout_seconds}s 內未完成"
                    f"（{summary.get('completedTasks', 0)}/{summary.get('totalTasks', 0)}）"
                )
            await asyncio.sleep(poll_interval)
    except HTTPException as exc:
        raise _to_tool_error(exc)
    except ToolError:
        raise
    except Exception as exc:
        raise _to_tool_error(exc)


# ══════════════════════════════════════════════════════════════════════════════
# ASGI app & CLI
# ══════════════════════════════════════════════════════════════════════════════

# Build the ASGI application with middleware.
#
# ``path="/mcp"`` makes the MCP server respond at ``/mcp`` (the Streamable
# HTTP transport path).  This is also the URL clients put in their
# ``claude_desktop_config.json`` ``"url"`` field.
#
app = mcp.http_app(
    path="/mcp",
    middleware=[
        Middleware(OriginCheckMiddleware),
        Middleware(
            CORSMiddleware,
            allow_origins=[o for o in _ORIGIN_ALLOW_LIST if o != "*"],
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=[
                "content-type",
                "authorization",
                "mcp-protocol-version",
                "mcp-session-id",
            ],
            expose_headers=["mcp-session-id"],
        ),
    ],
)


def main() -> None:
    """Run the MCP server via uvicorn.

    Usage::

        python -m mcp_server.server
    """
    import uvicorn

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8001"))
    uvicorn.run(
        "mcp_server.server:app",
        host=host,
        port=port,
        reload=bool(int(os.environ.get("MCP_RELOAD", "0"))),
    )


if __name__ == "__main__":
    main()
