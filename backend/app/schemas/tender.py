from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TenderCreate(BaseModel):
    title: str
    reference_number: str
    description: str | None = None


class TenderResponse(BaseModel):
    id: int
    title: str
    reference_number: str
    description: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)