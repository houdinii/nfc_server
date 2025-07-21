# app/routers/insights.py
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/")
async def get_insights(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get user insights - placeholder"""
    return {
        "message": "Insights endpoint - coming soon",
        "user_id": current_user.id
    }


# noinspection PyUnusedLocal
@router.get("/daily")
async def get_daily_insights(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get daily insights - placeholder"""
    return {
        "message": "Daily insights - coming soon",
        "date": datetime.now().date().isoformat()
    }
