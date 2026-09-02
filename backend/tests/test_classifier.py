from backend.app.services.document_processing.classifier import DocumentClassifier


def test_gst_certificate_classification():
    text = """
    GST REGISTRATION CERTIFICATE
    GSTIN: 27ABCDE1234F1Z5
    Legal Name: ABC Industries Pvt Ltd
    Registration Date: 15/04/2022
    Registration Status: Active
    Business Type: Private Limited Company
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"


def test_pan_card_classification():
    text = """
    INCOME TAX DEPARTMENT
    PERMANENT ACCOUNT NUMBER
    ABCDE1234F
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "PAN_CARD"


def test_unknown_document():
    text = """
    This is some random document content.
    It does not contain any known document indicators.
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "UNKNOWN"
    assert result["confidence"] == 0.0
    assert result["evidence_score"] == 0.0
    assert result["needs_review"] is True


def test_high_confidence_gst_certificate():
    text = """
    GOODS AND SERVICES TAX
    GST REGISTRATION
    GSTIN: 27ABCDE1234F1Z5
    CERTIFICATE OF REGISTRATION
    TAXPAYER
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["evidence_score"] == 1.0
    assert result["confidence"] >= 0.90
    assert result["confidence_level"] == "HIGH"
    assert result["needs_review"] is False


def test_medium_confidence_gst_certificate():
    text = """
    GSTIN: 27ABCDE1234F1Z5
    GST registration
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["evidence_score"] == 0.60
    assert result["confidence"] >= 0.70
    assert result["confidence_level"] == "MEDIUM"
    assert result["needs_review"] is False


def test_weighted_evidence_score():
    text = """
    GSTIN: 27ABCDE1234F1Z5
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["evidence_score"] == 0.40
    assert result["confidence"] == 0.40
    assert result["confidence_level"] == "LOW"
    assert result["needs_review"] is True


def test_evidence_breakdown():
    text = """
    GSTIN: 27ABCDE1234F1Z5
    GST registration
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["evidence"] == [
        {
            "pattern": "gstin",
            "weight": 0.40,
            "matched_as": "gstin",
        },
        {
            "pattern": "gst registration",
            "weight": 0.20,
            "matched_as": "gst registration",
        },
    ]


def test_gstin_ocr_variant():
    text = """
    GST1N: 27ABCDE1234F1Z5
    GST registration
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["evidence_score"] == 0.60
    assert result["confidence"] == 0.70

    assert {
        "pattern": "gstin",
        "weight": 0.40,
        "matched_as": "gst1n",
    } in result["evidence"]


def test_gstin_with_space_ocr_variant():
    text = """
    GST IN: 27ABCDE1234F1Z5
    GST registration
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["evidence_score"] == 0.60
    assert result["confidence"] == 0.70

    assert {
        "pattern": "gstin",
        "weight": 0.40,
        "matched_as": "gst in",
    } in result["evidence"]


def test_pan_substring_false_positive():
    text = """
    This company operates across multiple countries.
    The company has several departments and branches.
    """

    classifier = DocumentClassifier()

    result = classifier.classify(text)

    assert result["document_type"] == "UNKNOWN"
    assert result["confidence"] == 0.0
    assert result["evidence_score"] == 0.0
    assert result["matched_patterns"] == []
    assert result["evidence"] == []
    assert result["needs_review"] is True


def test_ambiguous_classification():
    classifier = DocumentClassifier()

    # Controlled test weights.
    # GST = 0.60
    # Company Registration = 0.55
    # Difference = 0.05
    classifier.DOCUMENT_PATTERNS = {
        "GST_CERTIFICATE": {
            "gstin": 0.60,
        },
        "COMPANY_REGISTRATION": {
            "certificate of incorporation": 0.55,
        },
    }

    text = """
    GSTIN
    certificate of incorporation
    """

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["evidence_score"] == 0.60
    assert result["second_best_document_type"] == "COMPANY_REGISTRATION"
    assert result["second_best_score"] == 0.55
    assert result["score_difference"] == 0.05
    assert result["ambiguity"] is True
    assert result["needs_review"] is True


def test_clear_classification_is_not_ambiguous():
    classifier = DocumentClassifier()

    text = """
    GST REGISTRATION CERTIFICATE
    GSTIN
    GST registration
    GOODS AND SERVICES TAX
    """

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["ambiguity"] is False
    assert result["needs_review"] is False


def test_ambiguity_threshold_boundary():
    classifier = DocumentClassifier()

    # GST = 0.60
    # Company Registration = 0.50
    # Difference = exactly 0.10
    classifier.DOCUMENT_PATTERNS = {
        "GST_CERTIFICATE": {
            "gstin": 0.60,
        },
        "COMPANY_REGISTRATION": {
            "certificate of incorporation": 0.50,
        },
    }

    text = """
    GSTIN
    certificate of incorporation
    """

    result = classifier.classify(text)

    assert result["document_type"] == "GST_CERTIFICATE"
    assert result["evidence_score"] == 0.60
    assert result["second_best_document_type"] == "COMPANY_REGISTRATION"
    assert result["second_best_score"] == 0.50
    assert result["score_difference"] == 0.10
    assert result["ambiguity"] is False


def test_udyam_classification_breakdown_documented():
    text = """
    UDYAM REGISTRATION CERTIFICATE
    UDYAM REGISTRATION NUMBER UDYAM-MH-26-0428912
    NAME OF ENTERPRISE HAPPY BABIES CARE
    """
    classifier = DocumentClassifier()
    result = classifier.classify(text)
    assert result["document_type"] == "UDYAM_CERTIFICATE"
    assert result["evidence_score"] >= 0.60