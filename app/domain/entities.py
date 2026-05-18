from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.enums import AnalysisStatus


@dataclass
class AnalysisProcess:
    id: UUID
    filename: str
    file_type: str
    file_url: str
    status: AnalysisStatus
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
