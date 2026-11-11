from fastapi import FastAPI

from app.core.config import settings
from app.routers.address_routes import router as address_router
from app.routers.user_routes import router as user_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.include_router(user_router)
app.include_router(address_router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}