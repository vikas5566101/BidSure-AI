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
    Verify that the complete pipeline extracts all supported
    structured GST fields from a native PDF.
    """

    processor = DocumentProcessor()

    result = processor.process(
        "mock_data/documents/test_gst_certificate.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert (
        result["classification"]["document_type"]
        == "GST_CERTIFICATE"
    )

    assert result["extracted_data"] == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_date": "15/04/2022",
        "registration_status": "ACTIVE",
        "business_type": "PRIVATE LIMITED COMPANY",
        "principal_address": (
            "123 Industrial Area, Mumbai, Maharashtra"
        ),
    }


def test_process_scanned_pdf_extracts_gst_fields():
    """
    Verify that the complete pipeline extracts structured GST
    fields from an OCR-based scanned PDF.

    The scanned fixture currently does not contain a
    Principal Address field, so only the fields actually
    present in the OCR text are expected.
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

    assert result["extracted_data"] == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_date": "15/04/2022",
        "registration_status": "ACTIVE",
        "business_type": "PRIVATE LIMITED COMPANY",
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

def test_process_pan_document_extracts_fields():
    """
    Verify that the complete pipeline classifies a PAN document
    and extracts its structured fields.
    """

    class PanDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": """
                INCOME TAX DEPARTMENT
                PERMANENT ACCOUNT NUMBER
                PAN: ABCDE1234F
                Name: ABC Industries Pvt Ltd
                Father's Name: Rajesh Kumar
                Date of Birth: 15/04/1985
                """,
            }

    processor = DocumentProcessor(
        document_loader=PanDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/test_pan_card.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert result["classification"]["document_type"] == (
        "PAN_CARD"
    )

    assert result["extracted_data"] == {
        "pan": "ABCDE1234F",
        "name": "ABC Industries Pvt Ltd",
        "father_name": "Rajesh Kumar",
        "date_of_birth": "15/04/1985",
    }


def test_process_udyam_document_extracts_fields():
    """
    Verify that the complete pipeline classifies a Udyam document
    and extracts its structured fields.
    """

    class UdyamDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": """
                UDYAM REGISTRATION CERTIFICATE
                UDYAM REGISTRATION NUMBER: UDYAM-MH-12-0012345
                Name of Enterprise: ABC Industries Pvt Ltd
                Type of Enterprise: Small
                Major Activity: Manufacturing
                Social Category: General
                Date of Incorporation: 15/04/2010
                Udyam Registration Date: 20/06/2021
                Enterprise Address: 123 Industrial Area,
                Mumbai, Maharashtra
                """,
            }

    processor = DocumentProcessor(
        document_loader=UdyamDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/test_udyam_certificate.pdf"
    )

    assert result["status"] == "SUCCESS"

    assert result["classification"]["document_type"] == (
        "UDYAM_CERTIFICATE"
    )

    assert result["extracted_data"] == {
        "udyam_number": "UDYAM-MH-12-0012345",
        "enterprise_name": "ABC Industries Pvt Ltd",
        "enterprise_type": "SMALL",
        "major_activity": "MANUFACTURING",
        "social_category": "GENERAL",
        "date_of_incorporation": "15/04/2010",
        "udyam_registration_date": "20/06/2021",
        "enterprise_address": (
            "123 Industrial Area, Mumbai, Maharashtra"
        ),
    }


def test_process_pan_document_returns_standard_contract():
    """
    Verify that PAN processing produces the standard
    Document Intelligence contract.
    """

    class PanDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": """
                INCOME TAX DEPARTMENT
                PERMANENT ACCOUNT NUMBER
                PAN: ABCDE1234F
                Name: ABC Industries Pvt Ltd
                Father's Name: Rajesh Kumar
                Date of Birth: 15/04/1985
                """,
            }

    processor = DocumentProcessor(
        document_loader=PanDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/test_pan_card.pdf"
    )

    contract = result["contract"]

    assert contract["success"] is True
    assert contract["processing_status"] == "SUCCESS"
    assert contract["document_type"] == "PAN_CARD"

    assert contract["extracted_data"] == {
        "pan": "ABCDE1234F",
        "name": "ABC Industries Pvt Ltd",
        "father_name": "Rajesh Kumar",
        "date_of_birth": "15/04/1985",
    }

    assert contract["errors"] == []


def test_process_udyam_document_returns_standard_contract():
    """
    Verify that Udyam processing produces the standard
    Document Intelligence contract.
    """

    class UdyamDocumentLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "native_pdf",
                "raw_text": """
                UDYAM REGISTRATION CERTIFICATE
                UDYAM REGISTRATION NUMBER: UDYAM-MH-12-0012345
                Name of Enterprise: ABC Industries Pvt Ltd
                Type of Enterprise: Small
                Major Activity: Manufacturing
                Social Category: General
                Date of Incorporation: 15/04/2010
                Udyam Registration Date: 20/06/2021
                Enterprise Address: 123 Industrial Area,
                Mumbai, Maharashtra
                """,
            }

    processor = DocumentProcessor(
        document_loader=UdyamDocumentLoader()
    )

    result = processor.process(
        "mock_data/documents/test_udyam_certificate.pdf"
    )

    contract = result["contract"]

    assert contract["success"] is True
    assert contract["processing_status"] == "SUCCESS"
    assert contract["document_type"] == "UDYAM_CERTIFICATE"

    assert contract["extracted_data"] == {
        "udyam_number": "UDYAM-MH-12-0012345",
        "enterprise_name": "ABC Industries Pvt Ltd",
        "enterprise_type": "SMALL",
        "major_activity": "MANUFACTURING",
        "social_category": "GENERAL",
        "date_of_incorporation": "15/04/2010",
        "udyam_registration_date": "20/06/2021",
        "enterprise_address": (
            "123 Industrial Area, Mumbai, Maharashtra"
        ),
    }

    assert contract["errors"] == []

    
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

    assert (
        contract["processing_status"]
        == "SUCCESS"
    )

    assert (
        contract["document_type"]
        == "GST_CERTIFICATE"
    )

    assert contract["extracted_data"] == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_date": "15/04/2022",
        "registration_status": "ACTIVE",
        "business_type": "PRIVATE LIMITED COMPANY",
        "principal_address": (
            "123 Industrial Area, Mumbai, Maharashtra"
        ),
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

    assert (
        contract["processing_status"]
        == "SUCCESS"
    )

    assert (
        contract["document_type"]
        == "GST_CERTIFICATE"
    )

    assert (
        contract["extracted_data"]["gstin"]
        == "27ABCDE1234F1Z5"
    )

    assert (
        contract["extracted_data"]["legal_name"]
        == "ABC Industries Pvt Ltd"
    )

    assert (
        contract["extracted_data"]["registration_date"]
        == "15/04/2022"
    )

    assert (
        contract["extracted_data"]["registration_status"]
        == "ACTIVE"
    )

    assert (
        contract["extracted_data"]["business_type"]
        == "PRIVATE LIMITED COMPANY"
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

    assert (
        contract["processing_status"]
        == "FAIL"
    )

    assert (
        contract["document_type"]
        == "UNKNOWN"
    )

    assert contract["extracted_data"] == {}

    assert contract["confidence"] == 0.0

    assert contract["errors"] == [
        "Document text extraction failed"
    ]


def test_pan_without_father_name_passes_quality_validation():
    """
    Verify a PAN document without father_name passes local quality validation
    without fabricating father_name or requiring human review.
    """
    class MockPanLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "ocr_image",
                "raw_text": (
                    "INCOME TAX DEPARTMENT GOVT OF INDIA\n"
                    "SAMPLE PERSON\n"
                    "15/08/1990\n"
                    "Permanent Account Number\n"
                    "ABCDE1234F"
                ),
                "ocr_candidates": [],
            }

    processor = DocumentProcessor(document_loader=MockPanLoader())
    result = processor.process("mock_pan_no_father.png")

    assert result["status"] == "SUCCESS"
    assert result["classification"]["document_type"] == "PAN_CARD"
    assert result["extracted_data"].get("pan") == "ABCDE1234F"
    assert result["extracted_data"].get("name") == "SAMPLE PERSON"
    assert result["extracted_data"].get("date_of_birth") == "15/08/1990"
    assert "father_name" not in result["extracted_data"]

    quality = result["extraction_quality"]
    assert quality["status"] == "PASS"
    assert quality["quality_score"] == 1.0
    assert "father_name" not in quality["fields_requiring_review"]

    verification = result["verification"]
    assert verification["verification_status"] == "VERIFIED"
    assert "father_name" not in verification["fields_requiring_review"]


def test_pan_with_father_name_passes_quality_validation():
    """
    Verify a PAN document with a valid father_name extracts it into verified_fields.
    """
    class MockPanWithFatherLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "ocr_image",
                "raw_text": (
                    "INCOME TAX DEPARTMENT\n"
                    "GOVT OF INDIA\n"
                    "SAMPLE PERSON\n"
                    "PARENT NAME\n"
                    "15/08/1990\n"
                    "Permanent Account Number\n"
                    "ABCDE1234F"
                ),
                "ocr_candidates": [],
            }

    processor = DocumentProcessor(document_loader=MockPanWithFatherLoader())
    result = processor.process("mock_pan_with_father.png")

    assert result["status"] == "SUCCESS"
    assert result["extracted_data"].get("father_name") == "PARENT NAME"
    assert "father_name" in result["extraction_quality"]["verified_fields"]
    assert result["extraction_quality"]["status"] == "PASS"


def test_pan_with_uncertain_father_name_requires_review():
    """
    Verify a PAN document where father_name evidence is present but noisy/uncertain
    places father_name into fields_requiring_review.
    """
    class MockPanUncertainFatherLoader:
        def load_and_extract(self, file_path):
            return {
                "status": "SUCCESS",
                "file_path": file_path,
                "extraction_method": "ocr_image",
                "raw_text": (
                    "INCOME TAX DEPARTMENT\n"
                    "GOVT OF INDIA\n"
                    "SAMPLE PERSON\n"
                    "Father's Name: pos junk\n"
                    "15/08/1990\n"
                    "Permanent Account Number\n"
                    "ABCDE1234F"
                ),
                "ocr_candidates": [],
            }

    processor = DocumentProcessor(document_loader=MockPanUncertainFatherLoader())
    result = processor.process("mock_pan_uncertain.png")

    assert result["status"] == "SUCCESS"
    assert "father_name" in result["extraction_quality"]["fields_requiring_review"]
    assert result["extraction_quality"]["status"] == "REVIEW_REQUIRED"