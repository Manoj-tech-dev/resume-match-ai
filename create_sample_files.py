"""Generate sample resumes in multiple formats: PDF, DOCX, PPTX, TXT, and PNG image."""

import io
from pathlib import Path
import docx
import pptx
from PIL import Image, ImageDraw

WORKSPACE = Path(__file__).resolve().parent

SAMPLE_LINES = [
    "Jane Doe - Senior Full-Stack & Backend Engineer",
    "jane@example.com | github.com/janedoe | (555) 019-2834",
    "",
    "SUMMARY",
    "Experienced software engineer with 5+ years architecting microservices, APIs, and web applications.",
    "Specialized in Python, FastAPI, React, TypeScript, Docker, and PostgreSQL database performance tuning.",
    "",
    "WORK EXPERIENCE",
    "Acme Corp — Senior Backend Engineer (2020 - Present)",
    "• Architected high-throughput REST APIs using FastAPI and PostgreSQL handling 50M+ monthly requests.",
    "• Containerized services with Docker and deployed to AWS Kubernetes (EKS) using GitHub Actions CI/CD.",
    "• Reduced database query latency by 35% through indexing and Redis distributed caching.",
    "• Led team code reviews, mentored 4 junior engineers, and maintained 90%+ pytest test coverage.",
    "",
    "Beta Solutions — Full-Stack Developer (2018 - 2020)",
    "• Developed internal customer analytics dashboard using React, TypeScript, and Node.js.",
    "• Integrated third-party payment APIs with robust transaction rollback and auditing.",
    "",
    "EDUCATION",
    "Bachelor of Science in Computer Science — State University (2018)",
    "",
    "SKILLS",
    "Python, FastAPI, TypeScript, React, PostgreSQL, Docker, Kubernetes, AWS, Redis, Git, CI/CD, Unit Testing",
]

def generate_samples():
    # 1. TXT
    txt_path = WORKSPACE / "sample_resume.txt"
    txt_path.write_text("\n".join(SAMPLE_LINES), encoding="utf-8")
    print(f"Generated {txt_path.name}")

    # 2. DOCX
    doc_path = WORKSPACE / "sample_resume.docx"
    doc = docx.Document()
    doc.add_heading("Jane Doe - Senior Backend Engineer", 0)
    for line in SAMPLE_LINES[3:]:
        if line in {"SUMMARY", "WORK EXPERIENCE", "EDUCATION", "SKILLS"}:
            doc.add_heading(line, level=1)
        elif line:
            doc.add_paragraph(line)
    doc.save(str(doc_path))
    print(f"Generated {doc_path.name}")

    # 3. PPTX
    pptx_path = WORKSPACE / "sample_resume.pptx"
    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Jane Doe - Technical Resume & Portfolio"
    body = slide.shapes.placeholders[1]
    body.text = (
        "Senior Backend Engineer with 5+ years experience.\n"
        "• Core Skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, React, TypeScript\n"
        "• Acme Corp: Architected REST APIs, optimized DB queries by 35%, deployed CI/CD on Kubernetes\n"
        "• Education: Bachelor of Science in Computer Science"
    )
    prs.save(str(pptx_path))
    print(f"Generated {pptx_path.name}")

    # 4. PNG Image (with clear typography for OCR)
    png_path = WORKSPACE / "sample_resume.png"
    img = Image.new("RGB", (900, 500), color="#ffffff")
    draw = ImageDraw.Draw(img)
    text_content = (
        "JANE DOE - SENIOR BACKEND ENGINEER\n\n"
        "SUMMARY: 5+ years experience building Python, FastAPI, and PostgreSQL microservices.\n\n"
        "EXPERIENCE:\n"
        "- Senior Backend Engineer at Acme Corp (2020 - Present)\n"
        "- Designed scalable REST APIs and managed PostgreSQL databases and Redis caching\n"
        "- Containerized microservices with Docker and deployed to AWS Kubernetes clusters\n"
        "- Maintained unit tests with pytest and CI/CD pipelines with GitHub Actions\n\n"
        "EDUCATION: Bachelor of Science in Computer Science\n\n"
        "SKILLS: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, Redis, React, TypeScript, Git"
    )
    draw.text((40, 40), text_content, fill="#111827", spacing=8)
    img.save(str(png_path), format="PNG")
    print(f"Generated {png_path.name}")

if __name__ == "__main__":
    generate_samples()
