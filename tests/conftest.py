import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.entities import AnalysisProcess
from app.domain.enums import AnalysisStatus


@pytest.fixture
def analysis_id():
    return uuid4()


@pytest.fixture
def mock_analysis(analysis_id):
    now = datetime.now(timezone.utc)
    return AnalysisProcess(
        id=analysis_id,
        filename=f"{analysis_id}.pdf",
        file_type="application/pdf",
        file_url=f"diagrams/{analysis_id}.pdf",
        status=AnalysisStatus.RECEBIDO,
        error_message=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_repo(mock_analysis):
    repo = AsyncMock()
    repo.save = AsyncMock(return_value=mock_analysis)
    repo.get_by_id = AsyncMock(return_value=mock_analysis)
    repo.update_status = AsyncMock(return_value=mock_analysis)
    return repo


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.upload_file = AsyncMock(return_value="diagrams/some-uuid.pdf")
    return storage


@pytest.fixture
def mock_messaging():
    messaging = AsyncMock()
    messaging.publish_analysis = AsyncMock()
    return messaging
