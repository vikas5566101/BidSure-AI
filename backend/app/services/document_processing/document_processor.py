"""
Document processing pipeline for BidSure AI.

This service orchestrates:
1. Document loading / text extraction
2. Document classification

It does not contain extraction or classification rules itself.
Those responsibilities remain in DocumentLoader and
DocumentClassifier.
"""

from .classifier import DocumentClassifier
from .document_loader import DocumentLoader


class DocumentProcessor:
    """
    Orchestrates document extraction and classification.
    """

    def __init__(
        self,
        document_loader: DocumentLoader | None = None,
        classifier: DocumentClassifier | None = None,
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

    def process(self, file_path: str) -> dict:
        """
        Process a document from file path to classification.

        Pipeline:

            file
              ↓
            DocumentLoader
              ↓
            raw_text
              ↓
            DocumentClassifier
              ↓
            classification

        Args:
            file_path: Path to the document.

        Returns:
            Dictionary containing extraction and classification
            results.
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
        # classification cannot be performed.
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
            }

        # ---------------------------------------------------------
        # 3. Classify extracted text
        # ---------------------------------------------------------

        classification_result = (
            self.classifier.classify(raw_text)
        )

        # ---------------------------------------------------------
        # 4. Return combined pipeline result
        # ---------------------------------------------------------

        return {
            "status": "SUCCESS",
            "file_path": extraction_result["file_path"],
            "extraction": extraction_result,
            "classification": classification_result,
        }