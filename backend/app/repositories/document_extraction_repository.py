from sqlalchemy.orm import Session

from app.models.document_extraction import DocumentExtraction


class DocumentExtractionRepository:
    """
    Database operations for document extraction records.

    This repository is responsible only for persistence.
    It does not perform document processing, AI extraction,
    verification, or compliance evaluation.
    """

    def create(
        self,
        db: Session,
        extraction: DocumentExtraction,
    ) -> DocumentExtraction:
        db.add(extraction)
        db.commit()
        db.refresh(extraction)
        return extraction

    def get_by_id(
        self,
        db: Session,
        extraction_id: int,
    ) -> DocumentExtraction | None:
        return (
            db.query(DocumentExtraction)
            .filter(DocumentExtraction.id == extraction_id)
            .first()
        )

    def get_by_document_id(
        self,
        db: Session,
        bid_document_id: int,
    ) -> list[DocumentExtraction]:
        return (
            db.query(DocumentExtraction)
            .filter(
                DocumentExtraction.bid_document_id
                == bid_document_id
            )
            .order_by(DocumentExtraction.created_at.desc())
            .all()
        )

    def get_latest_by_document_id(
        self,
        db: Session,
        bid_document_id: int,
    ) -> DocumentExtraction | None:
        return (
            db.query(DocumentExtraction)
            .filter(
                DocumentExtraction.bid_document_id
                == bid_document_id
            )
            .order_by(DocumentExtraction.created_at.desc())
            .first()
        )