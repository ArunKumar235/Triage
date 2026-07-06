from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from triage.api.deps import get_db, verify_webhook_signature

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health() -> dict:
    """Checks if the service is up and running."""
    return {"status": "ok"}

@router.get("/db")
async def db_health(db : AsyncSession = Depends(get_db)) -> dict:
    """Checks the database connection."""
    checks = {"database": False}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    healthy = all(checks.values())
    return {"status": "ready" if healthy else "degraded", "checks": checks}

@router.get("/webhooks", dependencies=[Depends(verify_webhook_signature)])
async def webhook_health() -> dict:
    """Checks if the webhook signature is valid."""
    return {"status": "ok"}
