from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ComplianceCheck(Base):
    """
    Represents the evaluation of one tender requirement
    against one bid submission.

    The compliance engine will use document extraction
    results and verification results as evidence.
    """

    __tablename__ = "compliance_checks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    bid_submission_id: Mapped[int] = mapped_column(
        ForeignKey("bid_submissions.id"),
        nullable=False,
        index=True,
    )

    tender_requirement_id: Mapped[int] = mapped_column(
        ForeignKey("tender_requirements.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    evidence: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    checked_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
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

    bid_submission = relationship(
        "BidSubmission",
        back_populates="compliance_checks",
    )

    tender_requirement = relationship(
        "TenderRequirement",
        back_populates="compliance_checks",
    )