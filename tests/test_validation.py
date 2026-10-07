import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.schemas.job import JobCreate
from app.services.validator import RecipientValidator


def test_validation_empty_recipients_list(client: TestClient):
    """Submitting a request with an empty recipients list must fail validation."""
    payload = {
        "event_title": "Docker & Kubernetes Mastery",
        "issuer_name": "Cloud Native Academy",
        "recipients": [],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_validation_invalid_recipient_email(client: TestClient):
    """Submitting an invalid email address format must fail validation."""
    payload = {
        "event_title": "Docker & Kubernetes Mastery",
        "issuer_name": "Cloud Native Academy",
        "recipients": [
            {"name": "Alice Smith", "email": "alice-at-example-dot-com"},
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_validation_empty_recipient_name(client: TestClient):
    """Submitting empty or whitespace-only name must fail validation."""
    payload = {
        "event_title": "Docker & Kubernetes Mastery",
        "issuer_name": "Cloud Native Academy",
        "recipients": [
            {"name": "   ", "email": "valid.user@example.com"},
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_event_title(client: TestClient):
    """Submitting empty or whitespace-only event title must fail validation."""
    payload = {
        "event_title": "   ",
        "issuer_name": "Cloud Native Academy",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_issuer_name(client: TestClient):
    """Submitting empty or whitespace-only issuer name must fail validation."""
    payload = {
        "event_title": "Docker Mastery",
        "issuer_name": " ",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_exceeds_max_batch_size():
    """Ensure JobCreate rejects batches larger than MAX_BATCH_SIZE."""
    orig_limit = settings.MAX_BATCH_SIZE
    try:
        settings.MAX_BATCH_SIZE = 2
        with pytest.raises(ValueError) as exc:
            JobCreate(
                event_title="Big Course",
                issuer_name="Academy",
                recipients=[
                    {"name": "User 1", "email": "u1@example.com"},
                    {"name": "User 2", "email": "u2@example.com"},
                    {"name": "User 3", "email": "u3@example.com"},
                ],
            )
        assert "exceeds maximum limit" in str(exc.value)
    finally:
        settings.MAX_BATCH_SIZE = orig_limit


def test_recipient_validator_direct():
    """Unit tests for RecipientValidator logic."""
    # Valid inputs
    valid, err = RecipientValidator.validate_recipient("John Doe", "john@example.com")
    assert valid is True
    assert err == ""

    # Blank name
    valid, err = RecipientValidator.validate_recipient("  ", "john@example.com")
    assert valid is False
    assert "empty" in err.lower()

    # Name too long
    valid, err = RecipientValidator.validate_recipient("A" * 200, "john@example.com")
    assert valid is False
    assert "length" in err.lower()

    # Illegal control character
    valid, err = RecipientValidator.validate_recipient("John\x00Doe", "john@example.com")
    assert valid is False
    assert "control character" in err.lower()

    # Blank email
    valid, err = RecipientValidator.validate_recipient("John Doe", "  ")
    assert valid is False
    assert "email cannot be empty" in err.lower()

    # Invalid email format
    valid, err = RecipientValidator.validate_recipient("John Doe", "invalid-email")
    assert valid is False
    assert "invalid email" in err.lower()
