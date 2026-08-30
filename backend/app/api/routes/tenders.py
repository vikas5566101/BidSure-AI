from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.tender_repository import tender_repository
from app.repositories.tender_requirement_repository import (
    tender_requirement_repository,
)
from app.schemas.tender import TenderCreate, TenderResponse
from app.schemas.tender_requirement import (
    TenderRequirementCreate,
    TenderRequirementResponse,
)


router = APIRouter(
    prefix="/tenders",
    tags=["Tenders"],
)


@router.post(
    "",
    response_model=TenderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tender(
    tender_data: TenderCreate,
    db: Session = Depends(get_db),
):
    existing_tender = (
        tender_repository.get_by_reference_number(
            db,
            tender_data.reference_number,
        )
    )

    if existing_tender:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tender with this reference number already exists.",
        )

    return tender_repository.create(
        db,
        tender_data,
    )


@router.get(
    "",
    response_model=list[TenderResponse],
)
def get_all_tenders(
    db: Session = Depends(get_db),
):
    return tender_repository.get_all(db)


@router.get(
    "/{tender_id}",
    response_model=TenderResponse,
)
def get_tender(
    tender_id: int,
    db: Session = Depends(get_db),
):
    tender = tender_repository.get_by_id(
        db,
        tender_id,
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    return tender


@router.post(
    "/{tender_id}/requirements",
    response_model=TenderRequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tender_requirement(
    tender_id: int,
    requirement_data: TenderRequirementCreate,
    db: Session = Depends(get_db),
):
    tender = tender_repository.get_by_id(
        db,
        tender_id,
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    return tender_requirement_repository.create(
        db,
        tender_id,
        requirement_data,
    )


@router.get(
    "/{tender_id}/requirements",
    response_model=list[TenderRequirementResponse],
)
def get_tender_requirements(
    tender_id: int,
    db: Session = Depends(get_db),
):
    tender = tender_repository.get_by_id(
        db,
        tender_id,
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found.",
        )

    return tender_requirement_repository.get_by_tender_id(
        db,
        tender_id,
    )