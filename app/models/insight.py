# app/models/insight.py
import enum

from sqlalchemy import Column, String, Text, Float, Boolean, JSON, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class InsightType(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    PATTERN_BASED = "pattern_based"
    ACHIEVEMENT = "achievement"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    MILESTONE = "milestone"
    TREND = "trend"


class InsightPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Insight(BaseModel):
    __tablename__ = "insights"

    # Identification
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    pattern_id = Column(String, ForeignKey("patterns.id"))

    # Insight properties
    type = Column(Enum(InsightType), nullable=False)
    priority = Column(Enum(InsightPriority), default=InsightPriority.MEDIUM)

    # Content
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default={})

    # Actionable elements
    actions = Column(JSON, default=[])  # Suggested actions
    quick_actions = Column(JSON, default=[])  # One-tap actions

    # Validity
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))

    # User interaction
    viewed = Column(Boolean, default=False)
    viewed_at = Column(DateTime(timezone=True))
    dismissed = Column(Boolean, default=False)
    helpful = Column(Boolean)  # User feedback

    # Impact tracking
    expected_impact = Column(Float)  # Predicted improvement
    actual_impact = Column(Float)  # Measured improvement

    # Relationships
    user = relationship("User", back_populates="insights")
    pattern = relationship("Pattern")
