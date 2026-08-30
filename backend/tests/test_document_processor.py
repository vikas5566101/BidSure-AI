from backend.app.services.document_processing.document_processor import (
    DocumentProcessor,
)


def test_process_native_pdf():
    """
    Verify that the processor correctly handles a native PDF
    and passes the extracted text to the classifier.
    """

    processor = DocumentProcessor()

    result = processor.process(
        "mock_data/documents/test_gst_certificate.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert (
        result["extraction"]["extraction_method"]
        == "native_pdf"
    )

    assert (
        result["classification"]["document_type"]
        == "GST_CERTIFICATE"
    )

    assert (
        result["classification"]["ambiguity"]
        is False
    )

    assert (
        result["classification"]["needs_review"]
        is False
    )


def test_process_scanned_pdf():
    """
    Verify that the processor correctly handles a scanned PDF,
    including OCR extraction followed by classification.
    """

    processor = DocumentProcessor()

    result = processor.process(
        "mock_data/documents/scanned_gst_certificate.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert (
        result["extraction"]["extraction_method"]
        == "ocr_pdf"
    )

    assert (
        result["classification"]["document_type"]
        == "GST_CERTIFICATE"
    )

    assert (
        result["classification"]["ambiguity"]
        is False
    )

    assert (
        result["classification"]["needs_review"]
        is False
    )


def test_process_empty_extraction():
    """
    Verify that an extraction result with no text is handled
    safely and results in a failed processing status.
    """

    class EmptyDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "FAIL",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": "",
            }

    processor = DocumentProcessor(
        document_loader=EmptyDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/empty.pdf"
    )

    assert result["status"] == "FAIL"

    assert result["extraction"]["status"] == "FAIL"

    assert (
        result["classification"]["document_type"]
        == "UNKNOWN"
    )

    assert (
        result["classification"]["needs_review"]
        is True
    )

    assert result["extracted_data"] == {}


def test_process_with_empty_raw_text():
    """
    Verify that a successful extraction response containing
    empty text is still treated as a failed processing result.
    """

    class EmptyTextDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": "",
            }

    processor = DocumentProcessor(
        document_loader=EmptyTextDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/empty.pdf"
    )

    assert result["status"] == "FAIL"

    assert (
        result["classification"]["document_type"]
        == "UNKNOWN"
    )

    assert (
        result["classification"]["needs_review"]
        is True
    )

    assert result["extracted_data"] == {}


def test_processor_uses_injected_classifier():
    """
    Verify dependency injection.

    The processor should use the supplied classifier instead
    of creating its own classifier internally.
    """

    class MockClassifier:
        def classify(self, text):
            assert "GSTIN" in text

            return {
                "document_type": "MOCK_DOCUMENT",
                "confidence": 1.0,
                "needs_review": False,
            }

    processor = DocumentProcessor(
        classifier=MockClassifier()
    )

    result = processor.process(
        "mock_data/documents/test_gst_certificate.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert (
        result["classification"]["document_type"]
        == "MOCK_DOCUMENT"
    )

    assert (
        result["classification"]["confidence"]
        == 1.0
    )

    assert (
        result["classification"]["needs_review"]
        is False
    )

    assert result["extracted_data"] == {}


def test_process_native_pdf_extracts_gst_fields():
    """
    Verify that the complete pipeline extracts structured GST
    fields from a native PDF.
    """

    processor = DocumentProcessor()

    result = processor.process(
        "mock_data/documents/test_gst_certificate.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert result["classification"]["document_type"] == (
        "GST_CERTIFICATE"
    )

    assert result["extracted_data"] == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_status": "ACTIVE",
    }


def test_process_scanned_pdf_extracts_gst_fields():
    """
    Verify that the complete pipeline extracts structured GST
    fields from an OCR-based scanned PDF.
    """

    processor = DocumentProcessor()

    result = processor.process(
        "mock_data/documents/scanned_gst_certificate.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert (
        result["extraction"]["extraction_method"]
        == "ocr_pdf"
    )

    assert result["classification"]["document_type"] == (
        "GST_CERTIFICATE"
    )

    assert result["extracted_data"] == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_status": "ACTIVE",
    }


def test_unknown_document_has_empty_extracted_data():
    """
    Verify that an unknown document does not produce
    structured fields.
    """

    class UnknownDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": (
                    "This is an unrelated document with "
                    "no known indicators."
                ),
            }

    processor = DocumentProcessor(
        document_loader=UnknownDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/unknown.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert (
        result["classification"]["document_type"]
        == "UNKNOWN"
    )

    assert result["extracted_data"] == {}


def test_document_processor_returns_standard_contract():
    """
    Verify that DocumentProcessor exposes the standard
    Document Intelligence module contract.
    """

    processor = DocumentProcessor()

    result = processor.process(
        "mock_data/documents/test_gst_certificate.pdf"
    )

    contract = result["contract"]

    assert contract["success"] is True
    assert contract["processing_status"] == "SUCCESS"

    assert contract["document_type"] == "GST_CERTIFICATE"

    assert contract["extracted_data"] == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_status": "ACTIVE",
    }

    assert contract["confidence"] == 0.7

    assert contract["errors"] == []


def test_scanned_pdf_returns_standard_contract():
    """
    Verify that OCR-based processing also produces the
    standard module contract.
    """

    processor = DocumentProcessor()

    result = processor.process(
        "mock_data/documents/scanned_gst_certificate.pdf"
    )

    contract = result["contract"]

    assert contract["success"] is True
    assert contract["processing_status"] == "SUCCESS"
    assert contract["document_type"] == "GST_CERTIFICATE"

    assert contract["extracted_data"]["gstin"] == (
        "27ABCDE1234F1Z5"
    )

    assert contract["confidence"] == 0.7
    assert contract["errors"] == []


def test_failed_extraction_returns_failed_contract():
    """
    Verify that failed document extraction produces a
    failed standard contract.
    """

    class EmptyDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "FAIL",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": "",
            }

    processor = DocumentProcessor(
        document_loader=EmptyDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/empty.pdf"
    )

    contract = result["contract"]

    assert contract["success"] is False
    assert contract["processing_status"] == "FAIL"
    assert contract["document_type"] == "UNKNOWN"
    assert contract["extracted_data"] == {}
    assert contract["confidence"] == 0.0
    assert contract["errors"] == [
        "Document text extraction failed"
    ]