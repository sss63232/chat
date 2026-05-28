import asyncio
from functools import lru_cache
from io import BytesIO
from urllib.parse import urlparse
from uuid import uuid4

from minio import Minio

from app.config import Settings


@lru_cache
def _get_minio_client(
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
) -> Minio:
    parsed = urlparse(minio_endpoint)
    endpoint = parsed.netloc or parsed.path
    secure = parsed.scheme == "https"
    return Minio(
        endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=secure,
    )


async def ensure_bucket(settings: Settings) -> None:
    client = _get_minio_client(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
    )
    bucket = settings.minio_bucket
    await asyncio.to_thread(_ensure_bucket_sync, client, bucket)


async def upload_file(
    settings: Settings,
    filename: str | None,
    content_type: str | None,
    content: bytes,
) -> str:
    client = _get_minio_client(
        settings.minio_endpoint,
        settings.minio_access_key,
        settings.minio_secret_key,
    )
    object_name = f"{uuid4()}-{sanitize_filename(filename)}"
    await asyncio.to_thread(
        client.put_object,
        settings.minio_bucket,
        object_name,
        BytesIO(content),
        len(content),
        content_type=content_type or "application/octet-stream",
    )
    return object_name


def _ensure_bucket_sync(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def sanitize_filename(filename: str | None) -> str:
    if not filename or not filename.strip():
        return "file"
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)
