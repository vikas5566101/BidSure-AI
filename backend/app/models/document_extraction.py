from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DocumentExtraction(Base):
    """
    Stores the result of a document extraction attempt.

    The actual extraction is performed by the Document Intelligence
    module. This model stores the resulting structured data and
    processing metadata.
    """

    __tablename__ = "document_extractions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    bid_document_id: Mapped[int] = mapped_column(
        ForeignKey("bid_documents.id"),
        nullable=False,
        index=True,
    )

    extraction_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
    )

    extracted_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    extractor_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    extractor_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
    )

    document = relationship(
        "BidDocument",
        back_populates="extractions",
    )