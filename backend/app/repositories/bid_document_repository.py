from sqlalchemy.orm import Session

from app.models.bid_document import BidDocument
from app.schemas.bid_document import BidDocumentCreate


class BidDocumentRepository:

    def create(
        self,
        db: Session,
        bid_submission_id: int,
        document_data: BidDocumentCreate,
    ) -> BidDocument:

        document = BidDocument(
            bid_submission_id=bid_submission_id,
            **document_data.model_dump(),
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    def get_by_id(
        self,
        db: Session,
        document_id: int,
    ) -> BidDocument | None:

        return (
            db.query(BidDocument)
            .filter(
                BidDocument.id == document_id
            )
            .first()
        )

    def get_by_submission_id(
        self,
        db: Session,
        bid_submission_id: int,
    ) -> list[BidDocument]:

        return (
            db.query(BidDocument)
            .filter(
                BidDocument.bid_submission_id
                == bid_submission_id
            )
            .all()
        )


bid_document_repository = BidDocumentRepository()