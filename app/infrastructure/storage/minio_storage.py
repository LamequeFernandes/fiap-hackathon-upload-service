import asyncio
import io
import logging
from functools import partial

from minio import Minio
from minio.error import S3Error

from app.application.ports.storage_port import IStoragePort
from app.core.config import settings
from app.domain.exceptions import StorageError

logger = logging.getLogger(__name__)


class MinIOStorage(IStoragePort):
    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
            logger.info(
                "MinIO bucket created",
                extra={"event": "bucket_created", "bucket": self._bucket},
            )

    async def upload_file(
        self, file_content: bytes, object_name: str, content_type: str
    ) -> str:
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                partial(self._upload_sync, file_content, object_name, content_type),
            )
        except S3Error as exc:
            raise StorageError(f"MinIO upload failed: {exc}") from exc
        return f"{self._bucket}/{object_name}"

    def _upload_sync(
        self, file_content: bytes, object_name: str, content_type: str
    ) -> None:
        self._client.put_object(
            self._bucket,
            object_name,
            io.BytesIO(file_content),
            length=len(file_content),
            content_type=content_type,
        )
