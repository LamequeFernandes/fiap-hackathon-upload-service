from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.enums import AnalysisStatus


class UploadResponse(BaseModel):
    analysis_id: str
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    filename: str
    created_at: datetime
    updated_at: datetime


class UpdateStatusRequest(BaseModel):
    status: AnalysisStatus
    error_message: Optional[str] = None


class AnalysisListResponse(BaseModel):
    items: List[AnalysisStatusResponse]
    total: int


class HealthResponse(BaseModel):
    status: str
    service: str
