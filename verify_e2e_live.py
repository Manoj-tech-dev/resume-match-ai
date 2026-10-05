"""End-to-End smoke test script against running live backend and frontend servers."""

import sys
from pathlib import Path
import httpx

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
WORKSPACE = Path(__file__).resolve().parent
SAMPLE_PDF = WORKSPACE / "sample_resume.pdf"

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
    print("AI RESUME ANALYZER - LIVE E2E SMOKE TEST")
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

    # 3. Resume Upload & Analysis Generation
    print("\n[Step 3] Uploading sample PDF resume and analyzing against Job Description...")
    assert SAMPLE_PDF.exists(), f"Sample PDF not found at {SAMPLE_PDF}"
    pdf_bytes = SAMPLE_PDF.read_bytes()

    files = {"resume": ("sample_resume.pdf", pdf_bytes, "application/pdf")}
    data = {"job_description": JOB_DESCRIPTION}

    analyze_res = client.post(f"{BACKEND_URL}/api/analyze", files=files, data=data)
    assert analyze_res.status_code == 201, f"Analyze API returned {analyze_res.status_code}: {analyze_res.text}"
    record = analyze_res.json()
    record_id = record["id"]
    result = record["result"]

    print(f" -> Analysis successfully generated! (ID: {record_id})")
    print(f"    - Job Title: {record['job_title']}")
    print(f"    - Overall Score: {record['overall_score']}/100")
    print(f"    - Matching Skills ({len(result['matching_skills'])}): {result['matching_skills']}")
    print(f"    - Missing Skills ({len(result['missing_skills'])}): {result['missing_skills']}")
    print(f"    - Keyword Coverage: {result['keyword_analysis']['match_rate']}%")
    print(f"    - Suggestions ({len(result['suggestions'])}): {[s['title'] for s in result['suggestions'][:3]]}...")
    print(f"    - Improved Bullets ({len(result['improved_bullets'])}): 1st rewrite -> {result['improved_bullets'][0]['improved'][:70]}...")
    print(f"    - Interview Questions ({len(result['interview_questions'])}): 1st question -> {result['interview_questions'][0]['question']}")

    # 4. History Listing Check
    print("\n[Step 4] Checking analysis history...")
    history_res = client.get(f"{BACKEND_URL}/api/analyses")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["total"] >= 1, "History total should be at least 1"
    matching_item = next((item for item in history_data["items"] if item["id"] == record_id), None)
    assert matching_item is not None, f"Analysis {record_id} not found in history"
    print(f" -> Found analysis {record_id} in history list! (Total in DB: {history_data['total']})")

    # 5. Fetch Single Analysis Record
    print(f"\n[Step 5] Fetching single analysis record {record_id}...")
    single_res = client.get(f"{BACKEND_URL}/api/analyses/{record_id}")
    assert single_res.status_code == 200
    single_record = single_res.json()
    assert single_record["id"] == record_id
    assert single_record["result"]["overall_score"] == record["overall_score"]
    print(f" -> Successfully retrieved record from DB with matching score: {single_record['result']['overall_score']}")

    # 6. Delete Analysis
    print(f"\n[Step 6] Deleting analysis record {record_id}...")
    del_res = client.delete(f"{BACKEND_URL}/api/analyses/{record_id}")
    assert del_res.status_code == 204
    print(" -> Deleted record (HTTP 204 No Content)")

    # 7. Confirm 404 after Deletion
    print(f"\n[Step 7] Confirming record is deleted (expecting 404)...")
    get_deleted = client.get(f"{BACKEND_URL}/api/analyses/{record_id}")
    assert get_deleted.status_code == 404
    print(" -> Confirmed record no longer exists (HTTP 404 Not Found)")

    print("\n" + "=" * 60)
    print("ALL LIVE END-TO-END SMOKE TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_test()
