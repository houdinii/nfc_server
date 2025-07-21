# app/models/pattern.py
from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class PatternType(enum.Enum):
    DAILY_ROUTINE = "daily_routine"
    WEEKLY_ROUTINE = "weekly_routine"
    DISTRACTION_LOOP = "distraction_loop"
    PRODUCTIVE_FLOW = "productive_flow"
    TRANSITION_DIFFICULTY = "transition_difficulty"
    HYPERFOCUS_TRIGGER = "hyperfocus_trigger"
    ENERGY_PATTERN = "energy_pattern"
    FOCUS_PATTERN = "focus_pattern"
    MEDICATION_IMPACT = "medication_impact"
    BREAK_PATTERN = "break_pattern"
    PROCRASTINATION = "procrastination"
    MOMENTUM_BUILDER = "momentum_builder"


class Pattern(BaseModel):
    __tablename__ = "patterns"

    # Identification
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(PatternType), nullable=False)
    name = Column(String)  # Human-readable pattern name

    # Pattern details
    sequence = Column(JSON)  # Tag sequences, time patterns, etc.
    conditions = Column(JSON)  # Conditions when pattern occurs
    triggers = Column(JSON, default=[])  # What triggers this pattern

    # Statistical measures
    confidence = Column(Float)  # 0-1 confidence score
    support = Column(Float)  # How often this pattern appears
    occurrences = Column(Integer, default=1)
    last_seen = Column(DateTime(timezone=True))

    # Pattern characteristics
    is_positive = Column(Boolean)  # Beneficial or detrimental
    impact_score = Column(Float)  # -1 to 1 impact on productivity

    # Time characteristics
    typical_duration = Column(Integer)  # seconds
    time_of_day_preference = Column(JSON)  # Hours when pattern occurs
    day_of_week_preference = Column(JSON)  # Days when pattern occurs

    # ADHD-specific insights
    energy_impact = Column(Float)  # How it affects energy
    focus_impact = Column(Float)  # How it affects focus
    medication_correlation = Column(Float)  # Correlation with medication

    # Actionable data
    interventions = Column(JSON, default=[])  # Suggested interventions
    success_strategies = Column(JSON, default=[])  # What has worked

    # Relationships
    user = relationship("User", back_populates="patterns")
