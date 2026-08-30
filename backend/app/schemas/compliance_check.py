from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplianceCheckCreate(BaseModel):
    bid_submission_id: int
    tender_requirement_id: int
    status: str = "PENDING"
    reason: str | None = None
    evidence: dict | None = None
    checked_by: str | None = None
    checked_at: datetime | None = None


class ComplianceCheckUpdate(BaseModel):
    status: str | None = None
    reason: str | None = None
    evidence: dict | None = None
    checked_by: str | None = None
    checked_at: datetime | None = None


class ComplianceCheckResponse(BaseModel):
    id: int
    bid_submission_id: int
    tender_requirement_id: int
    status: str
    reason: str | None
    evidence: dict | None
    checked_by: str | None
    checked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)