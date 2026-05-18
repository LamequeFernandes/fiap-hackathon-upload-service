import pytest

from app.application.use_cases.create_analysis import CreateAnalysisUseCase
from app.domain.enums import AnalysisStatus
from app.domain.exceptions import FileTooLargeError, InvalidFileTypeError

pytestmark = pytest.mark.asyncio

# Magic-byte valid file headers
VALID_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n" + b"\x00" * 50
VALID_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde"
    + b"\x00" * 50
)
VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 50


async def test_create_analysis_pdf_success(mock_repo, mock_storage, mock_messaging, mock_analysis):
    mock_repo.save.return_value = mock_analysis
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)

    result = await use_case.execute(VALID_PDF, "diagram.pdf", "application/pdf")

    assert result.status == AnalysisStatus.RECEBIDO
    mock_storage.upload_file.assert_called_once()
    mock_messaging.publish_analysis.assert_called_once()
    mock_repo.save.assert_called_once()


async def test_create_analysis_png_success(mock_repo, mock_storage, mock_messaging, mock_analysis):
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)
    result = await use_case.execute(VALID_PNG, "diagram.png", "image/png")
    assert result.status == AnalysisStatus.RECEBIDO


async def test_create_analysis_jpeg_success(mock_repo, mock_storage, mock_messaging, mock_analysis):
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)
    result = await use_case.execute(VALID_JPEG, "diagram.jpg", "image/jpeg")
    assert result.status == AnalysisStatus.RECEBIDO


async def test_create_analysis_file_too_large(mock_repo, mock_storage, mock_messaging):
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)
    large_content = b"x" * (11 * 1024 * 1024)  # 11 MB

    with pytest.raises(FileTooLargeError) as exc_info:
        await use_case.execute(large_content, "big.pdf", "application/pdf")

    assert exc_info.value.size_mb > 10
    mock_storage.upload_file.assert_not_called()


async def test_create_analysis_invalid_extension(mock_repo, mock_storage, mock_messaging):
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)

    with pytest.raises(InvalidFileTypeError) as exc_info:
        await use_case.execute(b"MZcontent", "malware.exe", "application/octet-stream")

    assert exc_info.value.type_value == ".exe"
    mock_storage.upload_file.assert_not_called()


async def test_create_analysis_no_extension(mock_repo, mock_storage, mock_messaging):
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)

    with pytest.raises(InvalidFileTypeError):
        await use_case.execute(b"content", "no_extension", "application/pdf")


async def test_create_analysis_wrong_magic_bytes(mock_repo, mock_storage, mock_messaging):
    """File has .pdf extension but content is not a real PDF (magic bytes mismatch)."""
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)

    with pytest.raises(InvalidFileTypeError):
        await use_case.execute(b"This is definitely not a PDF", "fake.pdf", "application/pdf")
    mock_storage.upload_file.assert_not_called()


async def test_filename_uses_uuid_not_original(mock_repo, mock_storage, mock_messaging, mock_analysis):
    """Safe filename (UUID) must be used, not the original user-provided name."""
    mock_repo.save.return_value = mock_analysis
    use_case = CreateAnalysisUseCase(mock_repo, mock_storage, mock_messaging)

    await use_case.execute(VALID_PDF, "../../../../etc/passwd.pdf", "application/pdf")

    saved_analysis = mock_repo.save.call_args[0][0]
    assert "passwd" not in saved_analysis.filename
    assert "etc" not in saved_analysis.filename
