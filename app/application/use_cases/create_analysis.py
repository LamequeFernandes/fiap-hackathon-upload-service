import logging
import uuid
from datetime import datetime, timezone

import filetype

from app.application.ports.analysis_repository_port import IAnalysisRepository
from app.application.ports.messaging_port import IMessagingPort
from app.application.ports.storage_port import IStoragePort
from app.core.config import settings
from app.domain.entities import AnalysisProcess
from app.domain.enums import AnalysisStatus
from app.domain.exceptions import FileTooLargeError, InvalidFileTypeError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}


class CreateAnalysisUseCase:
    def __init__(
        self,
        repository: IAnalysisRepository,
        storage: IStoragePort,
        messaging: IMessagingPort,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._messaging = messaging

    async def execute(
        self, file_content: bytes, original_filename: str, declared_content_type: str
    ) -> AnalysisProcess:
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(file_content) > max_bytes:
            raise FileTooLargeError(
                len(file_content) / (1024 * 1024), settings.max_file_size_mb
            )

        ext = self._get_extension(original_filename).lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(ext or "unknown")

        # Validate MIME from actual magic bytes — never trust client declaration
        detected = filetype.guess(file_content)
        if detected is None or detected.mime not in ALLOWED_MIME_TYPES:
            mime = detected.mime if detected else "unknown"
            raise InvalidFileTypeError(mime)

        analysis_id = uuid.uuid4()
        # Save with UUID-based name, never the original filename
        object_name = f"{analysis_id}{ext}"

        logger.info(
            "Upload received, starting analysis creation",
            extra={"event": "upload_received", "analysis_id": str(analysis_id)},
        )

        file_url = await self._storage.upload_file(
            file_content, object_name, detected.mime
        )
        logger.info(
            "File saved to MinIO",
            extra={"event": "file_saved", "analysis_id": str(analysis_id)},
        )

        now = datetime.now(timezone.utc)
        analysis = AnalysisProcess(
            id=analysis_id,
            filename=object_name,
            file_type=detected.mime,
            file_url=file_url,
            status=AnalysisStatus.RECEBIDO,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        await self._repository.save(analysis)

        await self._messaging.publish_analysis(analysis_id, file_url)
        logger.info(
            "Message published to RabbitMQ",
            extra={"event": "message_published", "analysis_id": str(analysis_id)},
        )

        return analysis

    @staticmethod
    def _get_extension(filename: str) -> str:
        if "." not in filename:
            return ""
        return "." + filename.rsplit(".", 1)[-1]
