from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.metrics import render_metrics
from app.db.session import SessionLocal

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "running",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/db")
def database_health_check():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/metrics")
def metrics():
    return render_metrics()
