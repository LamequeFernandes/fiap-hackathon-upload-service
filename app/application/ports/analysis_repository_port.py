from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities import AnalysisProcess
from app.domain.enums import AnalysisStatus


class IAnalysisRepository(ABC):
    @abstractmethod
    async def save(self, analysis: AnalysisProcess) -> AnalysisProcess:
        ...

    @abstractmethod
    async def get_by_id(self, analysis_id: UUID) -> Optional[AnalysisProcess]:
        ...

    @abstractmethod
    async def update_status(
        self,
        analysis_id: UUID,
        status: AnalysisStatus,
        error_message: Optional[str] = None,
    ) -> Optional[AnalysisProcess]:
        ...

    @abstractmethod
    async def list_all(self) -> List[AnalysisProcess]:
        ...
