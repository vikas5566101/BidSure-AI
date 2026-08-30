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