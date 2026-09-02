"""
Team 1 -> Team 2 Handoff Contract Unit Tests.

These tests verify the frozen minimal handoff interface between Team 1
(Document Intelligence) and Team 2 (Government Verification).

Contracts verified:
1. GST contract payload structure
2. PAN contract payload structure
3. Udyam contract payload structure
4. UNKNOWN document payload structure
5. Missing identifier handling
6. Ambiguous identifier handling
7. OCR / Loading failure handling
8. Internal field leakage prevention
"""

import pytest
from backend.app.services.document_processing.document_processor import DocumentProcessor


def test_gst_team2_contract_payload():
    processor = DocumentProcessor()
    raw_result = {
        "status": "SUCCESS",
        "file_path": "test.jpeg",
        "classification": {
            "document_type": "GST_CERTIFICATE",
            "confidence": 0.95,
            "evidence": ["GSTIN pattern matched"],
        },
        "extracted_data": {
            "gstin": "27AAACG1234F1Z5",
            "legal_name": "SAMPLE TRADERS",
            "trade_name": "SAMPLE TRADERS",
            "constitution": "Proprietorship",
            "registration_date": "01/07/2017",
            "registration_type": "REGULAR",
            "principal_address": "MUMBAI MAHARASHTRA 400001",
        },
        "extraction_quality": {
            "status": "PASS",
            "quality_score": 1.0,
            "verified_fields": ["gstin", "legal_name"],
            "fields_requiring_review": [],
        },
        "extraction": {"raw_text": "INTERNAL OCR TEXT"},
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    assert payload["document_type"] == "GST_CERTIFICATE"
    assert payload["extracted_data"]["gstin"] == "27AAACG1234F1Z5"
    assert payload["extracted_data"]["legal_name"] == "SAMPLE TRADERS"
    assert payload["extraction_status"] == "PASS"

    # Leakage assertions
    assert "raw_text" not in payload
    assert "classification_evidence" not in payload
    assert "ocr_candidates" not in payload
    assert "internal_scores" not in payload


def test_pan_team2_contract_payload():
    processor = DocumentProcessor()
    raw_result = {
        "status": "SUCCESS",
        "file_path": "pan.jpeg",
        "classification": {
            "document_type": "PAN_CARD",
            "confidence": 0.90,
        },
        "extracted_data": {
            "pan": "ABCDE1234F",
            "name": "SAMPLE KUMAR",
            "father_name": None,
            "date_of_birth": "01/01/2000",
        },
        "extraction_quality": {
            "status": "PASS",
            "quality_score": 1.0,
            "verified_fields": ["pan", "name", "date_of_birth"],
            "fields_requiring_review": [],
        },
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    assert payload["document_type"] == "PAN_CARD"
    assert payload["extracted_data"]["pan"] == "ABCDE1234F"
    assert payload["extracted_data"]["name"] == "SAMPLE KUMAR"
    assert payload["extracted_data"]["date_of_birth"] == "01/01/2000"
    assert payload["extraction_status"] == "PASS"

    assert "raw_text" not in payload
    assert "extraction" not in payload


def test_udyam_team2_contract_payload():
    processor = DocumentProcessor()
    raw_result = {
        "status": "SUCCESS",
        "file_path": "udyam.jpeg",
        "classification": {
            "document_type": "UDYAM_CERTIFICATE",
            "confidence": 0.88,
        },
        "extracted_data": {
            "udyam_number": "UDYAM-MH-01-0012345",
            "enterprise_name": "HAPPY ENTERPRISES",
            "enterprise_type": "MICRO",
        },
        "extraction_quality": {
            "status": "PASS",
            "quality_score": 0.9,
            "verified_fields": ["udyam_number", "enterprise_name"],
            "fields_requiring_review": [],
        },
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    assert payload["document_type"] == "UDYAM_CERTIFICATE"
    assert payload["extracted_data"]["udyam_number"] == "UDYAM-MH-01-0012345"
    assert payload["extracted_data"]["enterprise_name"] == "HAPPY ENTERPRISES"
    assert payload["extraction_status"] == "PASS"


def test_unknown_document_team2_contract_payload():
    processor = DocumentProcessor()
    raw_result = {
        "status": "SUCCESS",
        "file_path": "unknown.pdf",
        "classification": {
            "document_type": "UNKNOWN",
            "confidence": 0.20,
        },
        "extracted_data": {"some_garbage": "val"},
        "extraction_quality": {
            "status": "REVIEW_REQUIRED",
            "quality_score": 0.0,
            "verified_fields": [],
            "fields_requiring_review": [],
        },
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    assert payload["document_type"] == "UNKNOWN"
    assert payload["extracted_data"] == {}
    assert payload["extraction_status"] == "REVIEW_REQUIRED"


def test_missing_identifier_requires_review():
    processor = DocumentProcessor()
    raw_result = {
        "status": "SUCCESS",
        "file_path": "gst_no_id.jpeg",
        "classification": {
            "document_type": "GST_CERTIFICATE",
            "confidence": 0.85,
        },
        "extracted_data": {
            "legal_name": "SAMPLE TRADERS",
        },
        "extraction_quality": {
            "status": "REVIEW_REQUIRED",
            "quality_score": 0.2,
            "verified_fields": ["legal_name"],
            "fields_requiring_review": ["gstin"],
        },
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    assert payload["document_type"] == "GST_CERTIFICATE"
    assert "gstin" not in payload["extracted_data"]
    assert payload["extraction_status"] == "REVIEW_REQUIRED"


def test_ambiguous_identifier_requires_review():
    processor = DocumentProcessor()
    raw_result = {
        "status": "SUCCESS",
        "file_path": "pan_ambiguous.jpeg",
        "classification": {
            "document_type": "PAN_CARD",
            "confidence": 0.70,
        },
        "extracted_data": {
            "pan": "ABCDE1234",  # Malformed 9-char PAN
            "name": "SAMPLE KUMAR",
        },
        "extraction_quality": {
            "status": "REVIEW_REQUIRED",
            "quality_score": 0.5,
            "verified_fields": ["name"],
            "fields_requiring_review": ["pan"],
        },
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    assert payload["document_type"] == "PAN_CARD"
    assert payload["extraction_status"] == "REVIEW_REQUIRED"


def test_ocr_failure_team2_payload():
    processor = DocumentProcessor()
    raw_result = {
        "status": "FAIL",
        "file_path": "corrupt.jpg",
        "classification": {
            "document_type": "UNKNOWN",
            "confidence": 0.0,
        },
        "extracted_data": {},
        "extraction_quality": {
            "status": "REVIEW_REQUIRED",
            "quality_score": 0.0,
            "verified_fields": [],
            "fields_requiring_review": [],
        },
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    assert payload["document_type"] == "UNKNOWN"
    assert payload["extracted_data"] == {}
    assert payload["extraction_status"] == "REVIEW_REQUIRED"


def test_no_internal_diagnostic_fields_leak_into_team2_payload():
    processor = DocumentProcessor()
    raw_result = {
        "status": "SUCCESS",
        "file_path": "doc.jpg",
        "classification": {
            "document_type": "GST_CERTIFICATE",
            "confidence": 0.99,
            "evidence": ["GSTIN pattern matched"],
            "scores": {"GST": 100, "PAN": 0},
        },
        "extraction": {
            "status": "SUCCESS",
            "raw_text": "RAW OCR TEXT SAMPLE",
            "ocr_candidates": ["CANDIDATE 1", "CANDIDATE 2"],
        },
        "extracted_data": {
            "gstin": "27AAACG1234F1Z5",
        },
        "verification": {
            "verified_fields": ["gstin"],
        },
        "extraction_quality": {
            "status": "PASS",
            "quality_score": 1.0,
        },
        "internal_scores": {"ocr": 95.0},
    }

    payload = processor.get_team2_handoff_payload(raw_result)

    # Approved top-level keys ONLY
    allowed_keys = {"document_type", "extracted_data", "extraction_status"}
    assert set(payload.keys()) == allowed_keys

    # Explicit negative assertion on diagnostic leakages
    assert "raw_text" not in payload
    assert "classification_evidence" not in payload
    assert "ocr_candidates" not in payload
    assert "internal_scores" not in payload
    assert "verification" not in payload
    assert "extraction" not in payload
