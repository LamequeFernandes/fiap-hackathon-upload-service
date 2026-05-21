"""Route-level tests for upload-service.

Each handler has its infrastructure dependencies (repositories, storage, messaging)
stubbed out via `unittest.mock.patch` so that only the presentation layer (HTTP
contract, status codes, response shape) is exercised.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.domain.entities import AnalysisProcess
from app.domain.enums import AnalysisStatus
from app.domain.exceptions import AnalysisNotFoundError, FileTooLargeError, InvalidFileTypeError
from app.infrastructure.database.session import get_session
from app.main import app
from app.presentation.routes import _verify_internal_auth

pytestmark = pytest.mark.asyncio

_ANALYSIS_ID = str(uuid4())
_NOW = datetime.now(timezone.utc)
_INTERNAL_KEY = "dev-internal-api-key-change-in-production"

_MOCK_ANALYSIS = AnalysisProcess(
    id=uuid4(),
    filename="diagram.pdf",
    file_type="application/pdf",
    file_url=f"diagrams/{_ANALYSIS_ID}.pdf",
    status=AnalysisStatus.RECEBIDO,
    error_message=None,
    created_at=_NOW,
    updated_at=_NOW,
)

_FAKE_PDF = b"%PDF-1.4 fake content for testing"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def client():
    """HTTP test client with mocked DB session and bypassed internal auth."""

    async def _override_session():
        yield AsyncMock()

    app.dependency_overrides[get_session] = _override_session
    # Internal auth dependency is not the focus of route tests; bypass it here.
    app.dependency_overrides[_verify_internal_auth] = lambda: None

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def client_with_auth():
    """HTTP client that does NOT bypass internal auth, to test the auth path."""

    async def _override_session():
        yield AsyncMock()

    app.dependency_overrides[get_session] = _override_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "upload-service"


# ---------------------------------------------------------------------------
# POST /uploads
# ---------------------------------------------------------------------------


async def test_upload_success(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.MinIOStorage"),
        patch("app.presentation.routes.RabbitMQPublisher"),
        patch("app.presentation.routes.CreateAnalysisUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(return_value=_MOCK_ANALYSIS)

        response = await client.post(
            "/uploads",
            files={"file": ("diagram.pdf", _FAKE_PDF, "application/pdf")},
        )

    assert response.status_code == 202
    data = response.json()
    assert "analysis_id" in data
    assert data["status"] == AnalysisStatus.RECEBIDO
    assert "message" in data


async def test_upload_file_too_large(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.MinIOStorage"),
        patch("app.presentation.routes.RabbitMQPublisher"),
        patch("app.presentation.routes.CreateAnalysisUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(
            side_effect=FileTooLargeError(100.0, 10)
        )

        response = await client.post(
            "/uploads",
            files={"file": ("diagram.pdf", _FAKE_PDF, "application/pdf")},
        )

    assert response.status_code == 413


async def test_upload_invalid_file_type(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.MinIOStorage"),
        patch("app.presentation.routes.RabbitMQPublisher"),
        patch("app.presentation.routes.CreateAnalysisUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(
            side_effect=InvalidFileTypeError("text/plain")
        )

        response = await client.post(
            "/uploads",
            files={"file": ("diagram.txt", b"not a diagram", "text/plain")},
        )

    assert response.status_code == 422
    assert "não permitido" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /uploads/{analysis_id}
# ---------------------------------------------------------------------------


async def test_get_analysis_success(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.GetAnalysisUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(return_value=_MOCK_ANALYSIS)

        response = await client.get(f"/uploads/{_ANALYSIS_ID}")

    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "status" in data
    assert "filename" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_analysis_not_found(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.GetAnalysisUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(
            side_effect=AnalysisNotFoundError(_ANALYSIS_ID)
        )

        response = await client.get(f"/uploads/{_ANALYSIS_ID}")

    assert response.status_code == 404
    assert _ANALYSIS_ID in response.json()["detail"]


# ---------------------------------------------------------------------------
# PATCH /uploads/{analysis_id}/status
# ---------------------------------------------------------------------------


async def test_update_status_success(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.UpdateStatusUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(return_value=_MOCK_ANALYSIS)

        response = await client.patch(
            f"/uploads/{_ANALYSIS_ID}/status",
            json={"status": "EM_PROCESSAMENTO"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "status" in data


async def test_update_status_not_found(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.UpdateStatusUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(
            side_effect=AnalysisNotFoundError(_ANALYSIS_ID)
        )

        response = await client.patch(
            f"/uploads/{_ANALYSIS_ID}/status",
            json={"status": "ERRO", "error_message": "LLM timeout"},
        )

    assert response.status_code == 404


async def test_update_status_forbidden_without_key(client_with_auth):
    """PATCH endpoint must return 403 when the internal API key is missing."""
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.UpdateStatusUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(return_value=_MOCK_ANALYSIS)

        response = await client_with_auth.patch(
            f"/uploads/{_ANALYSIS_ID}/status",
            json={"status": "EM_PROCESSAMENTO"},
        )

    assert response.status_code == 403


async def test_update_status_accepted_with_correct_key(client_with_auth):
    """PATCH endpoint accepts requests with the correct internal API key."""
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.UpdateStatusUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(return_value=_MOCK_ANALYSIS)

        response = await client_with_auth.patch(
            f"/uploads/{_ANALYSIS_ID}/status",
            json={"status": "EM_PROCESSAMENTO"},
            headers={"X-Internal-API-Key": _INTERNAL_KEY},
        )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /uploads  (list)
# ---------------------------------------------------------------------------


async def test_list_analyses_success(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.ListAnalysesUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(return_value=[_MOCK_ANALYSIS])

        response = await client.get("/uploads")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 1
    assert isinstance(data["items"], list)


async def test_list_analyses_empty(client):
    with (
        patch("app.presentation.routes.AnalysisRepository"),
        patch("app.presentation.routes.ListAnalysesUseCase") as MockUC,
    ):
        MockUC.return_value.execute = AsyncMock(return_value=[])

        response = await client.get("/uploads")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
