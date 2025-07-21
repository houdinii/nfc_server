# app/routers/patterns.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/")
async def get_patterns(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get user patterns - placeholder"""
    return {
        "message": "Patterns endpoint - coming soon",
        "user_id": current_user.id
    }


# noinspection PyUnusedLocal
@router.get("/detect")
async def detect_patterns(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Detect patterns - placeholder"""
    return {
        "message": "Pattern detection - coming soon",
        "patterns_found": 0
    }
