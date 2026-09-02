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


def test_ocr_corrupted_address_label_locality_boundary():
    """
    Verify that OCR spelling variations of 'Locality' (such as 'Locallty') act as
    clean field boundaries, preventing landmark bleeding and enabling locality extraction.
    """
    extractor = FieldExtractor()

    addr = "Address of Principal Place of Business Building No./Flat No.: 44 x a Name Of Premises/Building: AMBALA CANTT Road/Street: LUXMI NAGAR Nearby Landmark; BD Flour Mill Locallty/Sub Locality: Nishat Bagh City/Town/Village: Ambala District: Ambala State: Haryana PIN Code: 133001"
    res = extractor.extract_gst_fields(addr)
    details = res.get("address_details", {})

    assert details.get("building_number") == "44"
    assert details.get("landmark") == "BD Flour Mill"
    assert details.get("locality") == "Nishat Bagh"
    assert details.get("city") == "Ambala"



def test_no_gstin_state_code_guessing():
    """
    Ensure missing 2-digit state codes in 13-character OCR fragments are NOT
    synthesized/guessed to manufacture a 15-character GSTIN.
    """
    extractor = FieldExtractor()

    # 13-character fragment (missing 2-digit state code)
    text = "Registration Number: ABCDE1234F1Z5"
    res = extractor.extract_gst_fields(text)

    # Should not fabricate a 15-character GSTIN with guessed state code
    assert res.get("gstin") is None


def test_pan_header_noise_rejection():
    """
    Verify header noise and lowercase single-word OCR artifacts (e.g. 'eat', 'pos')
    are not extracted as PAN person name.
    """
    extractor = FieldExtractor()

    text = "INCOME TAX DEPARTMENT eat GOVT. OF INDIA 22/11/1975 Permanent Account Number ABCDE1234F"
    res = extractor.extract_pan_fields(text)
    # 'eat' should not be extracted as name
    assert res.get("name") != "eat"


def test_pan_multi_line_layout_segmentation():
    """
    Verify multi-line PAN OCR text with line boundaries extracts person name and father name into separate fields.
    """
    extractor = FieldExtractor()

    text = "INCOME TAX DEPARTMENT\nGOVT. OF INDIA\nVIKRAM SHARMA\nDEEPAK SHARMA\n15/08/1985\nPermanent Account Number ABCDE1234F"
    res = extractor.extract_pan_fields(text)
    assert res.get("name") == "VIKRAM SHARMA"
    assert res.get("father_name") == "DEEPAK SHARMA"
    assert res.get("date_of_birth") == "15/08/1985"
    assert res.get("pan") == "ABCDE1234F"


def test_pan_single_word_name_support():
    """
    Verify single-word legitimate uppercase names are supported and properly extracted.
    """
    extractor = FieldExtractor()

    text = "INCOME TAX DEPARTMENT GOVT. OF INDIA ANAND 10/10/1990 Permanent Account Number ABCDE1234F"
    res = extractor.extract_pan_fields(text)
    assert res.get("name") == "ANAND"


def test_pan_four_word_name_not_arbitrarily_split():
    """
    Verify a 4-word legitimate person name (e.g. MOHAMMED ABDUL RAHMAN KHAN)
    is NOT arbitrarily split at the midpoint into name and father_name.
    """
    extractor = FieldExtractor()

    text = "INCOME TAX DEPARTMENT GOVT. OF INDIA MOHAMMED ABDUL RAHMAN KHAN 15/08/1985 Permanent Account Number ABCDE1234F"
    res = extractor.extract_pan_fields(text)

    # Name must remain intact, NOT split into MOHAMMED ABDUL / RAHMAN KHAN
    assert res.get("name") == "MOHAMMED ABDUL RAHMAN KHAN"
    assert res.get("father_name") is None


def test_pan_four_word_name_with_punctuation_separator_not_split():
    """
    Verify a legitimate 4-word person name containing punctuation/noise separators
    (e.g. MOHAMMED ABDUL, RAHMAN KHAN) is NOT arbitrarily split into father_name.
    """
    extractor = FieldExtractor()

    text = "INCOME TAX DEPARTMENT GOVT. OF INDIA MOHAMMED ABDUL, RAHMAN KHAN 15/08/1985 Permanent Account Number ABCDE1234F"
    res = extractor.extract_pan_fields(text)

    # Candidate name must be intact or first block, and father_name MUST be None
    assert res.get("father_name") is None


