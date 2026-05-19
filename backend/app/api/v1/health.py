from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.infrastructure.database.connection import get_db_session

router = APIRouter(tags=["health"])


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str
    database: str


@router.get("/health", response_model=HealthStatus)
async def health_check(
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db_session),
) -> HealthStatus:
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    return HealthStatus(
        status="ok",
        version="0.1.0",
        environment=settings.environment,
        database=db_status,
    )


@router.get("/health/liveness")
async def liveness() -> dict[str, str]:
    """Kubernetes liveness probe — does not check dependencies."""
    return {"status": "ok"}
