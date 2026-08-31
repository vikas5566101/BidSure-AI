from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.services.evaluators.base import (
    RequirementEvaluator,
)


class UdyamEvaluator(RequirementEvaluator):
    """
    Evaluates Udyam/MSME-related tender requirements
    using structured document and verification evidence.

    This evaluator does not communicate directly with
    the Udyam portal. Government verification data is
    supplied through verification_data.
    """

    @property
    def requirement_type(self) -> str:
        return "UDYAM"

    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:

        extracted_data = request.extracted_data or {}
        verification_data = request.verification_data or {}

        # --------------------------------------------------
        # 1. Check whether any Udyam evidence exists
        # --------------------------------------------------

        if not extracted_data and not verification_data:
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason="No Udyam/MSME evidence is available.",
                evidence={},
            )

        # --------------------------------------------------
        # 2. Extract Udyam number
        # --------------------------------------------------

        document_udyam = extracted_data.get(
            "udyam_number"
        )

        verified_udyam = verification_data.get(
            "udyam_number"
        )

        # --------------------------------------------------
        # 3. Check Udyam number consistency
        # --------------------------------------------------

        if (
            document_udyam
            and verified_udyam
            and document_udyam != verified_udyam
        ):
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "Udyam number mismatch between "
                    "document evidence and verification data."
                ),
                evidence={
                    "document_udyam_number": document_udyam,
                    "verified_udyam_number": verified_udyam,
                },
            )

        udyam_number = (
            verified_udyam or document_udyam
        )

        # --------------------------------------------------
        # 4. Check verification status
        # --------------------------------------------------

        verification_status = verification_data.get(
            "status"
        )

        if verification_status == "INVALID":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=(
                    "Udyam/MSME registration "
                    "could not be verified."
                ),
                evidence={
                    "udyam_number": udyam_number,
                    "verification_status": (
                        verification_status
                    ),
                },
            )

        # --------------------------------------------------
        # 5. Check enterprise status
        # --------------------------------------------------

        enterprise_status = verification_data.get(
            "enterprise_status"
        )

        if enterprise_status == "INACTIVE":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason=(
                    "Udyam/MSME enterprise is not active."
                ),
                evidence={
                    "udyam_number": udyam_number,
                    "enterprise_status": (
                        enterprise_status
                    ),
                },
            )

        # --------------------------------------------------
        # 6. Insufficient verification evidence
        # --------------------------------------------------

        if verification_status != "VERIFIED":
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "Udyam/MSME verification evidence "
                    "is incomplete."
                ),
                evidence={
                    "udyam_number": udyam_number,
                    "verification_status": (
                        verification_status
                    ),
                    "enterprise_status": (
                        enterprise_status
                    ),
                },
            )

        # --------------------------------------------------
        # 7. Udyam requirement satisfied
        # --------------------------------------------------

        if enterprise_status in (
            None,
            "ACTIVE",
        ):
            return ComplianceEvaluationResult(
                status="PASS",
                reason=(
                    "Udyam/MSME registration is verified "
                    "and the enterprise is active."
                ),
                evidence={
                    "udyam_number": udyam_number,
                    "verification_status": (
                        verification_status
                    ),
                    "enterprise_status": (
                        enterprise_status
                    ),
                },
            )

        # --------------------------------------------------
        # 8. Unknown enterprise status
        # --------------------------------------------------

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason=(
                "Udyam/MSME enterprise status "
                "requires review."
            ),
            evidence={
                "udyam_number": udyam_number,
                "verification_status": verification_status,
                "enterprise_status": enterprise_status,
            },
        )