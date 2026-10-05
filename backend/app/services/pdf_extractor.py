"""PDF upload validation and text extraction.

Processing happens fully in memory (bytes -> BytesIO); nothing user-supplied is
ever written to a path we choose, so there is no temp-file cleanup or path
traversal risk. Starlette itself spools large uploads to an anonymous
`SpooledTemporaryFile` that is deleted automatically.
"""

from __future__ import annotations

import io
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePath

from pypdf import PdfReader
from pypdf.errors import PdfReadError, PyPdfError

from app.core.exceptions import FileTooLargeError, InvalidFileError, PDFProcessingError

logger = logging.getLogger("app.pdf")

ALLOWED_CONTENT_TYPES = frozenset(
    {"application/pdf", "application/x-pdf", "application/acrobat", "application/octet-stream", ""}
)
PDF_MAGIC = b"%PDF-"
MIN_TEXT_CHARS = 50
MAX_TEXT_CHARS = 40_000  # Bound prompt size / cost.


@dataclass(frozen=True)
class ExtractedResume:
    text: str
    page_count: int


def sanitize_filename(filename: str | None) -> str:
    """Return a display-safe basename (no directories, control chars, or excessive length)."""
    name = PurePath((filename or "").replace("\\", "/")).name
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C").strip()
    return (name or "resume.pdf")[:255]


def validate_pdf_upload(filename: str | None, content_type: str | None, data: bytes, max_bytes: int) -> None:
    """Validate extension, MIME type, size and magic bytes. Raises on failure."""
    if not filename or not filename.lower().endswith(".pdf"):
        raise InvalidFileError("Only PDF files are supported. Please upload a file ending in .pdf.")
    if (content_type or "").split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        raise InvalidFileError("The uploaded file does not appear to be a PDF.")
    if len(data) == 0:
        raise PDFProcessingError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise FileTooLargeError(f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.")
    # The PDF spec allows the header to appear within the first 1024 bytes.
    if PDF_MAGIC not in data[:1024]:
        raise InvalidFileError("The file content is not a valid PDF (missing PDF header).")


def normalize_text(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(data: bytes, max_pages: int = 20) -> ExtractedResume:
    """Extract normalized text from PDF bytes. Raises `PDFProcessingError` for unusable files."""
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            # Many PDFs are "encrypted" with an empty user password; try that first.
            try:
                if not reader.decrypt(""):
                    raise PDFProcessingError("This PDF is password-protected. Please upload an unlocked copy.")
            except PDFProcessingError:
                raise
            except Exception as exc:
                raise PDFProcessingError("This PDF is password-protected. Please upload an unlocked copy.") from exc

        page_count = len(reader.pages)
        if page_count == 0:
            raise PDFProcessingError("The PDF has no pages.")
        if page_count > max_pages:
            raise PDFProcessingError(f"The PDF has {page_count} pages; resumes are limited to {max_pages} pages.")

        parts: list[str] = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:  # A single bad page shouldn't sink the whole resume.
                logger.warning("Failed to extract text from a PDF page; skipping it")
    except PDFProcessingError:
        raise
    except (PdfReadError, PyPdfError, ValueError, KeyError, TypeError, OSError) as exc:
        logger.info("Unreadable PDF: %s", type(exc).__name__)
        raise PDFProcessingError("The PDF appears to be corrupted or unreadable.") from exc
    except Exception as exc:  # pypdf can raise a wide range of errors on malformed input.
        logger.warning("Unexpected PDF parsing failure: %s", type(exc).__name__)
        raise PDFProcessingError("The PDF appears to be corrupted or unreadable.") from exc

    text = normalize_text("\n".join(parts))
    if len(text) < MIN_TEXT_CHARS:
        raise PDFProcessingError(
            "Could not extract enough text from this PDF. If it is a scanned image, "
            "please upload a text-based PDF."
        )
    return ExtractedResume(text=text[:MAX_TEXT_CHARS], page_count=page_count)
