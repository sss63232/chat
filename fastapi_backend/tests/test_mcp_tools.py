"""Integration tests for the MCP server tools.

Requires MongoDB + Ollama running locally (``docker compose up -d``,
``ollama pull gemma3:4b``).  Tests that need external services are gated
with ``@services_available``; the rest exercise validation logic directly
by calling the tool function or inspecting the registry.
"""

from __future__ import annotations

import json

import pytest
from mcp_server.server import mcp

from .conftest import mongodb_available, services_available

# ══════════════════════════════════════════════════════════════════════════════
# Connection / baseline
# ══════════════════════════════════════════════════════════════════════════════


class TestServerStartup:
    """Verify the FastMCP instance has the expected tools and resources."""

    def test_tools_registered(self):
        names = list(mcp._tool_manager._tools.keys())
        expected = {
            "create_session",
            "send_message",
            "send_message_streaming",
            "create_background_task",
            "get_task_status",
            "get_notebook_progress",
        }
        missing = expected - set(names)
        extra = set(names) - expected
        errs = []
        if missing:
            errs.append(f"missing tools: {missing}")
        if extra:
            errs.append(f"unexpected tools: {extra}")
        assert not errs, "; ".join(errs)

    async def test_resources_registered(self):
        templates = await mcp._resource_manager.get_resource_templates()
        expected = {
            "users://{user_id}/sessions",
            "sessions://{session_id}/messages",
        }
        missing = expected - set(templates.keys())
        assert not missing, f"missing resource templates: {missing}"

    async def test_fixed_resources_registered(self):
        """Verify fixed (non-templated) resources are registered."""
        resources = await mcp._resource_manager.get_resources()
        assert "users://list" in resources, (
            f"users://list not in fixed resources: {set(resources.keys())}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Tool: create_session
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateSession:
    @mongodb_available
    async def test_normal(self):
        data = await _call_tool(
            "create_session", {"user_id": "test-user", "title": "MCP test session"}
        )
        assert data["userId"] == "test-user"
        assert data["title"] == "MCP test session"
        assert "id" in data

    async def test_empty_user_id_returns_error(self):
        with pytest.raises(Exception, match="不能為空白"):
            await _call_tool("create_session", {"user_id": "", "title": "x"})

    async def test_empty_title_returns_error(self):
        with pytest.raises(Exception, match="不能為空白"):
            await _call_tool("create_session", {"user_id": "u1", "title": "  "})


# ══════════════════════════════════════════════════════════════════════════════
# Tool: send_message (requires session + Ollama)
# ══════════════════════════════════════════════════════════════════════════════


class TestSendMessage:
    @services_available
    async def test_normal(self):
        sess = await _call_tool(
            "create_session", {"user_id": "test-msg", "title": "msg-test"}
        )
        data = await _call_tool(
            "send_message",
            {"session_id": sess["id"], "content": "Hello MCP!"},
        )
        assert data["sessionId"] == sess["id"]
        assert data["assistantContent"]

    async def test_empty_content_returns_error(self):
        with pytest.raises(Exception, match="不能為空白"):
            await _call_tool("send_message", {"session_id": "x", "content": ""})

    @mongodb_available
    async def test_nonexistent_session_returns_404(self):
        with pytest.raises(Exception, match="404"):
            await _call_tool(
                "send_message",
                {"session_id": "000000000000000000000000", "content": "hello"},
            )


# ══════════════════════════════════════════════════════════════════════════════
# Tool: send_message_streaming
# ══════════════════════════════════════════════════════════════════════════════


class TestSendMessageStreaming:
    @services_available
    async def test_normal(self):
        sess = await _call_tool(
            "create_session", {"user_id": "test-stream", "title": "stream-test"}
        )
        data = await _call_tool(
            "send_message_streaming",
            {"session_id": sess["id"], "content": "Stream test"},
        )
        assert data["sessionId"] == sess["id"]
        assert data["assistantContent"]

    async def test_empty_content_returns_error(self):
        with pytest.raises(Exception, match="不能為空白"):
            await _call_tool(
                "send_message_streaming", {"session_id": "x", "content": ""}
            )


# ══════════════════════════════════════════════════════════════════════════════
# Tool: create_background_task
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateBackgroundTask:
    @mongodb_available
    async def test_normal(self):
        data = await _call_tool(
            "create_background_task",
            {
                "user_id": "test-task",
                "notebook_id": "nb-1",
                "task_type": "summary",
                "payload": json.dumps({"sessionId": "test", "sourceText": "hello"}),
            },
        )
        assert data["userId"] == "test-task"
        assert data["notebookId"] == "nb-1"
        assert data["status"] == "queued"

    async def test_empty_user_id_returns_error(self):
        with pytest.raises(Exception, match="不能為空白"):
            await _call_tool(
                "create_background_task",
                {"user_id": "", "notebook_id": "nb", "task_type": "t", "payload": "{}"},
            )

    async def test_invalid_payload_returns_error(self):
        with pytest.raises(Exception, match="不是合法的 JSON"):
            await _call_tool(
                "create_background_task",
                {
                    "user_id": "u1",
                    "notebook_id": "nb",
                    "task_type": "t",
                    "payload": "not-json",
                },
            )


# ══════════════════════════════════════════════════════════════════════════════
# Tool: get_task_status
# ══════════════════════════════════════════════════════════════════════════════


class TestGetTaskStatus:
    @mongodb_available
    async def test_invalid_object_id_returns_error(self):
        with pytest.raises(Exception, match="Invalid task id"):
            await _call_tool("get_task_status", {"task_id": "not-an-object-id"})

    async def test_empty_task_id_returns_error(self):
        with pytest.raises(Exception, match="不能為空白"):
            await _call_tool("get_task_status", {"task_id": ""})


# ══════════════════════════════════════════════════════════════════════════════
# Tool: get_notebook_progress
# ══════════════════════════════════════════════════════════════════════════════


class TestGetNotebookProgress:
    async def test_empty_notebook_id_returns_error(self):
        with pytest.raises(Exception, match="不能為空白"):
            await _call_tool("get_notebook_progress", {"notebook_id": ""})

    @mongodb_available
    async def test_nonexistent_notebook_returns_empty(self):
        data = await _call_tool(
            "get_notebook_progress",
            {"notebook_id": "nonexistent-nb"},
        )
        assert data["notebookId"] == "nonexistent-nb"
        assert data["totalTasks"] == 0
        assert data["tasks"] == []


# ══════════════════════════════════════════════════════════════════════════════
# Resource: users://list
# ══════════════════════════════════════════════════════════════════════════════


class TestListAllUsersResource:
    @mongodb_available
    async def test_returns_created_user(self):
        """Creating a session for a user makes that userId appear in users://list."""
        user_id = "test-users-list"
        await _call_tool("create_session", {"user_id": user_id, "title": "users-list test"})
        text = await _read_resource("users://list")
        user_ids = json.loads(text)
        assert user_id in user_ids, f"{user_id!r} not found in {user_ids}"


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


async def _call_tool(tool_name: str, arguments: dict) -> dict | str:
    """Call a tool by going through the server's tool manager."""
    result = await mcp._tool_manager.call_tool(tool_name, arguments)

    # ``result.content`` is a list of ``TextContent`` (or ``ImageContent``, …)
    texts = []
    for part in result.content:
        if hasattr(part, "text"):
            texts.append(part.text)
    body = "".join(texts)

    # Most tools return JSON, so parse it.
    if body:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            pass
    return body


async def _read_resource(uri: str) -> str:
    """Read a fixed (non-templated) resource and return its text content."""
    return await mcp._resource_manager.read_resource(uri)
