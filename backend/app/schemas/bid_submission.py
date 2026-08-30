from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BidSubmissionCreate(BaseModel):
    tender_id: int
    bidder_id: int


class BidSubmissionResponse(BaseModel):
    id: int
    tender_id: int
    bidder_id: int
    status: str
    submitted_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)