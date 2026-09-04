from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.bid_document_repository import (
    bid_document_repository,
)
from app.repositories.bid_submission_repository import (
    bid_submission_repository,
)
from app.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from app.schemas.bid_document import (
    BidDocumentCreate,
    BidDocumentResponse,
    DocumentExtractionResponse,
)
from app.services.document_intelligence.document_service import (
    document_processing_service,
)


router = APIRouter(
    prefix="/bid-submissions",
    tags=["Bid Documents"],
)


@router.post(
    "/{bid_submission_id}/documents",
    response_model=BidDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bid_document(
    bid_submission_id: int,
    document_data: BidDocumentCreate,
    db: Session = Depends(get_db),
):
    submission = bid_submission_repository.get_by_id(
        db,
        bid_submission_id,
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid submission not found.",
        )

    return bid_document_repository.create(
        db,
        bid_submission_id,
        document_data,
    )


@router.get(
    "/{bid_submission_id}/documents",
    response_model=list[BidDocumentResponse],
)
def get_bid_documents(
    bid_submission_id: int,
    db: Session = Depends(get_db),
):
    submission = bid_submission_repository.get_by_id(
        db,
        bid_submission_id,
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid submission not found.",
        )

    return bid_document_repository.get_by_submission_id(
        db,
        bid_submission_id,
    )


@router.post(
    "/documents/{bid_document_id}/process",
    response_model=DocumentExtractionResponse,
)
def process_document(
    bid_document_id: int,
    db: Session = Depends(get_db),
):
    """
    Run Document Intelligence on a previously registered BidDocument.

    The endpoint:
    1. Finds the BidDocument.
    2. Passes its file path to DocumentProcessingService.
    3. Persists the extraction attempt.
    4. Returns the resulting extraction record.

    This endpoint does not perform compliance verification.
    """

    document = bid_document_repository.get_by_id(
        db,
        bid_document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid document not found.",
        )

    extraction = document_processing_service.process_document(
        db=db,
        bid_document_id=document.id,
        file_path=document.file_path,
    )

    return extraction


@router.get(
    "/documents/{bid_document_id}/extraction",
    response_model=DocumentExtractionResponse,
)
def get_document_extraction(
    bid_document_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the latest Document Intelligence extraction
    for a BidDocument.
    """

    document = bid_document_repository.get_by_id(
        db,
        bid_document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid document not found.",
        )

    extraction_repository = DocumentExtractionRepository()

    extraction = (
        extraction_repository.get_latest_by_document_id(
            db,
            bid_document_id,
        )
    )

    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extraction found for this document.",
        )

    return extraction