from fastapi.testclient import TestClient

from tests.pdf_factory import make_pdf


def _post(client: TestClient, pdf: bytes | None, jd: str | None, filename: str = "resume.pdf", ctype: str = "application/pdf"):
    files = {"resume": (filename, pdf, ctype)} if pdf is not None else None
    data = {"job_description": jd} if jd is not None else None
    return client.post("/api/analyze", files=files, data=data)


def test_health(client: TestClient) -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["llm_provider"] == "mock"
    assert body["max_upload_size_mb"] == 1


def test_openapi_docs_available(client: TestClient) -> None:
    res = client.get("/api/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]
    assert {"/api/analyze", "/api/analyses", "/api/analyses/{analysis_id}", "/api/health"} <= set(paths)


class TestAnalyzeValidation:
    def test_missing_file(self, client: TestClient, job_description: str) -> None:
        res = _post(client, None, job_description)
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "validation_error"
        assert "resume" in res.json()["error"]["message"]

    def test_missing_job_description(self, client: TestClient, resume_pdf: bytes) -> None:
        res = _post(client, resume_pdf, None)
        assert res.status_code == 422
        assert res.json()["error"]["message"] == "Job description is required."

    def test_whitespace_job_description(self, client: TestClient, resume_pdf: bytes) -> None:
        res = _post(client, resume_pdf, "    \n\t ")
        assert res.status_code == 422
        assert "required" in res.json()["error"]["message"]

    def test_short_job_description(self, client: TestClient, resume_pdf: bytes) -> None:
        res = _post(client, resume_pdf, "Python dev")
        assert res.status_code == 422
        assert "too short" in res.json()["error"]["message"]

    def test_wrong_file_type(self, client: TestClient, job_description: str) -> None:
        res = _post(client, b"MZ\x90\x00" + b"0" * 50, job_description, filename="resume.exe", ctype="application/x-msdownload")
        assert res.status_code == 415
        assert res.json()["error"]["code"] == "invalid_file_type"

    def test_file_too_large(self, client: TestClient, job_description: str) -> None:
        big = b"%PDF-1.4\n" + b"0" * (1024 * 1024 + 10)
        res = _post(client, big, job_description)
        assert res.status_code == 413
        assert res.json()["error"]["code"] == "file_too_large"

    def test_empty_pdf(self, client: TestClient, job_description: str) -> None:
        res = _post(client, b"", job_description)
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "pdf_processing_error"

    def test_corrupted_pdf(self, client: TestClient, job_description: str) -> None:
        res = _post(client, b"%PDF-1.7\nthis is not really a pdf at all", job_description)
        assert res.status_code == 422
        assert "corrupted" in res.json()["error"]["message"]

    def test_pdf_with_no_text(self, client: TestClient, job_description: str) -> None:
        res = _post(client, make_pdf([]), job_description)
        assert res.status_code == 422
        assert "scanned" in res.json()["error"]["message"]


class TestAnalysisLifecycle:
    def test_full_flow(self, client: TestClient, resume_pdf: bytes, job_description: str) -> None:
        # Create
        res = _post(client, resume_pdf, job_description, filename="../secret/jane.pdf")
        assert res.status_code == 201, res.text
        record = res.json()
        assert record["resume_filename"] == "jane.pdf"
        assert record["provider"] == "mock"
        assert record["created_at"].endswith(("Z", "+00:00"))
        result = record["result"]
        assert 0 <= result["overall_score"] <= 100
        assert result["overall_score"] == record["overall_score"]
        assert "Python" in result["matching_skills"]
        assert "Kubernetes" in result["missing_skills"]
        assert result["job_title"] == "Senior Backend Engineer"

        # List
        listing = client.get("/api/analyses").json()
        assert listing["total"] == 1
        assert listing["items"][0]["id"] == record["id"]
        assert "result" not in listing["items"][0]

        # Get
        fetched = client.get(f"/api/analyses/{record['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["result"] == result

        # Delete
        assert client.delete(f"/api/analyses/{record['id']}").status_code == 204
        assert client.get(f"/api/analyses/{record['id']}").status_code == 404
        assert client.delete(f"/api/analyses/{record['id']}").status_code == 404
        assert client.get("/api/analyses").json()["total"] == 0

    def test_get_unknown_id(self, client: TestClient) -> None:
        res = client.get("/api/analyses/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "not_found"

    def test_invalid_id_format(self, client: TestClient) -> None:
        assert client.get("/api/analyses/not-a-uuid").status_code == 422
        assert client.delete("/api/analyses/1").status_code == 422

    def test_pagination_params_validated(self, client: TestClient) -> None:
        assert client.get("/api/analyses?limit=0").status_code == 422
        assert client.get("/api/analyses?limit=101").status_code == 422
        assert client.get("/api/analyses?offset=-1").status_code == 422

    def test_docx_upload_success(self, client: TestClient, job_description: str) -> None:
        import io, docx
        doc = docx.Document()
        doc.add_heading("Jane Doe - Senior Engineer", 0)
        doc.add_paragraph("Experienced software engineer with 5 years building Python, FastAPI, and PostgreSQL microservices.")
        buf = io.BytesIO()
        doc.save(buf)
        res = _post(
            client,
            buf.getvalue(),
            job_description,
            filename="resume.docx",
            ctype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert res.status_code == 201
        assert res.json()["resume_filename"] == "resume.docx"
        assert res.json()["result"]["overall_score"] > 0

    def test_txt_upload_success(self, client: TestClient, job_description: str) -> None:
        text = "Jane Doe\nExperienced software engineer with 5 years building Python, FastAPI, and PostgreSQL microservices.\nDocker, Git, CI/CD, Linux."
        res = _post(client, text.encode("utf-8"), job_description, filename="resume.txt", ctype="text/plain")
        assert res.status_code == 201
        assert res.json()["resume_filename"] == "resume.txt"
        assert res.json()["result"]["overall_score"] > 0
