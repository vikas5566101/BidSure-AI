from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TenderRequirement(Base):
    """
    Represents a statutory, eligibility, or tender-specific
    requirement for a tender.
    """

    __tablename__ = "tender_requirements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tender_id: Mapped[int] = mapped_column(
        ForeignKey("tenders.id"),
        nullable=False,
        index=True,
    )

    requirement_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    requirement_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    validation_config: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_document: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_chunk_ids: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    tender = relationship(
        "Tender",
        back_populates="requirements",
    )

    compliance_checks = relationship(
        "ComplianceCheck",
        back_populates="tender_requirement",
        cascade="all, delete-orphan",
    )