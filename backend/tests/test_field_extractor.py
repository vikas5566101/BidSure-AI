from backend.app.services.document_processing.field_extractor import (
    FieldExtractor,
)


# =========================================================
# GST TESTS
# =========================================================


def test_extract_gst_fields():
    text = """
    GST REGISTRATION CERTIFICATE
    GSTIN: 27ABCDE1234F1Z5
    Legal Name: ABC Industries Pvt Ltd
    Registration Date: 15/04/2022
    Registration Status: Active
    Business Type: Private Limited Company
    Principal Address: 123 Industrial Area, Mumbai, Maharashtra
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result == {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_date": "15/04/2022",
        "registration_status": "ACTIVE",
        "business_type": "PRIVATE LIMITED COMPANY",
        "principal_address": (
            "123 Industrial Area, Mumbai, Maharashtra"
        ),
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


# =========================================================
# PAN TESTS
# =========================================================


def test_extract_pan_fields():
    text = """
    INCOME TAX DEPARTMENT
    PERMANENT ACCOUNT NUMBER
    PAN: ABCDE1234F
    Name: ABC Industries Pvt Ltd
    Father's Name: Rajesh Kumar
    Date of Birth: 15/04/1985
    """

    extractor = FieldExtractor()

    result = extractor.extract_pan_fields(text)

    assert result == {
        "pan": "ABCDE1234F",
        "name": "ABC Industries Pvt Ltd",
        "father_name": "Rajesh Kumar",
        "date_of_birth": "15/04/1985",
    }


def test_extract_pan_fields_empty_text():
    extractor = FieldExtractor()

    result = extractor.extract_pan_fields("")

    assert result == {}


def test_extract_pan_without_label():
    text = "ABCDE1234F"

    extractor = FieldExtractor()

    result = extractor.extract_pan_fields(text)

    assert result == {
        "pan": "ABCDE1234F",
    }


# =========================================================
# UDYAM TESTS
# =========================================================


def test_extract_udyam_fields():
    text = """
    UDYAM REGISTRATION CERTIFICATE

    UDYAM REGISTRATION NUMBER: UDYAM-MH-12-0012345

    Name of Enterprise: ABC Industries Pvt Ltd
    Type of Enterprise: Small
    Major Activity: Manufacturing
    Social Category: General
    Date of Incorporation: 15/04/2010
    Udyam Registration Date: 20/06/2021
    Enterprise Address: 123 Industrial Area, Mumbai, Maharashtra
    """

    extractor = FieldExtractor()

    result = extractor.extract_udyam_fields(text)

    assert result == {
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


def test_extract_udyam_fields_empty_text():
    extractor = FieldExtractor()

    result = extractor.extract_udyam_fields("")

    assert result == {}


def test_extract_udyam_without_label():
    text = "UDYAM-MH-12-0012345"

    extractor = FieldExtractor()

    result = extractor.extract_udyam_fields(text)

    assert result == {
        "udyam_number": "UDYAM-MH-12-0012345",
    }