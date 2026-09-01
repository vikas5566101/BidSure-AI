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


# =========================================================
# REGISTRATION TYPE — generalized label extraction
# =========================================================


def test_registration_type_extracted_without_colon_separator():
    """
    OCR from real scanned GST certificates frequently omits the
    colon between the label and the value.  The extractor must
    handle "Type of Registration Regular" (no colon).
    """
    text = (
        "Date of Liability 01/07/2017 "
        "Type of Registration Regular "
        "Particulars of Approving Authority Some State"
    )

    extractor = FieldExtractor()
    result = extractor.extract_gst_fields(text)

    assert result.get("registration_type") == "REGULAR"


def test_registration_type_extracted_when_ocr_noise_follows_value():
    """
    When OCR noise appears between the value and the next field
    label (e.g. "Regular 9 |Particulars of Approving"), the
    known-type scan must still return the correct type rather
    than failing due to the bloated captured string.
    """
    text = (
        "Type of Registration Regular 9 |Particulars of Approving "
        "Some State Goods and Services Tax Act"
    )

    extractor = FieldExtractor()
    result = extractor.extract_gst_fields(text)

    assert result.get("registration_type") == "REGULAR"


def test_registration_type_extracted_composition():
    """
    All known registration types must be extractable, not just
    REGULAR.
    """
    text = "Type of Registration: Composition"

    extractor = FieldExtractor()
    result = extractor.extract_gst_fields(text)

    assert result.get("registration_type") == "COMPOSITION"


def test_registration_type_extracted_sez_developer():
    text = "Type of Registration SEZ Developer"

    extractor = FieldExtractor()
    result = extractor.extract_gst_fields(text)

    assert result.get("registration_type") == "SEZ DEVELOPER"


# =========================================================
# LEGAL NAME — field contamination detection
# =========================================================


def test_legal_name_contaminated_by_trade_name_label_is_review_required():
    """
    If the legal_name value contains a known field label such as
    "Trade Name", the extractor failed to stop at the correct
    boundary.  The verifier must flag this as review_required,
    not verified.
    """
    from backend.app.services.document_processing.verifier import (
        DocumentVerifier,
    )

    contaminated_name = "SOME COMPANY PVT LTD Trade Name ANOTHER CO"

    result = DocumentVerifier().verify(
        "GST_CERTIFICATE",
        {"legal_name": contaminated_name},
    )

    assert "legal_name" not in result["verified_fields"]
    assert "legal_name" in result["fields_requiring_review"]


def test_legal_name_clean_value_is_verified():
    """
    A clean business name that does not contain any field label
    must pass verification normally.
    """
    from backend.app.services.document_processing.verifier import (
        DocumentVerifier,
    )

    clean_name = "SUNRISE MEDI OPTIC DEVICES"

    result = DocumentVerifier().verify(
        "GST_CERTIFICATE",
        {"legal_name": clean_name},
    )

    assert "legal_name" in result["verified_fields"]
    assert "legal_name" not in result["fields_requiring_review"]


def test_legal_name_with_registration_in_company_name_not_flagged():
    """
    A company name that contains the word 'Registration' as part
    of its actual name must NOT be flagged as contaminated.
    The contamination check requires the FULL label phrase, not
    just individual common words.
    """
    from backend.app.services.document_processing.verifier import (
        DocumentVerifier,
    )

    # "Registration" alone is fine; "Registration Status" is the label
    name_with_registration = "ABC Registration Services Pvt Ltd"

    result = DocumentVerifier().verify(
        "GST_CERTIFICATE",
        {"legal_name": name_with_registration},
    )

    assert "legal_name" in result["verified_fields"]
    assert "legal_name" not in result["fields_requiring_review"]


# =========================================================
# AUDIT REGRESSION TESTS (Issues 1, 2, 3)
# =========================================================


