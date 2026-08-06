"""Isolated regression tests for ``app.services.llm_client``.

These tests exercise the OpenAI-compatible LLM client using ``httpx.MockTransport``
and do **not** connect to MongoDB or a live LLM provider.  They override the
autouse ``mcp_lifespan`` fixture from ``conftest.py`` with a no-op version.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest

from app.config import Settings
from app.services import llm_client


@pytest.fixture(autouse=True)
async def mcp_lifespan() -> AsyncIterator[None]:
    """Override the conftest autouse fixture so MongoDB is never touched."""
    yield


@asynccontextmanager
async def _patched_client(
    settings: Settings,
    handler: httpx.MockTransport,
) -> AsyncIterator[httpx.AsyncClient]:
    """Install a mocked httpx client for ``llm_client`` and clean up after."""
    client = httpx.AsyncClient(base_url=settings.llm_base_url, transport=handler)
    previous = llm_client._httpx_client
    llm_client._httpx_client = client
    try:
        yield client
    finally:
        llm_client._httpx_client = previous
        await client.aclose()


def _capture_handler(
    captured: list[httpx.Request],
    response: httpx.Response,
) -> httpx.MockTransport:
    """Return a MockTransport that records the request and returns ``response``."""

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return response

    return httpx.MockTransport(handler)


async def test_chat_sends_correct_request_and_returns_content() -> None:
    """Non-streaming call posts the expected payload and parses the reply."""
    settings = Settings(
        llm_base_url="https://example.com/v1",
        llm_model="test-model",
        llm_api_key="test-secret-key",
    )
    messages = [{"role": "user", "content": "Say hello"}]
    llm_response = {"choices": [{"message": {"content": "Hello, tester!"}}]}

    captured: list[httpx.Request] = []
    transport = _capture_handler(captured, httpx.Response(200, json=llm_response))

    async with _patched_client(settings, transport):
        result = await llm_client.chat(settings, messages)

    assert result == "Hello, tester!"
    assert len(captured) == 1
    request = captured[0]
    assert request.method == "POST"
    assert str(request.url) == "https://example.com/v1/chat/completions"
    assert json.loads(request.content) == {
        "model": "test-model",
        "messages": messages,
        "stream": False,
    }
    assert request.headers["Authorization"] == "Bearer test-secret-key"


async def test_chat_omits_authorization_when_key_is_empty() -> None:
    """No Authorization header is sent when the API key is blank."""
    settings = Settings(
        llm_base_url="https://example.com/v1",
        llm_model="test-model",
        llm_api_key="",
    )
    llm_response = {"choices": [{"message": {"content": "ok"}}]}

    captured: list[httpx.Request] = []
    transport = _capture_handler(captured, httpx.Response(200, json=llm_response))

    async with _patched_client(settings, transport):
        await llm_client.chat(settings, [{"role": "user", "content": "Hi"}])

    assert "Authorization" not in captured[0].headers


async def test_chat_raises_http_status_error_on_403() -> None:
    """A non-2xx response is converted into ``httpx.HTTPStatusError``."""
    settings = Settings(
        llm_base_url="https://example.com/v1",
        llm_model="test-model",
        llm_api_key="test-secret-key",
    )

    captured: list[httpx.Request] = []
    transport = _capture_handler(captured, httpx.Response(403, text="Forbidden"))

    async with _patched_client(settings, transport):
        with pytest.raises(httpx.HTTPStatusError):
            await llm_client.chat(settings, [{"role": "user", "content": "Hi"}])


async def test_stream_chat_parses_sse_deltas_and_stops_at_done() -> None:
    """Streaming yields concatenated content deltas and terminates on ``[DONE]``."""
    settings = Settings(
        llm_base_url="https://example.com/v1",
        llm_model="test-model",
        llm_api_key="test-secret-key",
    )
    messages = [{"role": "user", "content": "Count to three"}]

    sse_body = (
        'data: {"choices":[{"delta":{"content":"one"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":" two"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":" three"}}]}\n\n'
        "data: [DONE]\n\n"
    )

    captured: list[httpx.Request] = []
    transport = _capture_handler(
        captured,
        httpx.Response(
            200,
            text=sse_body,
            headers={"content-type": "text/event-stream"},
        ),
    )

    async with _patched_client(settings, transport):
        deltas = [delta async for delta in llm_client.stream_chat(settings, messages)]

    assert deltas == ["one", " two", " three"]
    assert "".join(deltas) == "one two three"

    request = captured[0]
    assert request.method == "POST"
    assert str(request.url) == "https://example.com/v1/chat/completions"
    assert json.loads(request.content) == {
        "model": "test-model",
        "messages": messages,
        "stream": True,
    }
    assert request.headers["Authorization"] == "Bearer test-secret-key"
