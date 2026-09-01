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

def test_gst_trade_name_stops_at_additional_trade_names():
    text = """
    Legal Name RISHABH JAIN
    Trade Name, if any SUNRISE MEDI OPTIC DEVICES Additional trade names, if any oS
    Constitution of Business Proprietorship
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result["legal_name"] == "RISHABH JAIN"
    assert result["trade_name"] == "SUNRISE MEDI OPTIC DEVICES"


def test_udyam_enterprise_name_stops_at_table_headers():
    text = """
    UDYAM REGISTRATION CERTIFICATE
    UDYAM REGISTRATION NUMBER: UDYAM-KR-03-0278313

    Name of Enterprise: ABHINAM ENTERPRISES [SNo. | Classification Year | Enterprise Type | Classification Date
    Type of Enterprise: Micro
    Social Category: General
    Date of Incorporation: 15/06/2017
    Udyam Registration Date: 26/06/2023
    """

    extractor = FieldExtractor()

    result = extractor.extract_udyam_fields(text)

    assert result["enterprise_name"] == "ABHINAM ENTERPRISES"


def test_gstin_ocr_one_character_correction():
    text = """
    GST REGISTRATION CERTIFICATE
    GSTIN: 27ABCDE1234FIZ5
    Legal Name: ABC Industries Pvt Ltd
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result["gstin"] == "27ABCDE1234F1Z5"


def test_gstin_with_spaces_and_ocr_noise():
    text = """
    GSTIN: 27 ABCDE 1234 F1 Z5
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result["gstin"] == "27ABCDE1234F1Z5"


def test_pan_ocr_one_character_correction():
    text = """
    INCOME TAX DEPARTMENT
    PAN: ABCDE1234I
    """

    extractor = FieldExtractor()

    result = extractor.extract_pan_fields(text)

    assert result["pan"] == "ABCDE1234I"


def test_udyam_ocr_one_character_correction():
    text = """
    UDYAM REGISTRATION CERTIFICATE
    UDYAM REGISTRATION NUMBER: UDYAM-KR-03-O278313
    """

    extractor = FieldExtractor()

    result = extractor.extract_udyam_fields(text)

    assert result["udyam_number"] == "UDYAM-KR-03-0278313"


def test_invalid_gstin_is_not_accepted():
    text = """
    GSTIN: INVALID12345678
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert "gstin" not in result


def test_invalid_pan_is_not_accepted():
    text = """
    PAN: INVALID123
    """

    extractor = FieldExtractor()

    result = extractor.extract_pan_fields(text)

    assert "pan" not in result


def test_real_gst_ocr_gstin_correction():
    text = """
    Registration Number : 06AIXPI829LIIZC
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result["gstin"] == "06AIXPI8291I1ZC"


def test_gst_trade_name_preserves_word_spacing():
    text = """
    Legal Name RISHABH JAIN
    Trade Name, if any SUNRISE MEDI OPTIC DEVICES
    Constitution of Business Proprietorship
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result["trade_name"] == "SUNRISE MEDI OPTIC DEVICES"


def test_gst_address_removes_trailing_ocr_noise_after_pin():
    text = """
    Address of Principal Place of Business Building No./Flat No.: 44
    Name Of Premises/Building: AMBALA CANTT
    Road/Street: LUXMI NAGAR
    Nearby Landmark; BD Flour Mill
    Locality/Sub Locality: Nishat Bagh
    City/Town/Village: Ambala
    District: Ambala
    State: Haryana
    PIN Code: 133001 6
    """

    extractor = FieldExtractor()

    result = extractor.extract_gst_fields(text)

    assert result["principal_address"].endswith(
        "PIN Code: 133001"
    )

    assert result["address_details"]["pin_code"] == "133001"