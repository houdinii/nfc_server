# app/routers/users.py
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.auth import get_current_user, hash_password, verify_password
from app.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.routers.base import BaseRouter
from app.schemas.user import (
    UserCreate, UserResponse, TokenResponse, UserPreferencesUpdate
)
from app.utils import utc_now


class UserRouter(BaseRouter[User, UserCreate, UserPreferencesUpdate, UserResponse]):
    @property
    def model_class(self):
        return User

    @property
    def create_schema(self):
        return UserCreate

    @property
    def update_schema(self):
        return UserPreferencesUpdate

    @property
    def response_schema(self):
        return UserResponse

    def __init__(self):
        super().__init__(tags=["users"])
        self._setup_user_routes()

    def _setup_user_routes(self):
        """Set up user-specific routes"""

        @self.router.post("/register", response_model=UserResponse)
        async def register(
                user: UserCreate,
                db: Session = Depends(get_db)
        ):
            """Register a new user"""
            # Check if email already exists
            existing = db.query(User).filter(User.email == user.email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Create new user
            new_user = User(
                email=str(user.email),
                hashed_password=hash_password(user.password),
                timezone=user.timezone
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return new_user

        @self.router.post("/login", response_model=TokenResponse)
        async def login(
                form_data: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)
        ):
            """Log in and get access token"""
            # Find user
            user = db.query(User).filter(User.email == form_data.username).first()

            if not user or not verify_password(form_data.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # For MVP, return user ID as token
            # In production, generate proper JWT token
            return TokenResponse(
                access_token=user.id,
                user=UserResponse.model_validate(user)
            )

        @self.router.get("/me", response_model=UserResponse)
        async def get_current_user_info(
                current_user: User = Depends(get_current_user)
        ):
            """Get current user information"""
            return current_user

        @self.router.patch("/me/preferences", response_model=UserResponse)
        async def update_preferences(
                preferences: UserPreferencesUpdate,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            """Update user preferences"""
            # Update only provided preferences
            current_prefs = current_user.preferences.copy()
            for key, value in preferences.model_dump(exclude_unset=True).items():
                if value is not None:
                    current_prefs[key] = value

            current_user.preferences = current_prefs
            db.commit()
            db.refresh(current_user)

            return current_user

        @self.router.post("/me/reset-daily", response_model=Dict[str, str])
        async def reset_daily_tracking(
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            """Emergency reset - end all active activities"""
            # End any active activities
            active_activities = db.query(Activity).filter(
                and_(
                    Activity.user_id == current_user.id,
                    Activity.end_time.is_(None)
                )
            ).all()

            for activity in active_activities:
                activity.end_time = utc_now()
                activity.duration = int(
                    (activity.end_time - activity.start_time).total_seconds()
                )
                activity.notes = (activity.notes or "") + " [Emergency reset]"

            db.commit()

            return {
                "message": "Daily tracking reset successfully",
                "activities_ended": len(active_activities)
            }

        @self.router.delete("/me")
        async def delete_account(
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            """Delete user account and all associated data"""
            db.delete(current_user)
            db.commit()

            return {"message": "Account deleted successfully"}


# Create router instance
user_router = UserRouter()
router = user_router.router
