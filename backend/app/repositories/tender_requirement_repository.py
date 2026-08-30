from sqlalchemy.orm import Session

from app.models.tender_requirement import TenderRequirement
from app.schemas.tender_requirement import TenderRequirementCreate


class TenderRequirementRepository:

    def create(
        self,
        db: Session,
        tender_id: int,
        requirement_data: TenderRequirementCreate,
    ) -> TenderRequirement:

        requirement = TenderRequirement(
            tender_id=tender_id,
            **requirement_data.model_dump(),
        )

        db.add(requirement)
        db.commit()
        db.refresh(requirement)

        return requirement

    def get_by_id(
        self,
        db: Session,
        requirement_id: int,
    ) -> TenderRequirement | None:

        return (
            db.query(TenderRequirement)
            .filter(
                TenderRequirement.id == requirement_id
            )
            .first()
        )

    def get_by_tender_id(
        self,
        db: Session,
        tender_id: int,
    ) -> list[TenderRequirement]:

        return (
            db.query(TenderRequirement)
            .filter(
                TenderRequirement.tender_id == tender_id
            )
            .all()
        )


tender_requirement_repository = TenderRequirementRepository()