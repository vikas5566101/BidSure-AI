from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image


def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from an image using OCR.

    Args:
        file_path: Path to the image file.

    Returns:
        Extracted text as a single string.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    supported_formats = {".jpg", ".jpeg", ".png"}

    if path.suffix.lower() not in supported_formats:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {supported_formats}"
        )

    image = Image.open(path)

    text = pytesseract.image_to_string(image)

    return text.strip()


def extract_text_from_scanned_pdf(file_path: str) -> str:
    """
    Extract text from a scanned PDF using OCR.

    Args:
        file_path: Path to the scanned PDF.

    Returns:
        Extracted text from all PDF pages.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Expected a PDF file")

    pdf = pymupdf.open(file_path)

    extracted_pages = []

    try:
        for page in pdf:
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

            image = Image.frombytes(
                "RGB",
                [pixmap.width, pixmap.height],
                pixmap.samples,
            )

            text = pytesseract.image_to_string(image)

            if text.strip():
                extracted_pages.append(text.strip())

    finally:
        pdf.close()

    return "\n\n".join(extracted_pages)