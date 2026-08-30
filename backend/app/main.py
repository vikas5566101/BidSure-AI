from fastapi import FastAPI

from backend.app.api.documents import router as documents_router


app = FastAPI(
    title="BidSure AI",
    description="AI-Powered Integrated Bid Compliance Verification Platform",
    version="0.1.0",
)


app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to BidSure AI API"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }