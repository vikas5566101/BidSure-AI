from sqlalchemy.orm import Session

from app.models.bidder import Bidder
from app.schemas.bidder import BidderCreate


class BidderRepository:

    def create(
        self,
        db: Session,
        bidder_data: BidderCreate,
    ) -> Bidder:

        bidder = Bidder(
            **bidder_data.model_dump()
        )

        db.add(bidder)
        db.commit()
        db.refresh(bidder)

        return bidder

    def get_by_id(
        self,
        db: Session,
        bidder_id: int,
    ) -> Bidder | None:

        return (
            db.query(Bidder)
            .filter(Bidder.id == bidder_id)
            .first()
        )

    def get_all(
        self,
        db: Session,
    ) -> list[Bidder]:

        return db.query(Bidder).all()

    def get_by_gstin(
        self,
        db: Session,
        gstin: str,
    ) -> Bidder | None:

        return (
            db.query(Bidder)
            .filter(Bidder.gstin == gstin)
            .first()
        )


bidder_repository = BidderRepository()