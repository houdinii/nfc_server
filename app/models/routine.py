# app/models/routine.py
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, Time, Enum, Float
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class RoutineType(enum.Enum):
    MORNING = "morning"
    EVENING = "evening"
    WORK_START = "work_start"
    WORK_END = "work_end"
    MEDICATION = "medication"
    EXERCISE = "exercise"
    MEAL = "meal"
    CUSTOM = "custom"


class Routine(BaseModel):
    __tablename__ = "routines"

    # Identification
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(RoutineType), nullable=False)

    # Schedule
    time_of_day = Column(Time)  # Preferred time
    days_of_week = Column(JSON, default=[])  # [0-6] for days
    flexible_minutes = Column(Integer, default=30)  # Flexibility window

    # Routine composition
    tag_sequence = Column(JSON, default=[])  # Expected tag sequence
    required_tags = Column(JSON, default=[])  # Must-scan tags
    optional_tags = Column(JSON, default=[])  # Optional tags

    # Tracking
    is_active = Column(Boolean, default=True)
    streak_current = Column(Integer, default=0)
    streak_best = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)

    # ADHD support
    preparation_reminder = Column(Integer, default=10)  # Minutes before
    transition_prompts = Column(JSON, default=[])  # Helpful prompts
    completion_reward = Column(String)  # Motivational message

    # Relationships
    user = relationship("User", back_populates="routines")
