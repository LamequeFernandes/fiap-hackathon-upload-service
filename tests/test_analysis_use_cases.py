import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.application.use_cases.get_analysis import GetAnalysisUseCase
from app.application.use_cases.update_status import UpdateStatusUseCase
from app.domain.enums import AnalysisStatus
from app.domain.exceptions import AnalysisNotFoundError

pytestmark = pytest.mark.asyncio


# GetAnalysisUseCase
async def test_get_analysis_success(mock_repo, mock_analysis):
    use_case = GetAnalysisUseCase(mock_repo)
    result = await use_case.execute(str(mock_analysis.id))
    assert result.id == mock_analysis.id
    mock_repo.get_by_id.assert_called_once_with(mock_analysis.id)


async def test_get_analysis_not_found(mock_repo):
    mock_repo.get_by_id.return_value = None
    use_case = GetAnalysisUseCase(mock_repo)

    with pytest.raises(AnalysisNotFoundError):
        await use_case.execute(str(uuid4()))


async def test_get_analysis_invalid_uuid(mock_repo):
    use_case = GetAnalysisUseCase(mock_repo)

    with pytest.raises(AnalysisNotFoundError):
        await use_case.execute("not-a-valid-uuid")
    mock_repo.get_by_id.assert_not_called()


# UpdateStatusUseCase
async def test_update_status_to_em_processamento(mock_repo, mock_analysis):
    from datetime import datetime, timezone
    from dataclasses import replace

    updated = replace(mock_analysis, status=AnalysisStatus.EM_PROCESSAMENTO)
    mock_repo.update_status.return_value = updated

    use_case = UpdateStatusUseCase(mock_repo)
    result = await use_case.execute(
        str(mock_analysis.id), AnalysisStatus.EM_PROCESSAMENTO
    )
    assert result.status == AnalysisStatus.EM_PROCESSAMENTO


async def test_update_status_to_erro(mock_repo, mock_analysis):
    from dataclasses import replace

    updated = replace(
        mock_analysis,
        status=AnalysisStatus.ERRO,
        error_message="Processing failed",
    )
    mock_repo.update_status.return_value = updated

    use_case = UpdateStatusUseCase(mock_repo)
    result = await use_case.execute(
        str(mock_analysis.id),
        AnalysisStatus.ERRO,
        error_message="Processing failed",
    )
    assert result.status == AnalysisStatus.ERRO
    assert result.error_message == "Processing failed"


async def test_update_status_not_found(mock_repo):
    mock_repo.update_status.return_value = None
    use_case = UpdateStatusUseCase(mock_repo)

    with pytest.raises(AnalysisNotFoundError):
        await use_case.execute(str(uuid4()), AnalysisStatus.ANALISADO)


async def test_update_status_invalid_uuid(mock_repo):
    use_case = UpdateStatusUseCase(mock_repo)

    with pytest.raises(AnalysisNotFoundError):
        await use_case.execute("bad-uuid", AnalysisStatus.ANALISADO)
    mock_repo.update_status.assert_not_called()
