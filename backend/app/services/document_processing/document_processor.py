"""
Document processing pipeline for BidSure AI.

Team 1 responsibilities:

1. Document loading / OCR
2. Document classification
3. Structured field extraction
4. Local extraction-quality validation
5. Standard module-contract output

IMPORTANT:

The verifier performs LOCAL extraction validation only.

It does NOT:
- verify GST registration with the government
- verify PAN with the government
- verify Udyam with the government
- prove document authenticity

External/government verification belongs to Team 2.
"""

from .classifier import DocumentClassifier
from .document_loader import DocumentLoader
from .field_extractor import FieldExtractor
from .verifier import DocumentVerifier


class DocumentProcessor:
    """
    Orchestrates document extraction, classification,
    structured field extraction, local extraction-quality
    validation, and contract formatting.
    """

    def __init__(
        self,
        document_loader: DocumentLoader | None = None,
        classifier: DocumentClassifier | None = None,
        field_extractor: FieldExtractor | None = None,
        verifier: DocumentVerifier | None = None,
    ):
        """
        Initialize the document processing pipeline.

        Optional dependencies can be injected for testing.
        """

        self.document_loader = (
            document_loader
            if document_loader is not None
            else DocumentLoader()
        )

        self.classifier = (
            classifier
            if classifier is not None
            else DocumentClassifier()
        )

        self.field_extractor = (
            field_extractor
            if field_extractor is not None
            else FieldExtractor()
        )

        self.verifier = (
            verifier
            if verifier is not None
            else DocumentVerifier()
        )

    # =========================================================
    # EXTRACTION QUALITY
    # =========================================================

    @staticmethod
    def _build_extraction_quality(
        verification: dict,
        extracted_data: dict,
        document_type: str = "UNKNOWN",
    ) -> dict:
        """
        Build Team 1 extraction-quality information.

        Quality is based on:
            1. Fields that were successfully verified.
            2. Fields that require review.
            3. Important fields that are expected for the
               detected document type but were not extracted.

        This is LOCAL extraction quality only.

        It does NOT mean:
            - government verification
            - document authenticity
            - portal verification
        """

        if not isinstance(verification, dict):
            verification = {}

        if not isinstance(extracted_data, dict):
            extracted_data = {}

        verified_fields = verification.get(
            "verified_fields",
            [],
        )

        fields_requiring_review = verification.get(
            "fields_requiring_review",
            [],
        )

        errors = verification.get(
            "errors",
            [],
        )

        if not isinstance(verified_fields, list):
            verified_fields = []

        if not isinstance(fields_requiring_review, list):
            fields_requiring_review = []

        if not isinstance(errors, list):
            errors = []

        # -----------------------------------------------------
        # Remove duplicates while preserving order.
        # -----------------------------------------------------

        verified_fields = list(
            dict.fromkeys(
                verified_fields
            )
        )

        fields_requiring_review = list(
            dict.fromkeys(
                fields_requiring_review
            )
        )

        # -----------------------------------------------------
        # Never allow the same field to be both verified and
        # requiring review.
        # -----------------------------------------------------

        verified_set = set(
            verified_fields
        )

        fields_requiring_review = [
            field
            for field in fields_requiring_review
            if field not in verified_set
        ]

        # -----------------------------------------------------
        # Required core fields.
        #
        # These are fields whose absence is important enough
        # to lower extraction quality.
        #
        # Trade name is deliberately NOT required because a GST
        # certificate may legitimately have no trade name.
        # -----------------------------------------------------

        required_fields = {
            "GST_CERTIFICATE": (
                "gstin",
                "legal_name",
                "constitution",
                "registration_date",
                "registration_type",
                "principal_address",
            ),

            "PAN_CARD": (
                "pan",
                "name",
                "father_name",
                "date_of_birth",
            ),

            "UDYAM_CERTIFICATE": (
                "udyam_number",
                "enterprise_name",
                "enterprise_type",
                "social_category",
                "date_of_incorporation",
                "udyam_registration_date",
            ),
        }.get(
            document_type,
            (),
        )

        # -----------------------------------------------------
        # Missing expected fields.
        #
        # Do not overwrite fields already verified/reviewed.
        # -----------------------------------------------------

        known_fields = (
            set(verified_fields)
            | set(fields_requiring_review)
        )

        for field in required_fields:

            if field not in known_fields:

                fields_requiring_review.append(
                    field
                )

        # -----------------------------------------------------
        # Calculate quality.
        #
        # IMPORTANT:
        #
        # Missing required fields are now included in the
        # denominator.
        #
        # Example:
        #
        # 2 verified + 4 missing
        # = 2 / 6
        # = 0.33
        # -----------------------------------------------------

        validated_field_count = (
            len(verified_fields)
            + len(fields_requiring_review)
        )

        if validated_field_count == 0:

            quality_score = 0.0

        else:

            quality_score = (
                len(verified_fields)
                / validated_field_count
            )

        quality_score = max(
            0.0,
            min(
                1.0,
                quality_score,
            ),
        )

        # -----------------------------------------------------
        # Determine quality status.
        # -----------------------------------------------------

        if errors:

            status = "REVIEW_REQUIRED"

        elif fields_requiring_review:

            status = "REVIEW_REQUIRED"

        elif verified_fields:

            status = "PASS"

        else:

            status = "REVIEW_REQUIRED"

        return {
            "status": status,
            "quality_score": round(
                quality_score,
                2,
            ),
            "verified_fields": verified_fields,
            "fields_requiring_review": (
                fields_requiring_review
            ),
            "errors": errors,
        }

    # =========================================================
    # CONTRACT BUILDER
    # =========================================================

    def _build_contract_result(
        self,
        status: str,
        document_type: str,
        extracted_data: dict,
        confidence: float,
        errors: list[str],
        verification: dict | None = None,
        extraction_quality: dict | None = None,
    ) -> dict:
        """
        Build the standard Document Intelligence contract.

        Existing fields are preserved for compatibility.

        extraction_quality explicitly represents Team 1
        extraction validation.
        """

        contract = {
            "success": status == "SUCCESS",
            "processing_status": status,
            "document_type": document_type,
            "extracted_data": extracted_data,
            "confidence": confidence,
            "errors": errors,
        }

        # -----------------------------------------------------
        # Keep the existing verification field for backward
        # compatibility.
        #
        # This is LOCAL validation only.
        # -----------------------------------------------------

        if verification is not None:

            contract["verification"] = verification

        # -----------------------------------------------------
        # Explicit Team 1 extraction-quality result.
        # -----------------------------------------------------

        if extraction_quality is not None:

            contract["extraction_quality"] = (
                extraction_quality
            )

        return contract

    # =========================================================
    # MAIN PIPELINE
    # =========================================================

    def process(
        self,
        file_path: str,
    ) -> dict:
        """
        Process a document from file path to structured result.

        Pipeline:

            file
              ↓
            DocumentLoader
              ↓
            raw_text
              ↓
            DocumentClassifier
              ↓
            FieldExtractor
              ↓
            DocumentVerifier
              ↓
            Extraction Quality
              ↓
            Contract
        """

        # =====================================================
        # 1. DOCUMENT LOADING / OCR
        # =====================================================

        extraction_result = (
            self.document_loader.load_and_extract(
                file_path
            )
        )

        # =====================================================
        # 2. CHECK EXTRACTION RESULT
        # =====================================================

        raw_text = extraction_result.get(
            "raw_text",
            "",
        )

        if (
            extraction_result.get("status") != "SUCCESS"
            or not raw_text.strip()
        ):

            classification_result = (
                self.classifier.classify("")
            )

            verification_result = (
                self.verifier.verify(
                    "UNKNOWN",
                    {},
                )
            )

            extraction_quality = (
                self._build_extraction_quality(
                    verification_result,
                    {},
                    classification_result.get(
                        "document_type",
                        "UNKNOWN",
                    ),
                )
            )

            contract_result = (
                self._build_contract_result(
                    status="FAIL",
                    document_type=(
                        classification_result.get(
                            "document_type",
                            "UNKNOWN",
                        )
                    ),
                    extracted_data={},
                    confidence=(
                        classification_result.get(
                            "confidence",
                            0.0,
                        )
                    ),
                    errors=[
                        "Document text extraction failed"
                    ],
                    verification=verification_result,
                    extraction_quality=(
                        extraction_quality
                    ),
                )
            )

            return {
                "status": "FAIL",
                "file_path": (
                    extraction_result.get(
                        "file_path",
                        file_path,
                    )
                ),
                "extraction": extraction_result,
                "classification": classification_result,
                "extracted_data": {},
                "verification": verification_result,
                "extraction_quality": (
                    extraction_quality
                ),
                "contract": contract_result,
            }

        # =====================================================
        # 3. CLASSIFICATION
        # =====================================================

        classification_result = (
            self.classifier.classify(
                raw_text
            )
        )

        document_type = (
            classification_result.get(
                "document_type",
                "UNKNOWN",
            )
        )

        # =====================================================
        # 4. FIELD EXTRACTION
        # =====================================================

        extracted_data = {}

        if document_type == "GST_CERTIFICATE":

            extracted_data = (
                self.field_extractor.extract_gst_fields(
                    raw_text
                )
            )

        elif document_type == "PAN_CARD":

            extracted_data = (
                self.field_extractor.extract_pan_fields(
                    raw_text
                )
            )

        elif document_type == "UDYAM_CERTIFICATE":

            extracted_data = (
                self.field_extractor.extract_udyam_fields(
                    raw_text
                )
            )

        # =====================================================
        # 5. LOCAL EXTRACTION VALIDATION
        # =====================================================

        verification_result = (
            self.verifier.verify(
                document_type,
                extracted_data,
            )
        )

        # =====================================================
        # 6. EXTRACTION QUALITY
        # =====================================================

        extraction_quality = (
            self._build_extraction_quality(
                verification_result,
                extracted_data,
                document_type,
            )
        )

        # =====================================================
        # 7. CLASSIFICATION CONFIDENCE
        # =====================================================

        classification_confidence = (
            classification_result.get(
                "confidence",
                0.0,
            )
        )

        # =====================================================
        # 8. BUILD CONTRACT
        # =====================================================

        contract_result = (
            self._build_contract_result(
                status="SUCCESS",
                document_type=(
                    document_type
                    or "UNKNOWN"
                ),
                extracted_data=extracted_data,
                confidence=(
                    classification_confidence
                ),
                errors=[],
                verification=verification_result,
                extraction_quality=(
                    extraction_quality
                ),
            )
        )

        # =====================================================
        # 9. RETURN COMPLETE RESULT
        # =====================================================

        return {
            "status": "SUCCESS",
            "file_path": extraction_result[
                "file_path"
            ],
            "extraction": extraction_result,
            "classification": classification_result,
            "extracted_data": extracted_data,
            "verification": verification_result,
            "extraction_quality": (
                extraction_quality
            ),
            "contract": contract_result,
        }