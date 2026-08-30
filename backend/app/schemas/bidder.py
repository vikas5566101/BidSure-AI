from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BidderCreate(BaseModel):
    company_name: str
    gstin: str | None = None
    pan: str | None = None
    udyam_number: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class BidderResponse(BaseModel):
    id: int
    company_name: str
    gstin: str | None
    pan: str | None
    udyam_number: str | None
    contact_email: str | None
    contact_phone: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)