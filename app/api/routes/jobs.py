from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.certificate import CertificateRecord
from app.models.job import GenerationJob, JobStatus
from app.schemas.certificate import CertificateResponse
from app.schemas.job import JobCreate, JobDetailResponse, JobListResponse, JobSummaryResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobSummaryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation request",
    description="Accepts a batch of recipients and schedules background generation.",
)
def create_generation_job(
    job_in: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = JobService.create_job(db, job_in)
    # Trigger background worker for non-blocking processing
    background_tasks.add_task(JobService.process_job_worker, job.id)
    return job


@router.get(
    "",
    response_model=JobListResponse,
    summary="List certificate generation jobs",
    description="Retrieve a paginated list of all certificate generation jobs.",
)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    jobs, total = JobService.list_jobs(db, skip=skip, limit=page_size)
    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        jobs=[JobSummaryResponse.model_validate(j) for j in jobs],
    )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job status and progress",
    description="Query real-time job status, aggregate counters, and per-recipient outcomes.",
)
def get_job_status(
    job_id: str,
    recipient_status: Optional[str] = Query(
        None,
        description="Optional filter for recipient statuses: PENDING, PROCESSING, COMPLETED, FAILED",
    ),
    limit: int = Query(200, ge=1, le=1000, description="Max recipients to return"),
    offset: int = Query(0, ge=0, description="Recipient offset"),
    db: Session = Depends(get_db),
):
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    query = db.query(CertificateRecord).filter(CertificateRecord.job_id == job_id)
    if recipient_status:
        query = query.filter(CertificateRecord.status == recipient_status.upper())

    certs = query.order_by(CertificateRecord.created_at).offset(offset).limit(limit).all()

    download_zip_url = None
    if job.success_count > 0:
        download_zip_url = f"{settings.BASE_URL}/api/v1/jobs/{job.id}/download-zip"

    return JobDetailResponse(
        id=job.id,
        event_title=job.event_title,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        status=job.status,
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        download_zip_url=download_zip_url,
        recipients=[CertificateResponse.model_validate(c) for c in certs],
    )


@router.get(
    "/{job_id}/download-zip",
    summary="Download all generated certificates as a ZIP archive",
    description="Packages all successfully generated certificates in this job into a single downloadable ZIP file.",
)
def download_job_zip(job_id: str, db: Session = Depends(get_db)):
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    if job.success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No certificates have been successfully generated for this job yet.",
        )

    zip_path = JobService.create_job_zip(db, job_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate ZIP archive for this job.",
        )

    return FileResponse(
        path=str(zip_path),
        filename=f"certificates_{job_id[:8]}.zip",
        media_type="application/zip",
    )
