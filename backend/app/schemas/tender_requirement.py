from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TenderRequirementCreate(BaseModel):
    requirement_type: str
    requirement_name: str
    description: str | None = None
    is_required: bool = True
    validation_config: str | None = None
    source_document: str | None = None
    source_chunk_ids: list[str] | None = None

class TenderRequirementResponse(BaseModel):
    id: int
    tender_id: int
    requirement_type: str
    requirement_name: str
    description: str | None
    is_required: bool
    validation_config: str | None
    source_document: str | None
    source_chunk_ids: list[str] | None
    created_at: datetime