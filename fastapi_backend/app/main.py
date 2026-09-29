from contextlib import asynccontextmanager

import hmac

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.examples import router as examples_router
from app.api.sessions import router as sessions_router
from app.api.tasks import router as tasks_router
from app.config import get_settings
from app.db import connect_to_mongo, disconnect_from_mongo
from app.services.llm_client import close_httpx_client
from app.services.minio_service import ensure_bucket


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    await connect_to_mongo()
    await ensure_bucket(settings)
    try:
        yield
    finally:
        await disconnect_from_mongo()
        await close_httpx_client()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_internal_token(request: Request, call_next):
    expected = settings.internal_api_token
    if expected and request.url.path != "/health" and request.method != "OPTIONS":
        provided = request.headers.get("x-internal-token", "")
        if not hmac.compare_digest(provided, expected):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(tasks_router)
app.include_router(examples_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
