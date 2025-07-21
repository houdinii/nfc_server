# app/models/user.py
from sqlalchemy import Column, String, Boolean, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    # Authentication
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # ADHD-specific preferences
    preferences = Column(JSON, default={
        "reminder_frequency": "medium",  # low, medium, high, off
        "transition_time": 5,  # minutes between activities
        "focus_session_length": 25,  # default pomodoro length
        "break_length": 5,  # minutes
        "hyperfocus_alert_after": 90,  # minutes
        "medication_reminders": True,
        "daily_summary_time": "21:00",
        "weekly_review_day": "Sunday",
        "time_display": "relative",  # relative or absolute
        "notification_style": "gentle",  # gentle, persistent, off
        "theme": "calm"  # calm, energetic, minimal, custom
    })

    # User profile
    timezone = Column(String, default="UTC")
    notification_token = Column(String)  # For push notifications

    # Relationships
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    patterns = relationship("Pattern", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")
    routines = relationship("Routine", back_populates="user", cascade="all, delete-orphan")
    