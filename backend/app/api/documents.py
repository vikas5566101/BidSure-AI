from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.services.document_processing.document_processor import (
    DocumentProcessor,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

processor = DocumentProcessor()

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


@router.post("/process")
async def process_document(
    file: UploadFile = File(...),
):
    """
    Upload and process a document.

    Supported formats:
    - PDF
    - JPG
    - JPEG
    - PNG
    """

    # ---------------------------------------------------------
    # 1. Validate filename
    # ---------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {extension}. "
                "Supported formats: PDF, JPG, JPEG, PNG."
            ),
        )

    # ---------------------------------------------------------
    # 2. Save uploaded file temporarily
    # ---------------------------------------------------------

    temporary_path = None

    try:
        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary_file:

            temporary_path = temporary_file.name

            content = await file.read()

            temporary_file.write(content)

        # -----------------------------------------------------
        # 3. Run document processing pipeline
        # -----------------------------------------------------

        result = processor.process(
            temporary_path
        )

        # Preserve the original uploaded filename
        # in the API response.
        result["file_name"] = file.filename

        return result

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    finally:
        # -----------------------------------------------------
        # 4. Remove temporary file
        # -----------------------------------------------------

        if temporary_path:

            temporary_file_path = Path(
                temporary_path
            )

            if temporary_file_path.exists():
                temporary_file_path.unlink()