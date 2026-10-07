from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Full name of the certificate recipient")
    email: EmailStr = Field(..., description="Valid email address of the recipient")
    custom_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional metadata such as grade, distinction, or student_id",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Recipient name cannot be blank or whitespace only.")
        return clean


class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    status: str
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
