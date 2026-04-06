from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db


router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> dict[str, bool | str]:
    db.execute(text("SELECT 1"))
    return {
        "ok": True,
        "message": "FastAPI backend is running",
        "database": "connected",
    }
