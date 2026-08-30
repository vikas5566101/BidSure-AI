from sqlalchemy.orm import Session

from app.models.compliance_assessment import ComplianceAssessment
from app.schemas.compliance_assessment import (
    ComplianceAssessmentCreate,
    ComplianceAssessmentUpdate,
)


class ComplianceAssessmentRepository:

    def create(
        self,
        db: Session,
        assessment_data: ComplianceAssessmentCreate,
    ) -> ComplianceAssessment:

        assessment = ComplianceAssessment(
            **assessment_data.model_dump()
        )

        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        return assessment

    def get_by_id(
        self,
        db: Session,
        assessment_id: int,
    ) -> ComplianceAssessment | None:

        return (
            db.query(ComplianceAssessment)
            .filter(
                ComplianceAssessment.id == assessment_id
            )
            .first()
        )

    def get_by_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> list[ComplianceAssessment]:

        return (
            db.query(ComplianceAssessment)
            .filter(
                ComplianceAssessment.bid_submission_id
                == bid_submission_id
            )
            .order_by(
                ComplianceAssessment.created_at.desc()
            )
            .all()
        )

    def get_latest_by_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> ComplianceAssessment | None:

        return (
            db.query(ComplianceAssessment)
            .filter(
                ComplianceAssessment.bid_submission_id
                == bid_submission_id
            )
            .order_by(
                ComplianceAssessment.created_at.desc()
            )
            .first()
        )

    def update(
        self,
        db: Session,
        assessment: ComplianceAssessment,
        assessment_data: ComplianceAssessmentUpdate,
    ) -> ComplianceAssessment:

        update_data = assessment_data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(assessment, field, value)

        db.commit()
        db.refresh(assessment)

        return assessment


compliance_assessment_repository = ComplianceAssessmentRepository()