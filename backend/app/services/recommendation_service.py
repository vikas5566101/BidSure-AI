from sqlalchemy.orm import Session

from app.models.compliance_assessment import ComplianceAssessment
from app.repositories.compliance_assessment_repository import (
    compliance_assessment_repository,
)
from app.repositories.compliance_check_repository import (
    compliance_check_repository,
)


class RecommendationService:
    """
    Generates a deterministic recommendation from the
    current compliance assessment and its individual checks.

    AI/RAG-based recommendation generation will be added
    in a later phase.
    """

    def generate_recommendation(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> ComplianceAssessment:

        # --------------------------------------------------
        # 1. Retrieve latest assessment
        # --------------------------------------------------

        assessment = (
            compliance_assessment_repository
            .get_latest_by_submission(
                db,
                bid_submission_id,
            )
        )

        if assessment is None:
            raise ValueError(
                "Compliance assessment not found for "
                f"bid submission: {bid_submission_id}"
            )

        # --------------------------------------------------
        # 2. Retrieve compliance checks
        # --------------------------------------------------

        checks = (
            compliance_check_repository.get_by_submission(
                db,
                bid_submission_id,
            )
        )

        # --------------------------------------------------
        # 3. Identify failed requirements
        # --------------------------------------------------

        failed_checks = [
            check
            for check in checks
            if check.status.upper() == "FAIL"
        ]

        # --------------------------------------------------
        # 4. Identify requirements needing review
        # --------------------------------------------------

        review_checks = [
            check
            for check in checks
            if check.status.upper() == "REVIEW"
        ]

        # --------------------------------------------------
        # 5. Identify pending requirements
        # --------------------------------------------------

        pending_checks = [
            check
            for check in checks
            if check.status.upper() == "PENDING"
        ]

        # --------------------------------------------------
        # 6. Generate recommendation
        # --------------------------------------------------

        if failed_checks:

            recommendation = (
                "Do not proceed with automatic qualification. "
                "One or more mandatory compliance requirements "
                "have failed and require resolution or "
                "manual review."
            )

        elif review_checks or pending_checks:

            recommendation = (
                "Manual review is recommended before "
                "proceeding. Some compliance requirements "
                "could not be conclusively verified."
            )

        elif assessment.status == "COMPLIANT":

            recommendation = (
                "The bid satisfies the evaluated compliance "
                "requirements. The Procurement Officer may "
                "proceed with the next stage of evaluation."
            )

        else:

            recommendation = (
                "Further compliance review is recommended "
                "before making a procurement decision."
            )

        # --------------------------------------------------
        # 7. Persist recommendation
        # --------------------------------------------------

        assessment.recommendation = recommendation

        db.commit()
        db.refresh(assessment)

        return assessment


recommendation_service = RecommendationService()