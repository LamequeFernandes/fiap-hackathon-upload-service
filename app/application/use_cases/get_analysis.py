import logging
from uuid import UUID

from app.application.ports.analysis_repository_port import IAnalysisRepository
from app.domain.entities import AnalysisProcess
from app.domain.exceptions import AnalysisNotFoundError

logger = logging.getLogger(__name__)


class GetAnalysisUseCase:
    def __init__(self, repository: IAnalysisRepository) -> None:
        self._repository = repository

    async def execute(self, analysis_id: str) -> AnalysisProcess:
        try:
            uid = UUID(analysis_id)
        except ValueError:
            raise AnalysisNotFoundError(analysis_id)

        analysis = await self._repository.get_by_id(uid)
        if analysis is None:
            raise AnalysisNotFoundError(analysis_id)
        return analysis
