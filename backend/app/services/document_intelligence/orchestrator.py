from pathlib import Path

from .classifier import DocumentClassifier
from .field_extractor import DocumentFieldExtractor
from .ocr_extractor import OCRExtractor
from .pdf_extractor import PDFTextExtractor
from .schemas import (
    DocumentIntelligenceResult,
    TextExtractionMethod,
)


class DocumentIntelligenceOrchestrator:
    """
    Coordinates the complete document intelligence pipeline.

    Responsibilities:
    - extract native PDF text when available
    - fall back to OCR for scanned PDFs
    - classify the document
    - extract structured fields

    This class does NOT:
    - verify government records
    - evaluate compliance
    - calculate compliance scores
    - make qualification decisions
    """

    def __init__(
        self,
        pdf_extractor: PDFTextExtractor | None = None,
        ocr_extractor: OCRExtractor | None = None,
        classifier: DocumentClassifier | None = None,
        field_extractor: DocumentFieldExtractor | None = None,
    ) -> None:
        self.pdf_extractor = pdf_extractor or PDFTextExtractor()
        self.ocr_extractor = ocr_extractor or OCRExtractor()
        self.classifier = classifier or DocumentClassifier()
        self.field_extractor = field_extractor or DocumentFieldExtractor()

    def process(
        self,
        file_path: str | Path,
    ) -> DocumentIntelligenceResult:
        """
        Process a PDF through the complete Document Intelligence pipeline.
        """

        path = Path(file_path)

        native_result = self.pdf_extractor.extract(path)

        if self._has_meaningful_text(native_result):
            extraction_result = native_result
            extraction_method = TextExtractionMethod.NATIVE_PDF
        else:
            extraction_result = self.ocr_extractor.extract(path)
            extraction_method = TextExtractionMethod.OCR

        extracted_text = self._combine_page_text(
            extraction_result.pages
        )

        classification = self.classifier.classify(
            extracted_text
        )

        structured = self.field_extractor.extract(
            extracted_text,
            classification.document_type,
        )

        return DocumentIntelligenceResult(
            document_type=classification.document_type,
            classification_confidence=classification.confidence,
            extraction_method=extraction_method,
            extracted_text=extracted_text,
            total_pages=extraction_result.total_pages,
            total_characters=extraction_result.total_characters,
            fields=structured.fields,
            extraction_confidence=structured.confidence,
        )

    @staticmethod
    def _has_meaningful_text(extraction_result) -> bool:
        """
        Determine whether native PDF extraction produced useful text.

        A PDF can technically contain whitespace or a tiny amount of
        metadata while still being effectively a scanned document.
        """

        text = "\n".join(
            page.text for page in extraction_result.pages
        )

        return bool(text.strip())

    @staticmethod
    def _combine_page_text(pages) -> str:
        """
        Combine page text while preserving page boundaries.
        """

        return "\n\n".join(
            page.text.strip()
            for page in pages
            if page.text.strip()
        )


document_intelligence = DocumentIntelligenceOrchestrator()