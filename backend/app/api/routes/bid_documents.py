from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.bid_document_repository import (
    bid_document_repository,
)
from app.repositories.bid_submission_repository import (
    bid_submission_repository,
)
from app.schemas.bid_document import (
    BidDocumentCreate,
    BidDocumentResponse,
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