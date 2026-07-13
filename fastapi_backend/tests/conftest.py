"""Test configuration: shared fixtures and service-availability guards."""

from __future__ import annotations

import pytest


def _mongodb_reachable() -> bool:
    """Return True if MongoDB on the default URI responds to a ping."""
    try:
        from pymongo import MongoClient

        client = MongoClient(
            "mongodb://localhost:27017/?replicaSet=rs0",
            serverSelectionTimeoutMS=2000,
        )
        client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


def _ollama_reachable() -> bool:
    """Return True if Ollama responds to a /api/tags request."""
    try:
        import httpx

        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


mongodb_available = pytest.mark.skipif(
    not _mongodb_reachable(),
    reason="MongoDB is not running locally. Start it with: docker compose up -d",
)

services_available = pytest.mark.skipif(
    not (_mongodb_reachable() and _ollama_reachable()),
    reason="MongoDB and/or Ollama are not running locally. "
    "Start them with: docker compose up -d && ollama pull gemma3:4b",
)


@pytest.fixture
def anyio_backend():
    return "asyncio"
