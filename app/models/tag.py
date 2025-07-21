# app/models/tag.py
from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, Enum, Index, DateTime, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class TagType(enum.Enum):
    WORK = "work"
    BREAK = "break"
    TRANSITION = "transition"
    RESET = "reset"
    MEDICATION = "medication"
    FOCUS = "focus"
    SOCIAL = "social"
    EXERCISE = "exercise"
    MEAL = "meal"
    SLEEP = "sleep"
    HOBBY = "hobby"
    CHORE = "chore"
    APPOINTMENT = "appointment"
    CUSTOM = "custom"


class Tag(BaseModel):
    __tablename__ = "tags"
    __table_args__ = (
        Index('idx_user_nfc', 'user_id', 'nfc_id', unique=True),
    )

    # Identification
    nfc_id = Column(String, nullable=False)  # Physical NFC tag ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Basic properties
    name = Column(String, nullable=False)
    location = Column(String)  # "Office desk", "Kitchen", etc.
    type = Column(Enum(TagType), nullable=False)

    # Visual customization
    color = Column(String, default="#3B82F6")  # Hex color
    icon = Column(String, default="tag")  # Icon identifier
    emoji = Column(String)  # Optional emoji for quick recognition

    # ADHD-specific metadata
    energy_cost = Column(Float, default=0.5)  # 0-1 scale (0=relaxing, 1=exhausting)
    focus_required = Column(Float, default=0.5)  # 0-1 scale (0=mindless, 1=deep focus)
    typical_duration = Column(Integer)  # Expected duration in minutes

    # Behavioral hints
    entry_ritual = Column(String)  # "Take 3 deep breaths"
    exit_ritual = Column(String)  # "Write down where you left off"
    environment_prep = Column(JSON, default=[])  # ["Close other tabs", "Get water"]

    # Advanced features
    is_interruptible = Column(Boolean, default=True)
    requires_medication = Column(Boolean, default=False)
    best_time_of_day = Column(JSON)  # {"start": "09:00", "end": "12:00"}

    # Statistics
    total_scans = Column(Integer, default=0)
    last_scanned = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="tags")
    activities = relationship("Activity", back_populates="tag", cascade="all, delete-orphan")
