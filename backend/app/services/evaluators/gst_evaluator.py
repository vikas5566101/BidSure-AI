from app.schemas.compliance_evaluation import (
    ComplianceEvaluationRequest,
    ComplianceEvaluationResult,
)
from app.services.evaluators.base import (
    RequirementEvaluator,
)


class GSTEvaluator(RequirementEvaluator):
    """
    Evaluates GST-related tender requirements using
    structured document and verification evidence.

    This evaluator does not communicate directly with
    external government portals. Government verification
    data is supplied through verification_data.
    """

    @property
    def requirement_type(self) -> str:
        return "GST"

    def evaluate(
        self,
        request: ComplianceEvaluationRequest,
    ) -> ComplianceEvaluationResult:

        extracted_data = request.extracted_data or {}
        verification_data = request.verification_data or {}

        # --------------------------------------------------
        # 1. Check whether any GST evidence exists
        # --------------------------------------------------

        if not extracted_data and not verification_data:
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason="No GST evidence is available.",
                evidence={},
            )

        # --------------------------------------------------
        # 2. Extract GSTIN from available evidence
        # --------------------------------------------------

        document_gstin = extracted_data.get("gstin")
        verified_gstin = verification_data.get("gstin")

        # --------------------------------------------------
        # 3. Check GSTIN consistency
        # --------------------------------------------------

        if (
            document_gstin
            and verified_gstin
            and document_gstin != verified_gstin
        ):
            return ComplianceEvaluationResult(
                status="REVIEW",
                reason=(
                    "GSTIN mismatch between document "
                    "evidence and verification data."
                ),
                evidence={
                    "document_gstin": document_gstin,
                    "verified_gstin": verified_gstin,
                },
            )

        gstin = verified_gstin or document_gstin

        # --------------------------------------------------
        # 4. Check verification status
        # --------------------------------------------------

        verification_status = verification_data.get(
            "status"
        )

        if verification_status == "INVALID":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason="GST registration could not be verified.",
                evidence={
                    "gstin": gstin,
                    "verification_status": verification_status,
                },
            )

        # --------------------------------------------------
        # 5. Check return filing status
        # --------------------------------------------------

        return_filing_status = verification_data.get(
            "return_filing_status"
        )

        if return_filing_status == "NON_COMPLIANT":
            return ComplianceEvaluationResult(
                status="FAIL",
                reason="GST return filing is non-compliant.",
                evidence={
                    "gstin": gstin,
                    "return_filing_status": (
                        return_filing_status
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
                    "GST registration verification "
                    "evidence is incomplete."
                ),
                evidence={
                    "gstin": gstin,
                    "verification_status": (
                        verification_status
                    ),
                    "return_filing_status": (
                        return_filing_status
                    ),
                },
            )

        # --------------------------------------------------
        # 7. GST requirement satisfied
        # --------------------------------------------------

        if (
            return_filing_status
            in (None, "COMPLIANT")
        ):
            return ComplianceEvaluationResult(
                status="PASS",
                reason=(
                    "GST registration is verified and "
                    "no non-compliant return filing "
                    "status was identified."
                ),
                evidence={
                    "gstin": gstin,
                    "verification_status": (
                        verification_status
                    ),
                    "return_filing_status": (
                        return_filing_status
                    ),
                },
            )

        # --------------------------------------------------
        # 8. Unknown filing status
        # --------------------------------------------------

        return ComplianceEvaluationResult(
            status="REVIEW",
            reason="GST return filing status requires review.",
            evidence={
                "gstin": gstin,
                "verification_status": verification_status,
                "return_filing_status": return_filing_status,
            },
        )