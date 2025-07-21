# app/routers/routines.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter()


# noinspection PyUnusedLocal
@router.get("/")
async def get_routines(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get user routines - placeholder"""
    return {
        "message": "Routines endpoint - coming soon",
        "user_id": current_user.id
    }


# noinspection PyUnusedLocal
@router.post("/")
async def create_routine(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create routine - placeholder"""
    return {
        "message": "Routine creation - coming soon",
        "user_id": current_user.id
    }
