from pathlib import Path

from .pdf_extractor import extract_text_from_pdf
from .ocr_service import (
    extract_text_from_image,
    extract_text_and_candidates_from_image,
    extract_text_from_scanned_pdf,
)


class DocumentLoader:
    """
    Routes uploaded documents to the appropriate text extraction method.

    Supported formats:
    - PDF
    - JPG
    - JPEG
    - PNG

    PDF handling:
    1. Try native PDF text extraction.
    2. Check whether extracted text is meaningful.
    3. If not meaningful, fall back to OCR.
    """

    def __init__(
        self,
        length_threshold: int = 50,
        alphanumeric_ratio: float = 0.5,
    ):
        self.length_threshold = length_threshold
        self.alphanumeric_ratio = alphanumeric_ratio

    def _is_meaningful_text(self, text: str) -> bool:
        """
        Determine whether text extracted directly from a PDF
        is meaningful enough to avoid OCR.
        """

        cleaned_text = text.strip()

        # Check minimum text length
        if len(cleaned_text) < self.length_threshold:
            return False

        # Count alphanumeric characters
        alnum_count = sum(
            character.isalnum()
            for character in cleaned_text
        )

        # Calculate meaningful character ratio
        ratio = alnum_count / len(cleaned_text)

        return ratio >= self.alphanumeric_ratio

    def load_and_extract(self, file_path: str) -> dict:
        """
        Load a document and extract its raw text.

        Returns:
            Dictionary containing:
            - status
            - file_path
            - extraction_method
            - raw_text
            - ocr_candidates
        """

        path = Path(file_path)

        # -----------------------------
        # 1. Check file exists
        # -----------------------------

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        extension = path.suffix.lower()

        # -----------------------------
        # 2. Image → OCR
        # -----------------------------

        ocr_candidates = []
        if extension in {".jpg", ".jpeg", ".png"}:

            raw_text, ocr_candidates = extract_text_and_candidates_from_image(
                file_path
            )

            extraction_method = "ocr_image"

        # -----------------------------
        # 3. PDF
        # -----------------------------

        elif extension == ".pdf":

            # First try native PDF text extraction
            raw_text = extract_text_from_pdf(
                file_path
            )

            extraction_method = "native_pdf"

            # Check whether the extracted text is meaningful
            if not self._is_meaningful_text(raw_text):

                # PDF is probably scanned/image-based
                raw_text = extract_text_from_scanned_pdf(
                    file_path
                )

                extraction_method = "ocr_pdf"

            ocr_candidates = [{"score": 100.0, "text": raw_text.strip(), "variant": extraction_method, "config": "default"}]

        # -----------------------------
        # 4. Unsupported file
        # -----------------------------

        else:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                "Supported formats: "
                ".pdf, .jpg, .jpeg, .png"
            )

        # -----------------------------
        # 5. Clean extracted text
        # -----------------------------

        cleaned_text = raw_text.strip()

        # -----------------------------
        # 6. Return JSON-compatible data
        # -----------------------------

        return {
            "status": (
                "SUCCESS"
                if cleaned_text
                else "FAIL"
            ),
            "file_path": str(path),
            "extraction_method": extraction_method,
            "raw_text": cleaned_text,
            "ocr_candidates": ocr_candidates,
        }