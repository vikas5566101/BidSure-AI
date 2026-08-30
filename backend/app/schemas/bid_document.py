from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BidDocumentCreate(BaseModel):
    document_type: str
    file_name: str
    file_path: str
    content_type: str | None = None
    file_size: int | None = None


class BidDocumentResponse(BaseModel):
    id: int
    bid_submission_id: int
    document_type: str
    file_name: str
    file_path: str
    content_type: str | None
    file_size: int | None
    status: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)