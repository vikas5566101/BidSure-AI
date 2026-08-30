from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.compliance_check import ComplianceCheck
from app.schemas.compliance_check import ComplianceCheckCreate
from app.repositories.compliance_check_repository import (
    compliance_check_repository,
)
from app.repositories.tender_requirement_repository import (
    tender_requirement_repository,
)
from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.services.evaluators.registry import (
    evaluator_registry,
)


class ComplianceService:
    """
    Coordinates tender requirement evaluation.

    The service retrieves the tender requirement, selects the
    appropriate evaluator, evaluates the available evidence,
    and persists the resulting ComplianceCheck.
    """

    def evaluate_requirement(
        self,
        db: Session,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceCheck:

        # --------------------------------------------------
        # 1. Retrieve tender requirement
        # --------------------------------------------------

        requirement = tender_requirement_repository.get_by_id(
            db,
            request.tender_requirement_id,
        )

        if requirement is None:
            raise ValueError(
                "Tender requirement not found: "
                f"{request.tender_requirement_id}"
            )

        # --------------------------------------------------
        # 2. Find evaluator
        # --------------------------------------------------

        evaluator = evaluator_registry.get(
            requirement.requirement_type
        )

        # --------------------------------------------------
        # 3. Handle unsupported requirement type
        # --------------------------------------------------

        if evaluator is None:

            result = ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "No automated evaluator is available "
                    "for requirement type: "
                    f"{requirement.requirement_type}"
                ),
                evidence={
                    "requirement_type": (
                        requirement.requirement_type
                    ),
                    "requirement_name": (
                        requirement.requirement_name
                    ),
                },
            )

        # --------------------------------------------------
        # 4. Evaluate using registered evaluator
        # --------------------------------------------------

        else:

            evaluation_request = ComplianceEvaluationRequest(
                bid_submission_id=(
                    request.bid_submission_id
                ),
                tender_requirement_id=(
                    request.tender_requirement_id
                ),
                requirement_type=(
                    requirement.requirement_type
                ),
                requirement_name=(
                    requirement.requirement_name
                ),
                description=requirement.description,
                is_required=requirement.is_required,
                validation_config=(
                    requirement.validation_config
                ),
                extracted_data=(
                    request.extracted_data
                ),
                verification_data=(
                    request.verification_data
                ),
            )

            result = evaluator.evaluate(
                evaluation_request
            )

        # --------------------------------------------------
        # 5. Convert evaluation result into persistence schema
        # --------------------------------------------------

        compliance_check_data = ComplianceCheckCreate(
            bid_submission_id=request.bid_submission_id,
            tender_requirement_id=request.tender_requirement_id,
            status=result.status,
            reason=result.reason,
            evidence=result.evidence,
            checked_by="COMPLIANCE_ENGINE",
            checked_at=datetime.now(timezone.utc),
        )

        # --------------------------------------------------
        # 6. Persist ComplianceCheck
        # --------------------------------------------------

        return compliance_check_repository.create(
            db,
            compliance_check_data,
        )


compliance_service = ComplianceService()