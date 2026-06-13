from fastapi import FastAPI
from app.core.config import settings
from app.routers import projects, members

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Includes the routers
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(members.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}