def test_pan_name_truncated_at_date_of_birth_boundary():
    extractor = FieldExtractor()
    text = "Name Sample Kumar // Date of Birth 01/01/2002 Permanent Account Number ABCDE1234F"
    res = extractor.extract_pan_fields(text)
    assert res.get("name") == "Sample Kumar"
    assert res.get("date_of_birth") == "01/01/2002"


def test_pan_name_truncated_at_clear_separator():
    extractor = FieldExtractor()
    text = "Name Sample Kumar // vist ferf24 Date of Birth 01/01/2002"
    res = extractor.extract_pan_fields(text)
    assert res.get("name") == "Sample Kumar"


def test_pan_card_without_father_name_field_does_not_fabricate_father_name():
    extractor = FieldExtractor()
    text = "INCOME TAX DEPARTMENT GOVT. OF INDIA Name Sample Kumar Date of Birth 01/01/2002 Permanent Account Number ABCDE1234F"
    res = extractor.extract_pan_fields(text)
    assert res.get("name") == "Sample Kumar"
    assert res.get("father_name") is None


def test_udyam_enterprise_name_stops_at_owner_name():
    extractor = FieldExtractor()
    text = "Name of Enterprise | HAPPY BABIES CARE Owner Name | SMT SHWETA SUDHIR PANDEY"
    res = extractor.extract_udyam_fields(text)
    assert res.get("enterprise_name") == "HAPPY BABIES CARE"


def test_udyam_enterprise_name_stops_at_pan_gstin_email_mobile():
    extractor = FieldExtractor()
    text = "Name of Enterprise | HAPPY BABIES CARE PAN | BKJPP3315D Do you have GSTIN | Exempted Email Id | happy@test.com Mobile No. | 9876543210"
    res = extractor.extract_udyam_fields(text)
    assert res.get("enterprise_name") == "HAPPY BABIES CARE"


def test_udyam_address_stops_at_national_industry_classification():
    extractor = FieldExtractor()
    text = "Official Address of Enterprise UNDRI PUNE 411060 National Industry Classification Code(S) 96 - Other personal service"
    res = extractor.extract_udyam_fields(text)
    assert "National Industry Classification" not in res.get("enterprise_address", "")
    assert "UNDRI PUNE 411060" in res.get("enterprise_address", "")


def test_udyam_address_stops_at_downstream_sections():
    extractor = FieldExtractor()
    text = "Enterprise Address UNDRI PUNE 411060 Government e-Market (GeM) Portal No Date of Printing 31/03/2023"
    res = extractor.extract_udyam_fields(text)
    assert "Government e-Market" not in res.get("enterprise_address", "")
    assert "Date of Printing" not in res.get("enterprise_address", "")


def test_udyam_number_handles_spacing_and_hyphen_variation():
    extractor = FieldExtractor()
    text1 = "Udyam Registration Number : UDYAM MH 26 0428912"
    text2 = "U DYAM-MH-26-0428912"
    assert extractor.extract_udyam_fields(text1).get("udyam_number") == "UDYAM-MH-26-0428912"
    assert extractor.extract_udyam_fields(text2).get("udyam_number") == "UDYAM-MH-26-0428912"


def test_udyam_number_invalid_candidate_rejected():
    extractor = FieldExtractor()
    text = "UDYAM-12-34-5678901 INVALID STRING UDYAM-XX-YY"
    res = extractor.extract_udyam_fields(text)
    assert res.get("udyam_number") is None


def test_udyam_address_stops_at_pin_before_mobile():
    extractor = FieldExtractor()
    text = "Official Address of Enterprise UNDRI PUNE CITY MAHARASHTRA District PUNE . Pin : 411060 Mobile 9326656062 Email: happybabiescare@gmail.com"
    res = extractor.extract_udyam_fields(text)
    addr = res.get("enterprise_address", "")
    assert "Mobile" not in addr
    assert "9326656062" not in addr
    assert "Email" not in addr
    assert "happybabiescare" not in addr
    assert addr.endswith("Pin : 411060") or addr.endswith("411060")


def test_udyam_address_stops_before_email():
    extractor = FieldExtractor()
    text = "Enterprise Address 123 MAIN ROAD CITY Pin 123456 Email Id info@test.com Mobile No. 9999999999"
    res = extractor.extract_udyam_fields(text)
    addr = res.get("enterprise_address", "")
    assert "Email" not in addr
    assert "Mobile" not in addr
    assert "info@test.com" not in addr


