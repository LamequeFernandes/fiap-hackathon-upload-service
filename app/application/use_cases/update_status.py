import logging
from typing import Optional
from uuid import UUID

from app.application.ports.analysis_repository_port import IAnalysisRepository
from app.domain.entities import AnalysisProcess
from app.domain.enums import AnalysisStatus
from app.domain.exceptions import AnalysisNotFoundError

logger = logging.getLogger(__name__)


class UpdateStatusUseCase:
    def __init__(self, repository: IAnalysisRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        analysis_id: str,
        status: AnalysisStatus,
        error_message: Optional[str] = None,
    ) -> AnalysisProcess:
        try:
            uid = UUID(analysis_id)
        except ValueError:
            raise AnalysisNotFoundError(analysis_id)

        analysis = await self._repository.update_status(uid, status, error_message)
        if analysis is None:
            raise AnalysisNotFoundError(analysis_id)

        logger.info(
            "Analysis status updated",
            extra={
                "event": "status_updated",
                "analysis_id": analysis_id,
                "status": status.value,
            },
        )
        return analysis
