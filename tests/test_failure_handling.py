from fastapi.testclient import TestClient


def test_individual_failure_does_not_halt_job(client: TestClient):
    """
    CRITICAL REQUIREMENT:
    A failure while generating one certificate should not prevent
    other valid certificates in the same job from being generated.
    """
    payload = {
        "event_title": "Resilience in Distributed Systems",
        "issuer_name": "Reliability Engineering Guild",
        "issue_date": "2026-10-07",
        "recipients": [
            {
                "name": "Sophia Davis",
                "email": "sophia@example.com",
                "custom_data": {"distinction": "Honors"},
            },
            {
                "name": "Corrupted Recipient __FORCE_FAIL__",
                "email": "corrupted@example.com",
            },
            {
                "name": "Marcus Vance",
                "email": "marcus@example.com",
                "custom_data": {"distinction": "High Honors"},
            },
        ],
    }

    # 1. Submit the job
    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["id"]

    # 2. Check Job Status
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()

    # Verify overall job status reflects partial success
    assert data["status"] == "PARTIALLY_COMPLETED"
    assert data["total_recipients"] == 3
    assert data["processed_count"] == 3
    assert data["success_count"] == 2
    assert data["failed_count"] == 1

    # Map recipients by name for assertions
    recipients_by_name = {r["recipient_name"]: r for r in data["recipients"]}

    # Verify first valid recipient succeeded
    r1 = recipients_by_name["Sophia Davis"]
    assert r1["status"] == "COMPLETED"
    assert r1["download_url"] is not None
    assert r1["error_message"] is None

    # Verify failing recipient failed gracefully with informative error
    r2 = recipients_by_name["Corrupted Recipient __FORCE_FAIL__"]
    assert r2["status"] == "FAILED"
    assert r2["download_url"] is None
    assert r2["error_message"] is not None
    assert "Simulated generation failure" in r2["error_message"]

    # Verify subsequent valid recipient STILL SUCCEEDED (did not abort)
    r3 = recipients_by_name["Marcus Vance"]
    assert r3["status"] == "COMPLETED"
    assert r3["download_url"] is not None
    assert r3["error_message"] is None


def test_all_recipients_failed_job_status(client: TestClient):
    """When every certificate in a job fails, the job status should be FAILED."""
    payload = {
        "event_title": "Fault Tolerance Workshop",
        "issuer_name": "Chaos Engineering Org",
        "recipients": [
            {"name": "Bad Recipient 1 __FORCE_FAIL__", "email": "bad1@example.com"},
            {"name": "Bad Recipient 2 __FORCE_FAIL__", "email": "bad2@example.com"},
        ],
    }

    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["id"]

    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()

    assert data["status"] == "FAILED"
    assert data["total_recipients"] == 2
    assert data["processed_count"] == 2
    assert data["success_count"] == 0
    assert data["failed_count"] == 2
