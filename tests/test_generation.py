from pathlib import Path
import pytest
from app.services.generator import CertificateGenerator


def test_certificate_generator_valid_pdf(tmp_path: Path):
    """Ensure generator creates a valid, readable PDF file."""
    output_pdf = tmp_path / "cert_test.pdf"

    pdf_bytes = CertificateGenerator.generate_certificate(
        certificate_id="cert-12345-uuid",
        recipient_name="Grace Hopper",
        recipient_email="grace.hopper@example.com",
        event_title="Advanced Compiler Design",
        issuer_name="Computer Pioneers Institute",
        issue_date="2026-10-07",
        custom_data={"grade": "A+", "credits": "4.0"},
        output_path=output_pdf,
        verification_url="https://verify.example.com/cert-12345-uuid",
    )

    # 1. Check returned bytes
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF"), "Must contain standard PDF header magic bytes"

    # 2. Check saved file
    assert output_pdf.exists()
    assert output_pdf.stat().st_size == len(pdf_bytes)


def test_certificate_generator_handles_minimal_data():
    """Ensure generator works even when custom_data is None."""
    pdf_bytes = CertificateGenerator.generate_certificate(
        certificate_id="minimal-uuid",
        recipient_name="Alan Turing",
        recipient_email="alan@turing.org",
        event_title="Theoretical Cryptography",
        issuer_name="Bletchley Park Academy",
        issue_date="2026-10-07",
        custom_data=None,
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 2000


def test_certificate_generator_raises_on_force_fail():
    """Ensure generator raises an exception when simulated failure flag is present."""
    with pytest.raises(RuntimeError) as exc_info:
        CertificateGenerator.generate_certificate(
            certificate_id="fail-uuid",
            recipient_name="Corrupted Recipient __FORCE_FAIL__",
            recipient_email="fail@example.com",
            event_title="Failure Testing",
            issuer_name="Test Org",
            issue_date="2026-10-07",
        )

    assert "Simulated generation failure" in str(exc_info.value)