def test_real_gst2_legal_name_boundary_isolation():
    extractor = FieldExtractor()
    text = "1 Legal Name KRISHNANAND GE 2 Trae Name, ifany KRISHNANAND € 3. Constitution of Business Limited Liability Partnership"
    res = extractor.extract_gst_fields(text)
    assert res.get("legal_name") == "KRISHNANAND GE"


def test_real_gst2_constitution_normalization():
    extractor = FieldExtractor()
    text = "3. Constitution of Business Limited Linbality Partnership"
    res = extractor.extract_gst_fields(text)
    assert res.get("constitution") == "Limited Liability Partnership"


def test_alternate_ocr_candidate_selection_when_primary_incomplete():
    extractor = FieldExtractor()
    primary_text = "1 Legal Name ALPHA ENTERPRISES 2 Trade Name ALPHA ENTERPRISES"
    candidates = [
        {"score": 90.0, "text": primary_text},
        {"score": 85.0, "text": "1 Legal Name ALPHA ENTERPRISES PRIVATE LIMITED\n2 Trade Name ALPHA ENTERPRISES"},
    ]
    res = extractor.extract_gst_fields(primary_text, ocr_candidates=candidates)
    assert res.get("legal_name") == "ALPHA ENTERPRISES PRIVATE LIMITED"


def test_alternate_ocr_candidate_no_fabrication():
    extractor = FieldExtractor()
    primary_text = "1 Legal Name SAMPLE GE 2 Trade Name SAMPLE GE"
    candidates = [
        {"score": 90.0, "text": primary_text},
        {"score": 88.0, "text": "1 Legal Name SAMPLE GEORCOLOGIST LLP\n2 Trade Name SAMPLE GEORCOLOGIST LLP"},
    ]
    res = extractor.extract_gst_fields(primary_text, ocr_candidates=candidates)
    assert res.get("legal_name") == "SAMPLE GEORCOLOGIST LLP"


def test_no_alternate_candidate_safe_incomplete_result():
    extractor = FieldExtractor()
    primary_text = "1 Legal Name INCOMPLETE COMPANY 2 Trade Name INCOMPLETE COMPANY"
    res = extractor.extract_gst_fields(primary_text, ocr_candidates=[])
    assert res.get("legal_name") == "INCOMPLETE COMPANY"


def test_alternate_ocr_trade_name_recovery_generic():
    extractor = FieldExtractor()
    primary_text = "1 Legal Name SAMPLE ENTERPRISE LLP 2 Trade Name, if any SAMPLE € “OLOGI Lup 3 Constitution Limited Liability Partnership"
    candidates = [
        {"score": 64.0, "text": primary_text},
        {
            "score": 63.0,
            "text": "1 Legal Name SAMPLE ENTERPRISE LLP 2 Trade Name, if any SAMPLE ENTERPRISE LLP 3 Constitution Limited Liability Partnership",
        },
        {
            "score": 62.0,
            "text": "1 Legal Name SAMPLE ENTERPRISE LLP 2 Trade Name, if any SAMPLE ENTERPRISE LLP 3 Constitution Limited Liability Partnership",
        },
    ]
    res = extractor.extract_gst_fields(primary_text, ocr_candidates=candidates)
    assert res.get("trade_name") == "SAMPLE ENTERPRISE LLP"


def test_pan_synthetic_layout_extraction_name_father_dob_pan():
    extractor = FieldExtractor()
    text = (
        "INCOME TAX DEPARTMENT\n"
        "GOVT OF INDIA\n"
        "SAMPLE PERSON\n"
        "PARENT NAME\n"
        "22/11/1975\n"
        "Permanent Account Number\n"
        "ABCDE1234F"
    )
    res = extractor.extract_pan_fields(text)
    assert res.get("name") == "SAMPLE PERSON"
    assert res.get("father_name") == "PARENT NAME"
    assert res.get("date_of_birth") == "22/11/1975"
    assert res.get("pan") == "ABCDE1234F"


def test_pan_header_noise_not_selected_as_father_name():
    extractor = FieldExtractor()
    text = (
        "INCOME TAX DEPARTMENT GOVT OF INDIA "
        "SAMPLE PERSON 22/11/1975 Permanent Account Number ABCDE1234F Signature"
    )
    res = extractor.extract_pan_fields(text)
    assert res.get("name") == "SAMPLE PERSON"
    assert "father_name" not in res or res.get("father_name") not in (
        "INCOME TAX DEPARTMENT",
        "GOVT OF INDIA",
        "PERMANENT ACCOUNT NUMBER",
        "SIGNATURE",
    )


