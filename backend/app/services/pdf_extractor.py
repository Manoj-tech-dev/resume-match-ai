"""Document upload validation and text extraction for PDF, DOCX, PPTX, Images, and TXT.

Processing happens fully in memory (bytes -> BytesIO); nothing user-supplied is
ever written to a path on disk, preventing temporary file leaks and path traversal risks.
"""

from __future__ import annotations

import io
import logging
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePath

from pypdf import PdfReader
from pypdf.errors import PdfReadError, PyPdfError

from app.core.exceptions import FileTooLargeError, InvalidFileError, PDFProcessingError

logger = logging.getLogger("app.extractor")

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
MIN_TEXT_CHARS = 50
MAX_TEXT_CHARS = 40_000

SUPPORTED_EXTENSIONS = frozenset({
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tiff",
    ".txt",
    ".md",
    ".rtf",
})

ALLOWED_MIME_PREFIXES = ("application/", "image/", "text/")


@dataclass(frozen=True)
class ExtractedResume:
    text: str
    page_count: int


def sanitize_filename(filename: str | None) -> str:
    """Return a display-safe basename (no directories, control chars, or excessive length)."""
    name = PurePath((filename or "").replace("\\", "/")).name
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C").strip()
    return (name or "resume.pdf")[:255]


def normalize_text(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_pdf_upload(filename: str | None, content_type: str | None, data: bytes, max_bytes: int) -> None:
    """Strictly validate that an upload is a valid PDF."""
    if not filename or not filename.lower().endswith(".pdf"):
        raise InvalidFileError("Only PDF files are supported. Please upload a file ending in .pdf.")
    clean_type = (content_type or "").split(";")[0].strip().lower()
    if clean_type and clean_type not in {"application/pdf", "application/x-pdf", "application/acrobat", "application/octet-stream"}:
        raise InvalidFileError("The uploaded file does not appear to be a PDF.")
    if len(data) == 0:
        raise PDFProcessingError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise FileTooLargeError(f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.")
    if PDF_MAGIC not in data[:1024]:
        raise InvalidFileError("The file content is not a valid PDF (missing PDF header).")


def validate_document_upload(filename: str | None, content_type: str | None, data: bytes, max_bytes: int) -> None:
    """Validate any supported resume upload (PDF, DOCX, PPTX, Images, TXT)."""
    if not filename:
        raise InvalidFileError("Filename is missing. Please select a valid document.")

    ext = PurePath(filename.lower()).suffix
    if ext not in SUPPORTED_EXTENSIONS:
        raise InvalidFileError(
            f"Unsupported file format '{ext or 'unknown'}'. "
            "Please upload a PDF (.pdf), Word document (.docx), PowerPoint presentation (.pptx), image (.png, .jpg), or text file."
        )

    if len(data) == 0:
        raise PDFProcessingError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise FileTooLargeError(f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.")

    clean_type = (content_type or "").split(";")[0].strip().lower()
    if clean_type and not any(clean_type.startswith(p) for p in ALLOWED_MIME_PREFIXES) and clean_type != "application/octet-stream":
        raise InvalidFileError(f"Unexpected file type '{clean_type}'.")

    # Magic-byte integrity checks
    if ext == ".pdf" and PDF_MAGIC not in data[:1024]:
        raise InvalidFileError("The file content is not a valid PDF (missing PDF header).")
    if ext in {".docx", ".pptx"} and not data.startswith(ZIP_MAGIC):
        raise InvalidFileError(f"The {ext.upper()[1:]} file appears to be corrupted (invalid package header).")


def extract_text_from_pdf(data: bytes, max_pages: int = 20) -> ExtractedResume:
    """Extract normalized text from PDF bytes. Raises `PDFProcessingError` for unusable files."""
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
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
            except Exception:
                logger.warning("Failed to extract text from a PDF page; skipping it")
    except PDFProcessingError:
        raise
    except (PdfReadError, PyPdfError, ValueError, KeyError, TypeError, OSError) as exc:
        logger.info("Unreadable PDF: %s", type(exc).__name__)
        raise PDFProcessingError("The PDF appears to be corrupted or unreadable.") from exc
    except Exception as exc:
        logger.warning("Unexpected PDF parsing failure: %s", type(exc).__name__)
        raise PDFProcessingError("The PDF appears to be corrupted or unreadable.") from exc

    text = normalize_text("\n".join(parts))
    if len(text) < MIN_TEXT_CHARS:
        raise PDFProcessingError(
            "Could not extract enough text from this PDF. If it is a scanned image, "
            "please upload a text-based PDF or image."
        )
    return ExtractedResume(text=text[:MAX_TEXT_CHARS], page_count=page_count)


def extract_text_from_docx(data: bytes, max_pages: int = 20) -> ExtractedResume:
    """Extract text from Microsoft Word (.docx) documents."""
    try:
        import docx

        doc = docx.Document(io.BytesIO(data))
        parts: list[str] = []
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(p.text)
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
    except Exception as exc:
        logger.warning("DOCX extraction error: %s", exc)
        raise PDFProcessingError("The Word document appears to be corrupted or unreadable.") from exc

    text = normalize_text("\n".join(parts))
    if len(text) < MIN_TEXT_CHARS:
        raise PDFProcessingError("Could not extract enough text from this Word document.")

    words = len(text.split())
    page_count = max(1, min(max_pages, math.ceil(words / 350)))
    return ExtractedResume(text=text[:MAX_TEXT_CHARS], page_count=page_count)


def extract_text_from_pptx(data: bytes, max_pages: int = 20) -> ExtractedResume:
    """Extract text from PowerPoint (.pptx) presentations."""
    try:
        import pptx

        prs = pptx.Presentation(io.BytesIO(data))
        slide_count = len(prs.slides)
        if slide_count == 0:
            raise PDFProcessingError("The PowerPoint presentation has no slides.")
        if slide_count > max_pages:
            raise PDFProcessingError(f"The presentation has {slide_count} slides; maximum allowed is {max_pages}.")

        parts: list[str] = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame and shape.text.strip():
                    parts.append(shape.text)
    except PDFProcessingError:
        raise
    except Exception as exc:
        logger.warning("PPTX extraction error: %s", exc)
        raise PDFProcessingError("The PowerPoint presentation appears to be corrupted or unreadable.") from exc

    text = normalize_text("\n".join(parts))
    if len(text) < MIN_TEXT_CHARS:
        raise PDFProcessingError("Could not extract enough text from this presentation.")

    return ExtractedResume(text=text[:MAX_TEXT_CHARS], page_count=slide_count)


def extract_text_from_image(data: bytes) -> ExtractedResume:
    """Extract text from images using native Windows OCR (or graceful fallback)."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        img.verify()
        # Re-open after verify()
        img = Image.open(io.BytesIO(data))
    except Exception as exc:
        raise PDFProcessingError("The uploaded image is corrupted or in an unsupported format.") from exc

    text = ""
    try:
        import winocr

        res = winocr.recognize_pil_sync(img)
        lines = [l.get("text", "") for l in res.get("lines", []) if l.get("text")]
        if lines:
            text = "\n".join(lines)
        elif res.get("text"):
            text = res.get("text")
    except Exception as ocr_err:
        logger.warning("Image OCR failed: %s", ocr_err)

    text = normalize_text(text)
    if len(text) < MIN_TEXT_CHARS:
        raise PDFProcessingError(
            "Could not extract enough text from this image via OCR. "
            "Please ensure the image has clear, legible text, or upload a PDF/Word document."
        )

    return ExtractedResume(text=text[:MAX_TEXT_CHARS], page_count=1)


def extract_text_from_txt(data: bytes, max_pages: int = 20) -> ExtractedResume:
    """Extract text from plain text or markdown files."""
    try:
        raw = data.decode("utf-8")
    except UnicodeDecodeError:
        raw = data.decode("latin-1", errors="replace")

    text = normalize_text(raw)
    if len(text) < MIN_TEXT_CHARS:
        raise PDFProcessingError("The text file does not contain enough text.")

    words = len(text.split())
    page_count = max(1, min(max_pages, math.ceil(words / 350)))
    return ExtractedResume(text=text[:MAX_TEXT_CHARS], page_count=page_count)


def extract_text_from_document(filename: str | None, data: bytes, max_pages: int = 20) -> ExtractedResume:
    """Extract text from any supported format (PDF, DOCX, PPTX, Image, TXT)."""
    ext = PurePath((filename or "").lower()).suffix

    if ext == ".pdf":
        return extract_text_from_pdf(data, max_pages=max_pages)
    if ext in {".docx", ".doc"}:
        return extract_text_from_docx(data, max_pages=max_pages)
    if ext in {".pptx", ".ppt"}:
        return extract_text_from_pptx(data, max_pages=max_pages)
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}:
        return extract_text_from_image(data)
    if ext in {".txt", ".md", ".rtf"}:
        return extract_text_from_txt(data, max_pages=max_pages)

    # Fallback attempt by magic bytes
    if data.startswith(PDF_MAGIC):
        return extract_text_from_pdf(data, max_pages=max_pages)
    if data.startswith(ZIP_MAGIC):
        return extract_text_from_docx(data, max_pages=max_pages)

    raise InvalidFileError(f"Unsupported file format '{ext}'.")
