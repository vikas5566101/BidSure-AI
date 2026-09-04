from pydantic import BaseModel, Field


class RequirementExtractionRequest(BaseModel):
    text: str = Field(min_length=1)
    source_document: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)