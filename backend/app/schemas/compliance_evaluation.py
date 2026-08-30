from pydantic import BaseModel


class ComplianceEvaluationRequest(BaseModel):
    bid_submission_id: int
    tender_requirement_id: int

    requirement_type: str
    requirement_name: str
    description: str | None = None
    is_required: bool = True
    validation_config: str | None = None

    extracted_data: dict | None = None
    verification_data: dict | None = None


class ComplianceEvaluationResult(BaseModel):
    status: str
    reason: str
    evidence: dict