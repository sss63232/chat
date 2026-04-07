from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.sessions import router as sessions_router
from app.config import get_settings
from app.db import connect_to_mongo, disconnect_from_mongo
from app.services.minio_service import minio_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    await minio_service.ensure_bucket()
    try:
        yield
    finally:
        await disconnect_from_mongo()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(sessions_router)
app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

