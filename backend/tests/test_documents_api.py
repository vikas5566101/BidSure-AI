from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_process_native_gst_pdf():
    with open(
        "mock_data/documents/test_gst_certificate.pdf",
        "rb",
    ) as file:

        response = client.post(
            "/documents/process",
            files={
                "file": (
                    "test_gst_certificate.pdf",
                    file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "SUCCESS"
    assert result["file_name"] == "test_gst_certificate.pdf"

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


def test_process_scanned_gst_pdf():
    with open(
        "mock_data/documents/scanned_gst_certificate.pdf",
        "rb",
    ) as file:

        response = client.post(
            "/documents/process",
            files={
                "file": (
                    "scanned_gst_certificate.pdf",
                    file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "SUCCESS"

    assert (
        result["file_name"]
        == "scanned_gst_certificate.pdf"
    )

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


def test_reject_unsupported_file_type():
    response = client.post(
        "/documents/process",
        files={
            "file": (
                "document.txt",
                b"This is not a supported document.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    result = response.json()

    assert "Unsupported file type" in result["detail"]


def test_missing_file():
    response = client.post(
        "/documents/process"
    )

    assert response.status_code == 422


def test_api_response_structure():
    with open(
        "mock_data/documents/test_gst_certificate.pdf",
        "rb",
    ) as file:

        response = client.post(
            "/documents/process",
            files={
                "file": (
                    "test_gst_certificate.pdf",
                    file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200

    result = response.json()

    # Top-level response
    assert "status" in result
    assert "file_name" in result
    assert "extraction" in result
    assert "classification" in result

    # Extraction response
    assert "status" in result["extraction"]
    assert "file_path" in result["extraction"]
    assert "extraction_method" in result["extraction"]
    assert "raw_text" in result["extraction"]

    # Classification response
    classification = result["classification"]

    assert "document_type" in classification
    assert "evidence_score" in classification
    assert "confidence" in classification
    assert "confidence_level" in classification
    assert "matched_patterns" in classification
    assert "evidence" in classification
    assert "ambiguity" in classification
    assert "second_best_document_type" in classification
    assert "second_best_score" in classification
    assert "score_difference" in classification
    assert "needs_review" in classification