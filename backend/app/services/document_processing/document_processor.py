"""
Document processing pipeline for BidSure AI.

This service orchestrates:
1. Document loading / text extraction
2. Document classification
3. Document field extraction
4. Standard module-contract output

It does not contain extraction, classification, or field-extraction
rules itself.

Those responsibilities remain in:
- DocumentLoader
- DocumentClassifier
- FieldExtractor
"""

from .classifier import DocumentClassifier
from .document_loader import DocumentLoader
from .field_extractor import FieldExtractor


class DocumentProcessor:
    """
    Orchestrates document extraction, classification,
    structured field extraction, and contract formatting.
    """

    def __init__(
        self,
        document_loader: DocumentLoader | None = None,
        classifier: DocumentClassifier | None = None,
        field_extractor: FieldExtractor | None = None,
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

    def _build_contract_result(
        self,
        status: str,
        document_type: str,
        extracted_data: dict,
        confidence: float,
        errors: list[str],
    ) -> dict:
        """
        Build the standard Document Intelligence module output.

        This is the interface that other BidSure modules can consume.
        """

        return {
            "success": status == "SUCCESS",
            "processing_status": status,
            "document_type": document_type,
            "extracted_data": extracted_data,
            "confidence": confidence,
            "errors": errors,
        }

    def process(self, file_path: str) -> dict:
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
            contract result

        Args:
            file_path: Path to the document.

        Returns:
            Dictionary containing detailed internal results and
            the standard module-contract result.
        """

        # ---------------------------------------------------------
        # 1. Extract document text
        # ---------------------------------------------------------

        extraction_result = (
            self.document_loader.load_and_extract(
                file_path
            )
        )

        # ---------------------------------------------------------
        # 2. Check extraction result
        # ---------------------------------------------------------

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

            contract_result = self._build_contract_result(
                status="FAIL",
                document_type=classification_result.get(
                    "document_type",
                    "UNKNOWN",
                ),
                extracted_data={},
                confidence=classification_result.get(
                    "confidence",
                    0.0,
                ),
                errors=[
                    "Document text extraction failed"
                ],
            )

            return {
                "status": "FAIL",
                "file_path": extraction_result.get(
                    "file_path",
                    file_path,
                ),
                "extraction": extraction_result,
                "classification": classification_result,
                "extracted_data": {},
                "contract": contract_result,
            }

        # ---------------------------------------------------------
        # 3. Classify extracted text
        # ---------------------------------------------------------

        classification_result = (
            self.classifier.classify(raw_text)
        )

        # ---------------------------------------------------------
        # 4. Extract structured fields
        # ---------------------------------------------------------

        extracted_data = {}

        document_type = classification_result.get(
            "document_type"
        )

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

        # Unknown document types intentionally produce
        # empty extracted_data.

        # ---------------------------------------------------------
        # 5. Build standard module-contract result
        # ---------------------------------------------------------

        classification_confidence = classification_result.get(
            "confidence",
            0.0,
        )

        contract_result = self._build_contract_result(
            status="SUCCESS",
            document_type=document_type or "UNKNOWN",
            extracted_data=extracted_data,
            confidence=classification_confidence,
            errors=[],
        )

        # ---------------------------------------------------------
        # 6. Return complete result
        # ---------------------------------------------------------

        return {
            "status": "SUCCESS",
            "file_path": extraction_result["file_path"],
            "extraction": extraction_result,
            "classification": classification_result,
            "extracted_data": extracted_data,
            "contract": contract_result,
        }