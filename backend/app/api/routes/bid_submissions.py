from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.bid_submission_repository import (
    bid_submission_repository,
)
from app.repositories.bidder_repository import bidder_repository
from app.repositories.tender_repository import tender_repository
from app.schemas.bid_submission import (
    BidSubmissionCreate,
    BidSubmissionResponse,
)


router = APIRouter(
    prefix="/bid-submissions",
    tags=["Bid Submissions"],
)


@router.post(
    "",
    response_model=BidSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bid_submission(
    submission_data: BidSubmissionCreate,
    db: Session = Depends(get_db),
):
    tender = tender_repository.get_by_id(
        db,
        submission_data.tender_id,
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    bidder = bidder_repository.get_by_id(
        db,
        submission_data.bidder_id,
    )

    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder not found.",
        )

    try:
        return bid_submission_repository.create(
            db,
            submission_data,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This bidder already has a submission "
                "for this tender."
            ),
        )


@router.get(
    "/{submission_id}",
    response_model=BidSubmissionResponse,
)
def get_bid_submission(
    submission_id: int,
    db: Session = Depends(get_db),
):
    submission = bid_submission_repository.get_by_id(
        db,
        submission_id,
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid submission not found.",
        )

    return submission