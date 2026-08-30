from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplianceAssessmentCreate(BaseModel):
    bid_submission_id: int
    score: float | None = None
    risk_level: str | None = None
    recommendation: str | None = None
    status: str = "PENDING"
    summary: str | None = None
    assessment_metadata: dict | None = None


class ComplianceAssessmentUpdate(BaseModel):
    score: float | None = None
    risk_level: str | None = None
    recommendation: str | None = None
    status: str | None = None
    summary: str | None = None
    assessment_metadata: dict | None = None
    assessed_at: datetime | None = None


class ComplianceAssessmentResponse(BaseModel):
    id: int
    bid_submission_id: int
    score: float | None
    risk_level: str | None
    recommendation: str | None
    status: str
    summary: str | None
    assessment_metadata: dict | None
    assessed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)