from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine, get_db

from app.api.routes import (
    bid_documents,
    bid_submissions,
    bidders,
    tenders,
)

# # Create all tables
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.include_router(bidders.router)
app.include_router(tenders.router)
app.include_router(bid_submissions.router)
app.include_router(bid_documents.router)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }

@app.get("/health/database")
def database_health_check(
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected",
    }