"""Test configuration: shared fixtures and service-availability guards."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
async def mcp_lifespan():
    """Connect MongoDB before each test so get_database() is available."""
    from app.db import connect_to_mongo, disconnect_from_mongo

    await connect_to_mongo()
    yield
    await disconnect_from_mongo()


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


def _llm_reachable() -> bool:
    """Return True if the configured LLM responds to a /models request."""
    try:
        import httpx

        from app.config import get_settings

        settings = get_settings()
        if not settings.llm_api_key:
            return False
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        r = httpx.get(f"{settings.llm_base_url}/models", headers=headers, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


mongodb_available = pytest.mark.skipif(
    not _mongodb_reachable(),
    reason="MongoDB is not running locally. Start it with: docker compose up -d",
)

services_available = pytest.mark.skipif(
    not (_mongodb_reachable() and _llm_reachable()),
    reason="MongoDB and/or the configured LLM are not reachable. "
    "Start MongoDB with: docker compose up -d; check LLM_BASE_URL/LLM_API_KEY.",
)


@pytest.fixture
def anyio_backend():
    return "asyncio"
