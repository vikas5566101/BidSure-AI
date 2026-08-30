import pymupdf


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from all pages of a PDF.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text as a single string.
    """
    document = pymupdf.open(file_path)

    try:
        pages = []

        for page in document:
            text = page.get_text()

            if text:
                pages.append(text)

        return "\n".join(pages).strip()

    finally:
        document.close()