def test_pan_candidate_dob_consensus_selection():
    extractor = FieldExtractor()
    primary_text = "GOVT OF INDIA SAMPLE PERSON PARENT NAME 22/01/1975 Permanent Account Number ABCDE1234F"
    candidates = [
        {"score": 50.0, "text": primary_text},
        {"score": 45.0, "text": "GOVT OF INDIA SAMPLE PERSON PARENT NAME 22/11/1975 Permanent Account Number ABCDE1234F"},
        {"score": 44.0, "text": "GOVT OF INDIA SAMPLE PERSON PARENT NAME 22/11/1975 Permanent Account Number ABCDE1234F"},
        {"score": 43.0, "text": "GOVT OF INDIA SAMPLE PERSON PARENT NAME 22/11/1975 Permanent Account Number ABCDE1234F"},
    ]
    res = extractor.extract_pan_fields(primary_text, ocr_candidates=candidates)
    assert res.get("date_of_birth") == "22/11/1975"


def test_udyam_enterprise_name_boundary_ocr_artifact_cleaning():
    extractor = FieldExtractor()
    cleaned = extractor._clean_udyam_enterprise_name("SAMPLE ENTERPRISES «")
    assert cleaned == "SAMPLE ENTERPRISES"

    cleaned_guillemet = extractor._clean_udyam_enterprise_name("« SAMPLE ENTERPRISES »")
    assert cleaned_guillemet == "SAMPLE ENTERPRISES"


def test_udyam_enterprise_name_preserves_internal_punctuation():
    extractor = FieldExtractor()
    cleaned = extractor._clean_udyam_enterprise_name("SAMPLE ENTERPRISES (INDIA) PVT. LTD.")
    assert cleaned == "SAMPLE ENTERPRISES (INDIA) PVT. LTD."


def test_udyam_enterprise_name_alternate_ocr_recovery():
    extractor = FieldExtractor()
    primary_text = "Type of Enterprise MICRO Social Category GENERAL Date of Incorporation 01/01/2022"
    candidates = [
        {"score": 45.0, "text": "Name of Enterprise | SAMPLE BUSINESS SERVICES Type of Enterprise MICRO"},
        {"score": 44.0, "text": "Name of Enterprise SAMPLE BUSINESS SERVICES Type of Enterprise MICRO"},
        {"score": 42.0, "text": "Name of Enterprise [SAMPLE BUSINESS SERVICES] Type of Enterprise MICRO"},
    ]
    res = extractor.extract_udyam_fields(primary_text, ocr_candidates=candidates)
    assert res.get("enterprise_name") == "SAMPLE BUSINESS SERVICES"


def test_udyam_noisy_enterprise_name_loses_to_clean_consensus_candidate():
    extractor = FieldExtractor()
    primary_text = "Name of Enterprise | S@MPLE €NTERPR1S3S Type of Enterprise MICRO"
    candidates = [
        {"score": 48.0, "text": "Name of Enterprise | SAMPLE BUSINESS SERVICES Type of Enterprise MICRO"},
        {"score": 47.0, "text": "Name of Enterprise SAMPLE BUSINESS SERVICES Type of Enterprise MICRO"},
    ]
    res = extractor.extract_udyam_fields(primary_text, ocr_candidates=candidates)
    assert res.get("enterprise_name") == "SAMPLE BUSINESS SERVICES"


def test_udyam_official_address_table_delimiter_and_sublabel_cleaning():
    extractor = FieldExtractor()
    text = """Official address of Enterprise
Flat/Door/Block No. OFFICE NO 102-103
Name of Premises/Building FIRST FLOOR, SHREE SIDDHIVINAYAK SANKALP
Village/Town PHASE 1
Block WADACHIWADI ROAD
Road/Street/Lane UNDRI
City PUNE CITY
State MAHARASHTRA
District PUNE
Pin 411060"""
    res = extractor.extract_udyam_fields(text)
    addr = res.get("enterprise_address", "")
    assert "OFFICE NO 102-103" in addr
    assert "FIRST FLOOR, SHREE SIDDHIVINAYAK SANKALP" in addr
    assert "411060" in addr
    for delimiter in ["[", "]", "|", "{", "}"]:
        assert delimiter not in addr


def test_udyam_incomplete_number_rejected():
    extractor = FieldExtractor()
    res = extractor.extract_udyam_fields("UDYAM-MH 4")
    assert "udyam_number" not in res