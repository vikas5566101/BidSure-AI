import pytest
from backend.app.services.document_processing.ocr_service import _calculate_ocr_confidence


def test_ocr_candidate_with_clean_date_evidence_preferred():
    """
    Verify that when two OCR candidates are otherwise virtually identical in score,
    the candidate containing structured date evidence receives the +3.0 date evidence bonus.
    """
    text_without_date = "INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER ABCDE1234F SAMPLE KUMAR"
    text_with_date = "INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER ABCDE1234F SAMPLE KUMAR 01/01/2002"

    score_without, _ = _calculate_ocr_confidence(None, config="--psm 3", raw_text=text_without_date)
    score_with, _ = _calculate_ocr_confidence(None, config="--psm 3", raw_text=text_with_date)

    assert score_with > score_without
    assert score_with - score_without >= 3.0


def test_ocr_date_bonus_does_not_override_superior_candidate():
    """
    Verify that the +3.0 date evidence bonus is small and proportional, so it CANNOT
    cause a low-quality or garbage candidate to beat a high-quality candidate.
    """
    text_high_quality = (
        "INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER ABCDE1234F "
        "MOHAMMED ABDUL RAHMAN KHAN FATHER NAME ABDUL RAHMAN"
    )
    text_garbage_with_date = "Garbage % $ # @ ~ 01/01/2002"

    score_high, _ = _calculate_ocr_confidence(None, config="--psm 3", raw_text=text_high_quality)
    score_garbage, _ = _calculate_ocr_confidence(None, config="--psm 3", raw_text=text_garbage_with_date)

    assert score_high > score_garbage
