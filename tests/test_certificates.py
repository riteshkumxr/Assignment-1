import io
import uuid
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.models.certificate import CertificateRecord, CertificateStatus
from app.models.job import GenerationJob, JobStatus


def test_retrieve_and_download_certificate(client: TestClient):
    """Test retrieving individual certificate metadata and downloading the PDF."""
    payload = {
        "event_title": "Quantum Computing Fundamentals",
        "issuer_name": "Institute for Quantum Physics",
        "recipients": [
            {"name": "Richard Feynman", "email": "richard.feynman@example.com"},
        ],
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["id"]

    job_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert job_resp.status_code == 200
    cert = job_resp.json()["recipients"][0]
    cert_id = cert["id"]

    # Get Certificate metadata
    cert_meta_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert cert_meta_resp.status_code == 200
    meta = cert_meta_resp.json()
    assert meta["id"] == cert_id
    assert meta["recipient_name"] == "Richard Feynman"
    assert meta["status"] == "COMPLETED"

    # Download the PDF file
    download_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert download_resp.content.startswith(b"%PDF")
    assert len(download_resp.content) > 2000


def test_download_failed_certificate_returns_400(client: TestClient):
    """Attempting to download a failed certificate returns 400 with the failure explanation."""
    payload = {
        "event_title": "Failure Test",
        "issuer_name": "Test Org",
        "recipients": [
            {"name": "Faulty Cert __FORCE_FAIL__", "email": "faulty@example.com"},
        ],
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    job_resp = client.get(f"/api/v1/jobs/{job_id}")
    cert_id = job_resp.json()["recipients"][0]["id"]

    download_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_resp.status_code == 400
    assert "failed" in download_resp.json()["detail"].lower()


def test_download_pending_certificate_returns_409(client: TestClient, db_session):
    """Attempting to download a certificate while still pending/processing returns 409 Conflict."""
    job = GenerationJob(
        id=str(uuid.uuid4()),
        event_title="In Progress Event",
        issuer_name="Test Org",
        issue_date="2026-10-07",
        status=JobStatus.PROCESSING.value,
    )
    cert = CertificateRecord(
        id=str(uuid.uuid4()),
        job_id=job.id,
        recipient_name="Still Generating",
        recipient_email="still@example.com",
        status=CertificateStatus.PROCESSING.value,
    )
    db_session.add(job)
    db_session.add(cert)
    db_session.commit()

    resp = client.get(f"/api/v1/certificates/{cert.id}/download")
    assert resp.status_code == 409
    assert "in progress" in resp.json()["detail"].lower()


def test_download_missing_file_returns_404(client: TestClient, db_session):
    """If DB says completed but file was deleted from disk, return 404."""
    job = GenerationJob(
        id=str(uuid.uuid4()),
        event_title="Ghost Cert Event",
        issuer_name="Test Org",
        issue_date="2026-10-07",
        status=JobStatus.COMPLETED.value,
    )
    cert = CertificateRecord(
        id=str(uuid.uuid4()),
        job_id=job.id,
        recipient_name="Ghost Recipient",
        recipient_email="ghost@example.com",
        status=CertificateStatus.COMPLETED.value,
        file_path="storage/test_certificates/nonexistent_file.pdf",
    )
    db_session.add(job)
    db_session.add(cert)
    db_session.commit()

    resp = client.get(f"/api/v1/certificates/{cert.id}/download")
    assert resp.status_code == 404
    assert "missing" in resp.json()["detail"].lower()


def test_download_job_bulk_zip(client: TestClient):
    """Test downloading all completed certificates in a job as a single ZIP archive."""
    payload = {
        "event_title": "Cloud Architecture Specialization",
        "issuer_name": "Cloud Providers Guild",
        "recipients": [
            {"name": "Ada Lovelace", "email": "ada@example.com"},
            {"name": "Charles Babbage", "email": "charles@example.com"},
        ],
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    # Download the ZIP
    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"

    # Inspect the ZIP in memory
    zip_bytes = io.BytesIO(zip_resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        file_list = zf.namelist()
        assert len(file_list) == 2
        for filename in file_list:
            assert filename.endswith(".pdf")
            content = zf.read(filename)
            assert content.startswith(b"%PDF")


def test_download_zip_for_job_with_no_success(client: TestClient):
    """Attempting to download ZIP when 0 certificates succeeded returns 400."""
    payload = {
        "event_title": "Zero Success Job",
        "issuer_name": "Test Org",
        "recipients": [
            {"name": "Failed Person __FORCE_FAIL__", "email": "fail@example.com"},
        ],
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-zip")
    assert zip_resp.status_code == 400
    assert "no certificates" in zip_resp.json()["detail"].lower()


def test_download_zip_nonexistent_job_returns_404(client: TestClient):
    """Attempting to download ZIP for non-existent job returns 404."""
    resp = client.get("/api/v1/jobs/nonexistent-id/download-zip")
    assert resp.status_code == 404


def test_get_nonexistent_certificate_returns_404(client: TestClient):
    """Querying a non-existent certificate returns 404."""
    resp = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_download_nonexistent_certificate_returns_404(client: TestClient):
    """Attempting to download a non-existent certificate returns 404."""
    resp = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download")
    assert resp.status_code == 404
