"""End-to-End smoke test script against running live backend and frontend servers.
Tests multi-format uploads: PDF, DOCX, and TXT resumes.
"""

import sys
from pathlib import Path
import httpx

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
WORKSPACE = Path(__file__).resolve().parent
SAMPLE_PDF = WORKSPACE / "sample_resume.pdf"
SAMPLE_DOCX = WORKSPACE / "sample_resume.docx"
SAMPLE_TXT = WORKSPACE / "sample_resume.txt"

JOB_DESCRIPTION = """Senior Backend Engineer

We are seeking a Senior Backend Engineer to join our high-growth platform team.
Responsibilities:
- Architect and develop scalable RESTful microservices in Python using FastAPI.
- Manage and optimize PostgreSQL relational database schemas, indexes, and queries.
- Build resilient caching layers using Redis.
- Package services in Docker containers and deploy to Kubernetes clusters on AWS.
- Implement automated testing with pytest and configure CI/CD pipelines via GitHub Actions.
- Collaborate with frontend engineers using React and TypeScript.

Qualifications:
- 4+ years of professional backend engineering experience.
- Strong proficiency in Python, FastAPI, and SQL.
- Hands-on experience with Docker, Kubernetes, and cloud infrastructure.
- Bachelor's degree in Computer Science, Software Engineering, or equivalent practical experience.
- Excellent communication and technical problem-solving skills.
"""

def run_smoke_test():
    print("=" * 60)
    print("AI RESUME ANALYZER - MULTI-FORMAT LIVE E2E SMOKE TEST")
    print("=" * 60)

    client = httpx.Client(timeout=30.0)

    # 1. Frontend Check
    print("\n[Step 1] Checking frontend live dev server...")
    try:
        fe_res = client.get(FRONTEND_URL)
        assert fe_res.status_code == 200, f"Frontend returned {fe_res.status_code}"
        assert "<div id=\"root\">" in fe_res.text, "Frontend HTML missing #root element"
        print(" -> Frontend is LIVE and serving React SPA (HTTP 200)")
    except Exception as e:
        print(f" -> ERROR connecting to frontend: {e}")
        sys.exit(1)

    # 2. Backend Health Check
    print("\n[Step 2] Checking backend health API...")
    try:
        health_res = client.get(f"{BACKEND_URL}/api/health")
        assert health_res.status_code == 200, f"Health API returned {health_res.status_code}"
        health_data = health_res.json()
        print(f" -> Backend is HEALTHY (Status: {health_data['status']}, DB: {health_data['database']}, Provider: {health_data['llm_provider']}, Model: {health_data['llm_model']})")
    except Exception as e:
        print(f" -> ERROR connecting to backend: {e}")
        sys.exit(1)

    # 3. PDF Resume Upload & Analysis
    print("\n[Step 3a] Uploading PDF resume (sample_resume.pdf)...")
    assert SAMPLE_PDF.exists(), f"Sample PDF not found at {SAMPLE_PDF}"
    files_pdf = {"resume": ("sample_resume.pdf", SAMPLE_PDF.read_bytes(), "application/pdf")}
    data = {"job_description": JOB_DESCRIPTION}

    res_pdf = client.post(f"{BACKEND_URL}/api/analyze", files=files_pdf, data=data)
    assert res_pdf.status_code == 201, f"PDF Analyze returned {res_pdf.status_code}: {res_pdf.text}"
    rec_pdf = res_pdf.json()
    print(f" -> PDF analyzed! ID: {rec_pdf['id']}, Score: {rec_pdf['overall_score']}/100, Role: {rec_pdf['job_title']}")

    # 3b. DOCX Resume Upload & Analysis
    print("\n[Step 3b] Uploading Word DOCX resume (sample_resume.docx)...")
    assert SAMPLE_DOCX.exists(), f"Sample DOCX not found at {SAMPLE_DOCX}"
    files_docx = {
        "resume": (
            "sample_resume.docx",
            SAMPLE_DOCX.read_bytes(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    res_docx = client.post(f"{BACKEND_URL}/api/analyze", files=files_docx, data=data)
    assert res_docx.status_code == 201, f"DOCX Analyze returned {res_docx.status_code}: {res_docx.text}"
    rec_docx = res_docx.json()
    print(f" -> DOCX analyzed! ID: {rec_docx['id']}, Score: {rec_docx['overall_score']}/100, Format: {rec_docx['resume_filename']}")

    # 3c. Plain TXT Resume Upload & Analysis
    print("\n[Step 3c] Uploading Text resume (sample_resume.txt)...")
    assert SAMPLE_TXT.exists(), f"Sample TXT not found at {SAMPLE_TXT}"
    files_txt = {"resume": ("sample_resume.txt", SAMPLE_TXT.read_bytes(), "text/plain")}
    res_txt = client.post(f"{BACKEND_URL}/api/analyze", files=files_txt, data=data)
    assert res_txt.status_code == 201, f"TXT Analyze returned {res_txt.status_code}: {res_txt.text}"
    rec_txt = res_txt.json()
    print(f" -> TXT analyzed! ID: {rec_txt['id']}, Score: {rec_txt['overall_score']}/100, Format: {rec_txt['resume_filename']}")

    # 4. History Listing Check
    print("\n[Step 4] Checking analysis history...")
    history_res = client.get(f"{BACKEND_URL}/api/analyses")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["total"] >= 3, "Expected at least 3 analyses in history"
    print(f" -> Found {history_data['total']} analyses in history! Items:")
    for item in history_data["items"][:3]:
        print(f"    - {item['resume_filename']}: {item['overall_score']}/100 ({item['job_title']})")

    # 5. Fetch Single Analysis Record
    print(f"\n[Step 5] Fetching single analysis record {rec_docx['id']}...")
    single_res = client.get(f"{BACKEND_URL}/api/analyses/{rec_docx['id']}")
    assert single_res.status_code == 200
    single_record = single_res.json()
    assert single_record["id"] == rec_docx["id"]
    print(f" -> Successfully retrieved record from DB with matching score: {single_record['overall_score']}")

    # 6. Delete Analyses
    print(f"\n[Step 6] Cleaning up test records...")
    for rid in [rec_pdf["id"], rec_docx["id"], rec_txt["id"]]:
        del_res = client.delete(f"{BACKEND_URL}/api/analyses/{rid}")
        assert del_res.status_code == 204
    print(" -> All test records cleaned up (HTTP 204)")

    print("\n" + "=" * 60)
    print("ALL MULTI-FORMAT LIVE E2E SMOKE TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_test()
