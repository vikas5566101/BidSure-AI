from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.compliance_assessment import ComplianceAssessment
from app.repositories.compliance_assessment_repository import (
    compliance_assessment_repository,
)
from app.repositories.compliance_check_repository import (
    compliance_check_repository,
)
from app.schemas.compliance_assessment import (
    ComplianceAssessmentCreate,
)


class ComplianceAssessmentService:
    """
    Generates an overall compliance assessment for a bid submission.

    The service summarizes individual ComplianceCheck records and
    calculates a deterministic compliance score, risk level, and
    overall status.

    AI-generated recommendations will be added in a later phase.
    """

    def assess_submission(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> ComplianceAssessment:

        # --------------------------------------------------
        # 1. Retrieve compliance checks
        # --------------------------------------------------

        checks = (
            compliance_check_repository.get_by_submission(
                db,
                bid_submission_id,
            )
        )

        # --------------------------------------------------
        # 2. Handle no compliance checks
        # --------------------------------------------------

        if not checks:

            assessment_data = ComplianceAssessmentCreate(
                bid_submission_id=bid_submission_id,
                score=None,
                risk_level=None,
                recommendation=None,
                status="PENDING",
                summary=(
                    "No compliance checks are available "
                    "for this bid submission."
                ),
                assessment_metadata={
                    "total_checks": 0,
                    "passed": 0,
                    "failed": 0,
                    "review": 0,
                    "pending": 0,
                },
                assessed_at=None,
            )

            return compliance_assessment_repository.create(
                db,
                assessment_data,
            )

        # --------------------------------------------------
        # 3. Count compliance results
        # --------------------------------------------------

        total_checks = len(checks)

        passed = sum(
            1
            for check in checks
            if check.status.upper() == "PASS"
        )

        failed = sum(
            1
            for check in checks
            if check.status.upper() == "FAIL"
        )

        review = sum(
            1
            for check in checks
            if check.status.upper() == "REVIEW"
        )

        pending = sum(
            1
            for check in checks
            if check.status.upper() == "PENDING"
        )

        # --------------------------------------------------
        # 4. Calculate deterministic compliance score
        # --------------------------------------------------

        score = round(
            (passed / total_checks) * 100,
            2,
        )

        # --------------------------------------------------
        # 5. Determine risk level
        # --------------------------------------------------

        if failed > 0:
            risk_level = "HIGH"

        elif review > 0 or pending > 0:
            risk_level = "MEDIUM"

        elif score >= 80:
            risk_level = "LOW"

        else:
            risk_level = "MEDIUM"

        # --------------------------------------------------
        # 6. Determine overall status
        # --------------------------------------------------

        if failed > 0:
            status = "NON_COMPLIANT"

        elif review > 0 or pending > 0:
            status = "REVIEW"

        elif passed == total_checks:
            status = "COMPLIANT"

        else:
            status = "REVIEW"

        # --------------------------------------------------
        # 7. Generate deterministic summary
        # --------------------------------------------------

        summary = (
            f"Compliance assessment completed for "
            f"{total_checks} requirement(s): "
            f"{passed} passed, "
            f"{failed} failed, "
            f"{review} under review, "
            f"{pending} pending."
        )

        # --------------------------------------------------
        # 8. Prepare assessment metadata
        # --------------------------------------------------

        assessment_metadata = {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "review": review,
            "pending": pending,
        }

        # --------------------------------------------------
        # 9. Persist assessment
        # --------------------------------------------------

        assessment_data = ComplianceAssessmentCreate(
            bid_submission_id=bid_submission_id,
            score=score,
            risk_level=risk_level,
            recommendation=None,
            status=status,
            summary=summary,
            assessment_metadata=assessment_metadata,
            assessed_at=datetime.now(timezone.utc),
        )

        return compliance_assessment_repository.create(
            db,
            assessment_data,
        )


compliance_assessment_service = ComplianceAssessmentService()