from typing import List

from app.application.ports.analysis_repository_port import IAnalysisRepository
from app.domain.entities import AnalysisProcess


class ListAnalysesUseCase:
    def __init__(self, repository: IAnalysisRepository) -> None:
        self._repository = repository

    async def execute(self) -> List[AnalysisProcess]:
        return await self._repository.list_all()
