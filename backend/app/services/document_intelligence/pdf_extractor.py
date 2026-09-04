from pathlib import Path

import fitz

from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    """
    Text extracted from a single PDF page.
    """

    page_number: int = Field(ge=1)
    text: str


class PDFTextExtractionResult(BaseModel):
    """
    Result of extracting text from a native/text-based PDF.
    """

    pages: list[ExtractedPage]
    total_pages: int = Field(ge=0)
    total_characters: int = Field(ge=0)


class PDFTextExtractor:
    """
    Extracts embedded text from native/text-based PDF files.

    This component does not perform OCR. Scanned/image PDFs
    will be handled by the OCR layer separately.
    """

    def extract(
        self,
        file_path: str | Path,
    ) -> PDFTextExtractionResult:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"PDF path is not a file: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "File must have a .pdf extension."
            )

        try:
            document = fitz.open(path)
        except Exception as exc:
            raise ValueError(
                f"Unable to open PDF: {path}"
            ) from exc

        try:
            pages: list[ExtractedPage] = []

            for page_index, page in enumerate(
                document,
                start=1,
            ):
                text = page.get_text("text")

                pages.append(
                    ExtractedPage(
                        page_number=page_index,
                        text=text,
                    )
                )

            total_pages = len(pages)

            total_characters = sum(
                len(page.text)
                for page in pages
            )

            return PDFTextExtractionResult(
                pages=pages,
                total_pages=total_pages,
                total_characters=total_characters,
            )

        finally:
            document.close()


pdf_text_extractor = PDFTextExtractor()