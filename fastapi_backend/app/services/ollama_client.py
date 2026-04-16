import json
from collections.abc import AsyncIterator

import httpx

from app.config import Settings


_httpx_client: httpx.AsyncClient | None = None


def _get_httpx_client(settings: Settings) -> httpx.AsyncClient:
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0)
    return _httpx_client


async def close_httpx_client() -> None:
    global _httpx_client
    if _httpx_client is not None:
        await _httpx_client.aclose()
        _httpx_client = None


async def chat(settings: Settings, messages: list[dict[str, str]]) -> str:
    client = _get_httpx_client(settings)
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
    }

    response = await client.post("/api/chat", json=payload)
    response.raise_for_status()

    data = response.json()
    content = data.get("message", {}).get("content")
    if not content:
        raise RuntimeError("Ollama returned an empty response")
    return content


async def stream_chat(settings: Settings, messages: list[dict[str, str]]) -> AsyncIterator[str]:
    client = _get_httpx_client(settings)
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": True,
    }

    async with client.stream("POST", "/api/chat", json=payload) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
            if chunk.get("done") is True:
                break
