import json
from collections.abc import AsyncIterator

import httpx

from app.config import get_settings


class OllamaClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=120.0) as client:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content")
        if not content:
            raise RuntimeError("Ollama returned an empty response")
        return content

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        payload = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": True,
        }

        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=None) as client:
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


ollama_client = OllamaClient()

