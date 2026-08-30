from backend.app.services.document_processing.field_extractor import (
    FieldExtractor,
)


def test_extract_gst_fields():
    text = """
    GST REGISTRATION CERTIFICATE
    GSTIN: 27ABCDE1234F1Z5
    Legal Name: ABC Industries Pvt Ltd
    Registration Date: 15/04/2022
    Registration Status: Active
    Business Type: Private Limited Company
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_status": "ACTIVE",
    }


def test_extract_gst_fields_empty_text():
    extractor = FieldExtractor()

    result = extractor.extract_gst_fields("")

    assert result == {}


def test_extract_gstin_only():
    text = """
    GSTIN: 27ABCDE1234F1Z5
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result == {
        "gstin": "27ABCDE1234F1Z5",
    }
