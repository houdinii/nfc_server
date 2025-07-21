# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    timezone: str = "UTC"


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPreferencesUpdate(BaseModel):
    reminder_frequency: Optional[str] = None
    transition_time: Optional[int] = None
    focus_session_length: Optional[int] = None
    break_length: Optional[int] = None
    hyperfocus_alert_after: Optional[int] = None
    medication_reminders: Optional[bool] = None
    daily_summary_time: Optional[str] = None
    weekly_review_day: Optional[str] = None
    time_display: Optional[str] = None
    notification_style: Optional[str] = None
    theme: Optional[str] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    preferences: Dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
