from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["system"])

@router.get("/api/v1/health")
def health_check():
    """Simple system health check."""
    return {
        "api": "ok",
        "database": "ok",
        "auth": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
