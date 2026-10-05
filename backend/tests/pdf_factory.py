"""Build small, valid text PDFs in-memory for tests (no extra dependencies)."""

from __future__ import annotations


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(lines: list[str], pages: int = 1) -> bytes:
    """Return bytes of a valid PDF with `lines` of text on each of `pages` pages."""
    objects: list[bytes] = []
    page_ids = [4 + i * 2 for i in range(pages)]

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {pages} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for pid in page_ids:
        ops = ["BT", "/F1 11 Tf", "14 TL", "50 750 Td"]
        for line in lines:
            ops.append(f"({_escape(line)}) Tj T*")
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {pid + 1} 0 R >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    return bytes(out)


SAMPLE_RESUME_LINES = [
    "Jane Doe - Software Engineer",
    "jane@example.com | github.com/janedoe",
    "SUMMARY",
    "Backend engineer with 5 years of experience building Python services.",
    "EXPERIENCE",
    "Acme Corp, Senior Software Engineer, 2020 - Present",
    "Worked on REST APIs with FastAPI and PostgreSQL for the billing platform team",
    "Built Docker based CI/CD pipelines with GitHub Actions for twelve microservices",
    "Mentored junior engineers and led code reviews across the backend team",
    "Beta Inc, Software Engineer, 2018 - 2020",
    "Developed React dashboards in TypeScript for internal analytics users",
    "PROJECTS",
    "Resume Parser - Python, Pandas, scikit-learn text classification tool",
    "EDUCATION",
    "Bachelor of Science in Computer Science, State University, 2018",
]

SAMPLE_JOB_DESCRIPTION = """Senior Backend Engineer

We are looking for a Senior Backend Engineer with 4+ years of experience.
Requirements:
- Strong Python and FastAPI skills
- Experience with PostgreSQL and Redis
- Docker and Kubernetes in production
- AWS cloud experience
- Building RESTful APIs and microservices
- CI/CD and unit testing with pytest
- Excellent communication and collaboration
Bachelor's degree in Computer Science or related field.
"""
