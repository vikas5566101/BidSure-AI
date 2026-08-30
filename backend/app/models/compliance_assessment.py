from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ComplianceAssessment(Base):
    """
    Represents the overall compliance assessment of a bid submission.

    The assessment summarizes individual ComplianceCheck records.
    Scoring, risk calculation, and recommendation generation will
    be implemented by the appropriate business/AI services later.
    """

    __tablename__ = "compliance_assessments"

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

    score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    risk_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assessment_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    assessed_at: Mapped[datetime | None] = mapped_column(
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
        back_populates="compliance_assessments",
    )