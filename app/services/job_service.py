from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import uuid
import zipfile
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models.certificate import CertificateRecord, CertificateStatus
from app.models.job import GenerationJob, JobStatus
from app.schemas.job import JobCreate
from app.services.generator import CertificateGenerator
from app.services.validator import RecipientValidator

logger = logging.getLogger("bulk_cert_generator.service")


class JobService:
    """Service orchestrating bulk certificate generation jobs."""

    @staticmethod
    def create_job(db: Session, job_in: JobCreate) -> GenerationJob:
        """Create a new certificate generation job and initialize recipient records."""
        job_id = str(uuid.uuid4())
        total_recipients = len(job_in.recipients)

        job = GenerationJob(
            id=job_id,
            event_title=job_in.event_title,
            issuer_name=job_in.issuer_name,
            issue_date=job_in.issue_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            status=JobStatus.PENDING.value,
            total_recipients=total_recipients,
            processed_count=0,
            success_count=0,
            failed_count=0,
        )
        db.add(job)

        # Batch create certificate records
        for recipient in job_in.recipients:
            cert = CertificateRecord(
                id=str(uuid.uuid4()),
                job_id=job_id,
                recipient_name=recipient.name,
                recipient_email=str(recipient.email),
                custom_data=recipient.custom_data,
                status=CertificateStatus.PENDING.value,
            )
            db.add(cert)

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def process_job_worker(job_id: str) -> None:
        """
        Background worker that processes all certificate generations for a job.
        Runs in an independent DB session to avoid lifecycle/concurrency issues.
        Ensures partial failure isolation per recipient.
        """
        db = SessionLocal()
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found in worker.")
                return

            # Transition job status to PROCESSING
            job.status = JobStatus.PROCESSING.value
            db.commit()

            job_dir = settings.storage_path / job_id
            job_dir.mkdir(parents=True, exist_ok=True)

            certificates = (
                db.query(CertificateRecord)
                .filter(CertificateRecord.job_id == job_id)
                .order_by(CertificateRecord.created_at)
                .all()
            )

            success_count = 0
            failed_count = 0

            for cert in certificates:
                cert.status = CertificateStatus.PROCESSING.value
                db.commit()

                try:
                    # 1. Validation check
                    is_valid, error_msg = RecipientValidator.validate_recipient(
                        cert.recipient_name, cert.recipient_email
                    )
                    if not is_valid:
                        raise ValueError(error_msg)

                    # 2. Generate PDF certificate
                    file_name = f"{cert.id}.pdf"
                    file_path = job_dir / file_name
                    download_url = f"{settings.BASE_URL}/api/v1/certificates/{cert.id}/download"

                    CertificateGenerator.generate_certificate(
                        certificate_id=cert.id,
                        recipient_name=cert.recipient_name,
                        recipient_email=cert.recipient_email,
                        event_title=job.event_title,
                        issuer_name=job.issuer_name,
                        issue_date=job.issue_date,
                        custom_data=cert.custom_data,
                        output_path=file_path,
                        verification_url=download_url,
                    )

                    # Mark record as COMPLETED
                    cert.status = CertificateStatus.COMPLETED.value
                    cert.file_path = str(file_path)
                    cert.download_url = download_url
                    cert.error_message = None
                    success_count += 1

                except Exception as exc:
                    # Isolate failure: Record error and proceed to remaining recipients
                    logger.warning(
                        f"Failed generating certificate for recipient {cert.recipient_name} ({cert.id}): {exc}"
                    )
                    cert.status = CertificateStatus.FAILED.value
                    cert.error_message = str(exc)
                    failed_count += 1

                # Increment job progress incrementally
                job.processed_count = success_count + failed_count
                job.success_count = success_count
                job.failed_count = failed_count
                db.commit()

            # Finalize Job Status
            if failed_count == 0:
                job.status = JobStatus.COMPLETED.value
            elif success_count > 0:
                job.status = JobStatus.PARTIALLY_COMPLETED.value
            else:
                job.status = JobStatus.FAILED.value

            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as exc:
            logger.exception(f"Fatal error during processing job {job_id}: {exc}")
            try:
                job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
                if job:
                    job.status = JobStatus.FAILED.value
                    job.completed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[GenerationJob]:
        """Fetch job by ID."""
        return db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    @staticmethod
    def list_jobs(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[GenerationJob], int]:
        """Fetch paginated list of generation jobs and total count."""
        total = db.query(GenerationJob).count()
        jobs = (
            db.query(GenerationJob)
            .order_by(GenerationJob.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return jobs, total

    @staticmethod
    def create_job_zip(db: Session, job_id: str) -> Optional[Path]:
        """Create a zip archive containing all successfully generated certificates."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return None

        successful_certs = (
            db.query(CertificateRecord)
            .filter(
                CertificateRecord.job_id == job_id,
                CertificateRecord.status == CertificateStatus.COMPLETED.value,
            )
            .all()
        )

        if not successful_certs:
            return None

        job_dir = settings.storage_path / job_id
        zip_path = job_dir / f"certificates_job_{job_id[:8]}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for cert in successful_certs:
                if cert.file_path and Path(cert.file_path).exists():
                    safe_name = "".join(c for c in cert.recipient_name if c.isalnum() or c in (" ", "_", "-")).strip()
                    safe_name = safe_name.replace(" ", "_") or "recipient"
                    archive_name = f"{safe_name}_{cert.id[:8]}.pdf"
                    zip_file.write(cert.file_path, arcname=archive_name)

        return zip_path
