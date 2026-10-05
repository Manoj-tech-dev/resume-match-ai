import pytest

from app.core.exceptions import FileTooLargeError, InvalidFileError, PDFProcessingError
from app.services.pdf_extractor import (
    extract_text_from_pdf,
    normalize_text,
    sanitize_filename,
    validate_pdf_upload,
)
from tests.pdf_factory import make_pdf

MB = 1024 * 1024


class TestValidatePdfUpload:
    def test_accepts_valid_pdf(self, resume_pdf: bytes) -> None:
        validate_pdf_upload("resume.pdf", "application/pdf", resume_pdf, MB)

    def test_extension_is_case_insensitive(self, resume_pdf: bytes) -> None:
        validate_pdf_upload("RESUME.PDF", "application/pdf", resume_pdf, MB)

    @pytest.mark.parametrize("filename", ["resume.docx", "resume.txt", "resume", "", None, "resume.pdf.exe"])
    def test_rejects_wrong_extension(self, filename: str | None, resume_pdf: bytes) -> None:
        with pytest.raises(InvalidFileError):
            validate_pdf_upload(filename, "application/pdf", resume_pdf, MB)

    def test_rejects_wrong_content_type(self, resume_pdf: bytes) -> None:
        with pytest.raises(InvalidFileError):
            validate_pdf_upload("resume.pdf", "image/png", resume_pdf, MB)

    def test_rejects_non_pdf_content_with_pdf_extension(self) -> None:
        with pytest.raises(InvalidFileError, match="not a valid PDF"):
            validate_pdf_upload("resume.pdf", "application/pdf", b"PK\x03\x04 this is a zip" * 10, MB)

    def test_rejects_empty_file(self) -> None:
        with pytest.raises(PDFProcessingError, match="empty"):
            validate_pdf_upload("resume.pdf", "application/pdf", b"", MB)

    def test_rejects_oversized_file(self, resume_pdf: bytes) -> None:
        with pytest.raises(FileTooLargeError):
            validate_pdf_upload("resume.pdf", "application/pdf", resume_pdf, max_bytes=100)


class TestExtractText:
    def test_extracts_text(self, resume_pdf: bytes) -> None:
        result = extract_text_from_pdf(resume_pdf)
        assert result.page_count == 1
        assert "Jane Doe" in result.text
        assert "FastAPI" in result.text

    def test_multi_page(self) -> None:
        pdf = make_pdf(["Experienced engineer building distributed systems in Python and Go."], pages=3)
        result = extract_text_from_pdf(pdf)
        assert result.page_count == 3
        assert result.text.count("Experienced engineer") == 3

    def test_too_many_pages(self) -> None:
        pdf = make_pdf(["Some reasonably long line of text for page content."], pages=3)
        with pytest.raises(PDFProcessingError, match="limited to 2 pages"):
            extract_text_from_pdf(pdf, max_pages=2)

    def test_corrupted_pdf(self) -> None:
        with pytest.raises(PDFProcessingError, match="corrupted"):
            extract_text_from_pdf(b"%PDF-1.4\n\x00\x01garbage-bytes-not-a-real-pdf" * 5)

    def test_truncated_pdf(self, resume_pdf: bytes) -> None:
        with pytest.raises(PDFProcessingError):
            extract_text_from_pdf(resume_pdf[: len(resume_pdf) // 3])

    def test_pdf_without_text(self) -> None:
        with pytest.raises(PDFProcessingError, match="extract enough text"):
            extract_text_from_pdf(make_pdf([]))


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  a \t b\n\n\n\nc \x00 ") == "a b\n\nc"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../etc/passwd.pdf", "passwd.pdf"),
        ("C:\\Users\\me\\cv.pdf", "cv.pdf"),
        ("my\x00resume\n.pdf", "myresume.pdf"),
        (None, "resume.pdf"),
        ("", "resume.pdf"),
    ],
)
def test_sanitize_filename(raw: str | None, expected: str) -> None:
    assert sanitize_filename(raw) == expected
