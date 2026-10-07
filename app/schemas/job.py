from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.config import settings
from app.schemas.certificate import CertificateResponse, RecipientInput


class JobCreate(BaseModel):
    event_title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the course, event, workshop, or award",
        examples=["Advanced Machine Learning Specialization"],
    )
    issuer_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the issuing organization, university, or company",
        examples=["Google DeepMind Academy"],
    )
    issue_date: Optional[str] = Field(
        default_factory=lambda: date.today().isoformat(),
        description="Certificate issuance date formatted as YYYY-MM-DD or readable string. Defaults to current date if omitted.",
        examples=["2026-10-07"],
    )
    recipients: List[RecipientInput] = Field(
        ...,
        min_length=1,
        description="List of recipients for whom certificates should be generated.",
    )

    @field_validator("event_title", "issuer_name")
    @classmethod
    def validate_non_blank(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Field cannot be blank or whitespace only.")
        return clean

    @field_validator("issue_date")
    @classmethod
    def default_issue_date(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return date.today().isoformat()
        return v.strip()

    @field_validator("recipients")
    @classmethod
    def validate_batch_size(cls, v: List[RecipientInput]) -> List[RecipientInput]:
        if not v:
            raise ValueError("Recipient list cannot be empty.")
        if len(v) > settings.MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch exceeds maximum limit of {settings.MAX_BATCH_SIZE} recipients."
            )
        return v


class JobSummaryResponse(BaseModel):
    id: str
    event_title: str
    issuer_name: str
    issue_date: str
    status: str
    total_recipients: int
    processed_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobDetailResponse(JobSummaryResponse):
    recipients: List[CertificateResponse] = []
    download_zip_url: Optional[str] = None


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    jobs: List[JobSummaryResponse]
