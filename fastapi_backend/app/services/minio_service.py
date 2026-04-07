import asyncio
from io import BytesIO
from urllib.parse import urlparse
from uuid import uuid4

from minio import Minio

from app.config import get_settings


class MinioService:
    def __init__(self) -> None:
        settings = get_settings()
        parsed = urlparse(settings.minio_endpoint)
        endpoint = parsed.netloc or parsed.path
        secure = parsed.scheme == "https"
        self.bucket = settings.minio_bucket
        self.client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
        )

    async def ensure_bucket(self) -> None:
        await asyncio.to_thread(self._ensure_bucket_sync)

    async def upload_file(
        self,
        filename: str | None,
        content_type: str | None,
        content: bytes,
    ) -> str:
        object_name = f"{uuid4()}-{self._sanitize_filename(filename)}"
        await asyncio.to_thread(
            self.client.put_object,
            self.bucket,
            object_name,
            BytesIO(content),
            len(content),
            content_type=content_type or "application/octet-stream",
        )
        return object_name

    def _ensure_bucket_sync(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    @staticmethod
    def _sanitize_filename(filename: str | None) -> str:
        if not filename or not filename.strip():
            return "file"
        return "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)


minio_service = MinioService()

