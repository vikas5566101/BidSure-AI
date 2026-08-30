from sqlalchemy.orm import Session

from app.models.tender import Tender
from app.schemas.tender import TenderCreate


class TenderRepository:

    def create(
        self,
        db: Session,
        tender_data: TenderCreate,
    ) -> Tender:

        tender = Tender(
            **tender_data.model_dump()
        )

        db.add(tender)
        db.commit()
        db.refresh(tender)

        return tender

    def get_by_id(
        self,
        db: Session,
        tender_id: int,
    ) -> Tender | None:

        return (
            db.query(Tender)
            .filter(Tender.id == tender_id)
            .first()
        )

    def get_all(
        self,
        db: Session,
    ) -> list[Tender]:

        return db.query(Tender).all()

    def get_by_reference_number(
        self,
        db: Session,
        reference_number: str,
    ) -> Tender | None:

        return (
            db.query(Tender)
            .filter(
                Tender.reference_number == reference_number
            )
            .first()
        )


tender_repository = TenderRepository()