import json
from collections.abc import AsyncIterator

import httpx

from app.config import Settings

_httpx_client: httpx.AsyncClient | None = None


def _get_httpx_client(settings: Settings) -> httpx.AsyncClient:
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.AsyncClient(base_url=settings.llm_base_url, timeout=120.0)
    return _httpx_client


def _auth_headers(settings: Settings) -> dict[str, str]:
    headers: dict[str, str] = {}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"
    return headers


async def close_httpx_client() -> None:
    global _httpx_client
    if _httpx_client is not None:
        await _httpx_client.aclose()
        _httpx_client = None


async def chat(settings: Settings, messages: list[dict[str, str]]) -> str:
    """Send a non-streaming chat completion request and return the reply content."""
    client = _get_httpx_client(settings)
    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "stream": False,
    }

    response = await client.post(
        "/chat/completions",
        json=payload,
        headers=_auth_headers(settings),
    )
    response.raise_for_status()

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("LLM returned an empty response")
    return content


async def stream_chat(
    settings: Settings,
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    """Stream a chat completion request and yield each content delta."""
    client = _get_httpx_client(settings)
    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "stream": True,
    }

    async with client.stream(
        "POST",
        "/chat/completions",
        json=payload,
        headers=_auth_headers(settings),
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line:
                continue
            if not line.startswith("data: "):
                continue
            data = line[len("data: ") :].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if content:
                yield content
