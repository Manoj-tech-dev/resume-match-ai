import io
import pytest
from PIL import Image, ImageDraw

from app.core.exceptions import InvalidFileError, PDFProcessingError
from app.services.pdf_extractor import (
    extract_text_from_document,
    extract_text_from_docx,
    extract_text_from_pptx,
    extract_text_from_txt,
    validate_document_upload,
)

MB = 5 * 1024 * 1024


def test_validate_document_upload_supported_types() -> None:
    # PDF
    validate_document_upload("resume.pdf", "application/pdf", b"%PDF-1.4\ncontent", MB)
    # DOCX
    validate_document_upload("resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK\x03\x04" + b"0" * 50, MB)
    # PPTX
    validate_document_upload("slides.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", b"PK\x03\x04" + b"0" * 50, MB)
    # PNG Image
    validate_document_upload("scan.png", "image/png", b"\x89PNG\r\n\x1a\n" + b"0" * 50, MB)
    # TXT
    validate_document_upload("resume.txt", "text/plain", b"Sample text resume content", MB)


def test_validate_document_upload_rejects_unsupported() -> None:
    with pytest.raises(InvalidFileError, match="Unsupported file format"):
        validate_document_upload("resume.exe", "application/x-msdownload", b"MZ" * 50, MB)

    with pytest.raises(InvalidFileError, match="Unsupported file format"):
        validate_document_upload("script.py", "text/x-python", b"print('hello')" * 10, MB)


def test_docx_extraction() -> None:
    import docx
    doc = docx.Document()
    doc.add_heading("Jane Doe - Staff Software Engineer", 0)
    doc.add_paragraph("Over 8 years of distributed systems engineering using Python, FastAPI, and PostgreSQL.")
    doc.add_paragraph("Built Kafka pipelines handling millions of events daily.")
    buf = io.BytesIO()
    doc.save(buf)

    extracted = extract_text_from_docx(buf.getvalue())
    assert extracted.page_count >= 1
    assert "Jane Doe" in extracted.text
    assert "FastAPI" in extracted.text


def test_pptx_extraction() -> None:
    import pptx
    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Jane Doe Technical Portfolio"
    slide.placeholders[1].text = "Senior Python Developer with expertise in Docker, Kubernetes, and AWS."
    buf = io.BytesIO()
    prs.save(buf)

    extracted = extract_text_from_pptx(buf.getvalue())
    assert extracted.page_count == 1
    assert "Jane Doe" in extracted.text
    assert "Kubernetes" in extracted.text


def test_txt_extraction() -> None:
    text = "Jane Doe\nFull-Stack Developer skilled in React, TypeScript, Node.js, and PostgreSQL.\nBuilt 10+ web apps."
    extracted = extract_text_from_txt(text.encode("utf-8"))
    assert extracted.page_count == 1
    assert "React" in extracted.text
    assert "TypeScript" in extracted.text


def test_unified_extract_router() -> None:
    # Router routes to docx
    import docx
    doc = docx.Document()
    doc.add_paragraph("Jane Doe developer with extensive experience building cloud native apps.")
    buf = io.BytesIO()
    doc.save(buf)

    res = extract_text_from_document("my_resume.docx", buf.getvalue())
    assert "cloud native" in res.text
