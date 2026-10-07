from fastapi.testclient import TestClient


def test_api_root_and_health(client: TestClient):
    """Test API root metadata and health check endpoints."""
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert "endpoints" in resp_root.json()

    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"


def test_create_and_process_job_success(client: TestClient):
    """Test full workflow: create job, automatic background execution, status check."""
    payload = {
        "event_title": "Full-Stack Python Architecture",
        "issuer_name": "DevMasters Institute",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com", "custom_data": {"grade": "A+"}},
            {"name": "Bob Williams", "email": "bob@example.com", "custom_data": {"grade": "A"}},
            {"name": "Charlie Brown", "email": "charlie@example.com"},
        ],
    }

    # 1. Create Job (202 Accepted)
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    job_id = data["id"]
    assert data["event_title"] == "Full-Stack Python Architecture"
    assert data["issuer_name"] == "DevMasters Institute"
    assert data["total_recipients"] == 3

    # 2. Check Job Status
    # In FastAPI TestClient, background_tasks execute during request teardown
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    job_data = status_resp.json()

    assert job_data["id"] == job_id
    assert job_data["status"] == "COMPLETED"
    assert job_data["total_recipients"] == 3
    assert job_data["processed_count"] == 3
    assert job_data["success_count"] == 3
    assert job_data["failed_count"] == 0
    assert job_data["download_zip_url"] is not None

    # Check recipient items
    recipients = job_data["recipients"]
    assert len(recipients) == 3
    for r in recipients:
        assert r["status"] == "COMPLETED"
        assert r["download_url"] is not None
        assert r["error_message"] is None


def test_list_jobs(client: TestClient):
    """Test paginated job listing."""
    response = client.get("/api/v1/jobs?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "jobs" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] >= 1
    assert len(data["jobs"]) >= 1


def test_get_nonexistent_job_returns_404(client: TestClient):
    """Querying a non-existent job ID must return 404."""
    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_filter_job_recipients_by_status(client: TestClient):
    """Test filtering recipients in job status endpoint."""
    payload = {
        "event_title": "Docker Essentials",
        "issuer_name": "DevOps Hub",
        "recipients": [
            {"name": "Dev One", "email": "dev1@example.com"},
        ],
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    # Filter COMPLETED
    resp_completed = client.get(f"/api/v1/jobs/{job_id}?recipient_status=COMPLETED")
    assert resp_completed.status_code == 200
    assert len(resp_completed.json()["recipients"]) == 1

    # Filter FAILED
    resp_failed = client.get(f"/api/v1/jobs/{job_id}?recipient_status=FAILED")
    assert resp_failed.status_code == 200
    assert len(resp_failed.json()["recipients"]) == 0
