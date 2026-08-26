from fastapi import FastAPI

app = FastAPI(
    title="BidSure AI",
    description="AI-Powered Integrated Bid Compliance Verification Platform",
    version="0.1.0"
)


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