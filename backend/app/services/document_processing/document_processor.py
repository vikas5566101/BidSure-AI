"""
Document processing pipeline for BidSure AI.

This service orchestrates:
1. Document loading / text extraction
2. Document classification
3. Document field extraction

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
    and structured field extraction.
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
            result

        Args:
            file_path: Path to the document.

        Returns:
            Dictionary containing extraction,
            classification, and extracted fields.
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

        # If extraction failed or produced no text,
        # classification and field extraction cannot be performed.
        if (
            extraction_result.get("status") != "SUCCESS"
            or not raw_text.strip()
        ):
            classification_result = (
                self.classifier.classify("")
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

        # ---------------------------------------------------------
        # 5. Return combined pipeline result
        # ---------------------------------------------------------

        return {
            "status": "SUCCESS",
            "file_path": extraction_result["file_path"],
            "extraction": extraction_result,
            "classification": classification_result,
            "extracted_data": extracted_data,
        }