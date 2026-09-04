from pathlib import Path

import fitz
import fitz
import pymupdf
import pytesseract
from PIL import Image

from app.services.document_intelligence.schemas import (
    ExtractedPage,
    PDFTextExtractionResult,
)


class OCRExtractor:
    """
    Extract text from scanned/image-based PDF documents using Tesseract OCR.

    This extractor is specifically for PDFs where normal PDF text extraction
    does not provide usable text.

    Pipeline:
        PDF -> PyMuPDF rendering -> PIL Image -> Tesseract OCR
    """

    def __init__(
        self,
        tesseract_cmd: str | None = None,
        dpi: int = 300,
        language: str = "eng",
    ) -> None:
        """
        Args:
            tesseract_cmd:
                Optional path to the Tesseract executable.
                If None, pytesseract uses the Tesseract available on PATH.

            dpi:
                Resolution used when rendering PDF pages.
                300 DPI is a good balance between OCR accuracy and speed.

            language:
                Tesseract language code.
                "eng" is used for the initial GST/Udyam/PAN/Income Tax demo.
        """
        if dpi <= 0:
            raise ValueError("dpi must be greater than 0")

        if not language.strip():
            raise ValueError("language must not be empty")

        self.dpi = dpi
        self.language = language

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract(self, file_path: str | Path) -> PDFTextExtractionResult:
        """
        Extract text from every page of a scanned PDF.

        Args:
            file_path: Path to the PDF file.

        Returns:
            PDFTextExtractionResult containing page-wise OCR text.

        Raises:
            FileNotFoundError:
                If the file does not exist.

            ValueError:
                If the path is not a file or is not a PDF.

            RuntimeError:
                If the PDF cannot be opened or OCR fails.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {path.suffix}")

        document = None

        try:
            document = pymupdf.open(path)

            pages: list[ExtractedPage] = []

            for page_index in range(len(document)):
                page = document[page_index]

                # Render PDF page to an image.
                pixmap = self._render_page(page)

                # Convert PyMuPDF pixmap to PIL Image.
                image = Image.frombytes(
                    "RGB",
                    [pixmap.width, pixmap.height],
                    pixmap.samples,
                )

                # Run OCR.
                text = pytesseract.image_to_string(
                    image,
                    lang=self.language,
                )

                pages.append(
                    ExtractedPage(
                        page_number=page_index + 1,
                        text=text,
                    )
                )

            total_characters = sum(len(page.text) for page in pages)

            return PDFTextExtractionResult(
                pages=pages,
                total_pages=len(pages),
                total_characters=total_characters,
            )

        except Exception as exc:
            # Preserve our own validation exceptions.
            if isinstance(exc, (FileNotFoundError, ValueError)):
                raise

            raise RuntimeError(
                f"Failed to perform OCR on PDF: {path}"
            ) from exc

        finally:
            if document is not None:
                document.close()

    def _render_page(self, page: fitz.Page) -> fitz.Pixmap:
        """
        Render a PDF page at the configured DPI.

        PyMuPDF's default page rendering is roughly 72 DPI, so we scale
        the page according to the requested DPI.
        """
        scale = self.dpi / 72

        matrix = pymupdf.Matrix(scale, scale)

        return page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )


ocr_extractor = OCRExtractor()