def test_gstin_checksum_synthesis_prevention():
    """
    Ensure GSTIN with non-matching check digit is NOT synthesized
    into a verified field and requires human review.
    """
    from backend.app.services.document_processing.verifier import DocumentVerifier

    text = "Registration Number : 09AAYFK4129N1ZE"
    extractor = FieldExtractor()
    extracted = extractor.extract_gst_fields(text)

    assert extracted.get("gstin") == "09AAYFK4129N1ZE"

    verification = DocumentVerifier().verify("GST_CERTIFICATE", extracted)
    assert "gstin" in verification["fields_requiring_review"]
    assert "gstin" not in verification["verified_fields"]


def test_registration_type_unidentifiable_returns_none():
    """
    If OCR contains severe corruption and no known registration type
    enum candidate can be identified, registration_type must return None,
    not a raw garbage string.
    """
    text = "Type of Registration Rein BRrs Ren ain eno fae Rae [s"
    extractor = FieldExtractor()
    extracted = extractor.extract_gst_fields(text)

    assert extracted.get("registration_type") is None


def test_registration_type_closed_enum_variants():
    """
    Test generic registration type variants across different OCR line breaks,
    colons, and spacing.
    """
    extractor = FieldExtractor()

    t1 = extractor.extract_gst_fields("Type of Registration Regular")
    assert t1.get("registration_type") == "REGULAR"

    t2 = extractor.extract_gst_fields("Type of Registration: Regular")
    assert t2.get("registration_type") == "REGULAR"

    t3 = extractor.extract_gst_fields("Type of Registration\nRegular")
    assert t3.get("registration_type") == "REGULAR"

    t4 = extractor.extract_gst_fields("Type of Registration 9 | Particulars ... Regular")
    assert t4.get("registration_type") == "REGULAR"


def test_address_multiline_split_label_business_cleaned():
    """
    Ensure multiline table OCR split-labels ('Address of Principal Place of \n Business')
    do not leak the label token 'Business' into the extracted address value.
    """
    extractor = FieldExtractor()

    a1 = extractor.extract_gst_fields("Address of Principal Place of Business 123 Main Road\nDate of Liability 01/07/2017")
    assert a1.get("principal_address") == "123 Main Road"

    a2 = extractor.extract_gst_fields("Address of Principal Place of \n Business \n 123 Main Road\nDate of Liability 01/07/2017")
    assert a2.get("principal_address") == "123 Main Road"

    a3 = extractor.extract_gst_fields("Address of Principal Place of Business: \n 123 Main Road\nDate of Liability 01/07/2017")
    assert a3.get("principal_address") == "123 Main Road"

    a4 = extractor.extract_gst_fields("Address of Principal Place of 1504, TOWER 8, SAVIOUR GREENISLE CROSSINGS: Business REPUBLIC, GHAZIABAD, 201016\nPeriod of Validity From")
    assert "Business" not in a4.get("principal_address")


def test_legal_name_leading_ocr_table_index_cleaned():
    """
    Verify leading OCR table numbers and column noise prefixes are cleaned
    from legal names.
    """
    extractor = FieldExtractor()

    r1 = extractor.extract_gst_fields("1. Legal Name RISHABH JAIN\n2. Trade Name SUNRISE MEDI OPTIC DEVICES")
    assert r1.get("legal_name") == "RISHABH JAIN"

    r2 = extractor.extract_gst_fields("1. Legal Name Bi ice oi RISHABH JAIN : —e Th 2. | Trade Name SUNRISE MEDI OPTIC DEVICES")
    assert r2.get("legal_name") == "RISHABH JAIN"



def test_trade_name_trailing_table_symbol_cleaned():
    """
    Verify trailing OCR table index symbols are cleaned from trade names.
    """
    extractor = FieldExtractor()

    r1 = extractor.extract_gst_fields("Trade Name, if any SUNRISE MEDI OPTIC DEVICES — | 3\nConstitution of Business Proprietorship")
    assert r1.get("trade_name") == "SUNRISE MEDI OPTIC DEVICES"


def test_constitution_trailing_table_symbol_cleaned():
    """
    Verify trailing OCR table index symbols are cleaned from constitution values.
    """
    extractor = FieldExtractor()

    r1 = extractor.extract_gst_fields("Constitution of Business Proprietorship —s > =) | 5\nDate of Liability 01/07/2017")
    assert r1.get("constitution") == "Proprietorship"