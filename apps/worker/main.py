from fastapi import FastAPI
from app.routers import ingest

app = FastAPI(title="OmniMind v2 Worker")

app.include_router(ingest.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
