from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.analysis_repository_port import IAnalysisRepository
from app.domain.entities import AnalysisProcess
from app.domain.enums import AnalysisStatus
from app.infrastructure.database.models import AnalysisProcessModel


class AnalysisRepository(IAnalysisRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, analysis: AnalysisProcess) -> AnalysisProcess:
        model = AnalysisProcessModel(
            id=analysis.id,
            filename=analysis.filename,
            file_type=analysis.file_type,
            file_url=analysis.file_url,
            status=analysis.status.value,
            error_message=analysis.error_message,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, analysis_id: UUID) -> Optional[AnalysisProcess]:
        result = await self._session.execute(
            select(AnalysisProcessModel).where(AnalysisProcessModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_status(
        self,
        analysis_id: UUID,
        status: AnalysisStatus,
        error_message: Optional[str] = None,
    ) -> Optional[AnalysisProcess]:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(AnalysisProcessModel)
            .where(AnalysisProcessModel.id == analysis_id)
            .values(status=status.value, error_message=error_message, updated_at=now)
        )
        await self._session.commit()
        return await self.get_by_id(analysis_id)

    @staticmethod
    def _to_entity(model: AnalysisProcessModel) -> AnalysisProcess:
        return AnalysisProcess(
            id=model.id,
            filename=model.filename,
            file_type=model.file_type,
            file_url=model.file_url,
            status=AnalysisStatus(model.status),
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
