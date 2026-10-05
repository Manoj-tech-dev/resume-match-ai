"""CLI script to generate sample resume PDFs for testing and local demonstration."""

from pathlib import Path
from tests.pdf_factory import SAMPLE_RESUME_LINES, make_pdf

if __name__ == "__main__":
    out_path = Path(__file__).resolve().parents[1] / "sample_resume.pdf"
    pdf_bytes = make_pdf(SAMPLE_RESUME_LINES)
    out_path.write_bytes(pdf_bytes)
    print(f"Generated sample resume PDF ({len(pdf_bytes)} bytes) at: {out_path}")
