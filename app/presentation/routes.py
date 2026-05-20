import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.create_analysis import CreateAnalysisUseCase
from app.application.use_cases.get_analysis import GetAnalysisUseCase
from app.application.use_cases.list_analyses import ListAnalysesUseCase
from app.application.use_cases.update_status import UpdateStatusUseCase
from app.domain.exceptions import (
    AnalysisNotFoundError,
    FileTooLargeError,
    InvalidFileTypeError,
)
from app.infrastructure.database.repositories import AnalysisRepository
from app.infrastructure.database.session import get_session
from app.infrastructure.messaging.rabbitmq_publisher import RabbitMQPublisher
from app.infrastructure.storage.minio_storage import MinIOStorage
from app.presentation.schemas import (
    AnalysisListResponse,
    AnalysisStatusResponse,
    HealthResponse,
    UpdateStatusRequest,
    UploadResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="healthy", service="upload-service")


@router.get("/uploads", response_model=AnalysisListResponse, tags=["uploads"])
async def list_analyses(
    session: AsyncSession = Depends(get_session),
) -> AnalysisListResponse:
    error_id = str(uuid.uuid4())
    try:
        use_case = ListAnalysesUseCase(AnalysisRepository(session))
        analyses = await use_case.execute()
        items = [
            AnalysisStatusResponse(
                analysis_id=str(a.id),
                status=a.status,
                filename=a.filename,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in analyses
        ]
        return AnalysisListResponse(items=items, total=len(items))
    except Exception:
        logger.exception("Unexpected error listing analyses", extra={"error_id": error_id})
        raise HTTPException(
            status_code=500, detail=f"Internal server error. Reference: {error_id}"
        )


@router.post("/uploads", status_code=202, response_model=UploadResponse, tags=["uploads"])
async def upload_diagram(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> UploadResponse:
    error_id = str(uuid.uuid4())
    try:
        file_content = await file.read()
        use_case = CreateAnalysisUseCase(
            repository=AnalysisRepository(session),
            storage=MinIOStorage(),
            messaging=RabbitMQPublisher(),
        )
        analysis = await use_case.execute(
            file_content,
            file.filename or "unknown",
            file.content_type or "application/octet-stream",
        )
        return UploadResponse(
            analysis_id=str(analysis.id),
            status=analysis.status.value,
            message="Diagrama recebido e enfileirado para análise.",
        )
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except InvalidFileTypeError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Tipo de arquivo não permitido: {exc.type_value}",
        )
    except Exception:
        logger.exception("Unexpected error during upload", extra={"error_id": error_id})
        raise HTTPException(
            status_code=500, detail=f"Internal server error. Reference: {error_id}"
        )


@router.get("/uploads/{analysis_id}", response_model=AnalysisStatusResponse, tags=["uploads"])
async def get_analysis(
    analysis_id: str,
    session: AsyncSession = Depends(get_session),
) -> AnalysisStatusResponse:
    error_id = str(uuid.uuid4())
    try:
        use_case = GetAnalysisUseCase(AnalysisRepository(session))
        analysis = await use_case.execute(analysis_id)
        return AnalysisStatusResponse(
            analysis_id=str(analysis.id),
            status=analysis.status,
            filename=analysis.filename,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )
    except AnalysisNotFoundError:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found.")
    except Exception:
        logger.exception("Unexpected error getting analysis", extra={"error_id": error_id})
        raise HTTPException(
            status_code=500, detail=f"Internal server error. Reference: {error_id}"
        )


@router.patch(
    "/uploads/{analysis_id}/status",
    response_model=AnalysisStatusResponse,
    tags=["uploads"],
)
async def update_status(
    analysis_id: str,
    body: UpdateStatusRequest,
    session: AsyncSession = Depends(get_session),
) -> AnalysisStatusResponse:
    error_id = str(uuid.uuid4())
    try:
        use_case = UpdateStatusUseCase(AnalysisRepository(session))
        analysis = await use_case.execute(analysis_id, body.status, body.error_message)
        return AnalysisStatusResponse(
            analysis_id=str(analysis.id),
            status=analysis.status,
            filename=analysis.filename,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )
    except AnalysisNotFoundError:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found.")
    except Exception:
        logger.exception("Unexpected error updating status", extra={"error_id": error_id})
        raise HTTPException(
            status_code=500, detail=f"Internal server error. Reference: {error_id}"
        )
