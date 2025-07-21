# app/models/activity.py
from sqlalchemy import Column, String, Integer, Boolean, Text, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Activity(BaseModel):
    __tablename__ = "activities"
    __table_args__ = (
        Index('idx_user_time', 'user_id', 'start_time'),
        Index('idx_tag_time', 'tag_id', 'start_time'),
        Index('idx_user_end', 'user_id', 'end_time'),
    )

    # Foreign keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tag_id = Column(String, ForeignKey("tags.id"), nullable=False)
    previous_activity_id = Column(String, ForeignKey("activities.id"))

    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True))
    duration = Column(Integer)  # Calculated duration in seconds

    # ADHD-specific metrics
    energy_level = Column(Integer)  # 1-5 scale at start
    energy_level_end = Column(Integer)  # 1-5 scale at end
    focus_level = Column(Integer)  # 1-5 scale at start
    focus_level_end = Column(Integer)  # 1-5 scale at end

    # Mood tracking
    mood_start = Column(String)  # happy, neutral, anxious, frustrated, calm, energetic
    mood_end = Column(String)
    mood_notes = Column(Text)

    # Activity quality
    planned = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    interrupted = Column(Boolean, default=False)
    interruption_count = Column(Integer, default=0)
    distraction_count = Column(Integer, default=0)

    # Hyperfocus detection
    hyperfocus_detected = Column(Boolean, default=False)
    hyperfocus_duration = Column(Integer)  # seconds in hyperfocus state

    # Context and environment
    context = Column(JSON, default={})  # Flexible context storage
    environment = Column(JSON, default={})  # noise_level, lighting, temperature, etc.

    # Productivity metrics
    perceived_productivity = Column(Integer)  # 1-5 self-rating
    flow_state_achieved = Column(Boolean, default=False)

    # Notes and reflection
    notes = Column(Text)
    wins = Column(JSON, default=[])  # List of accomplishments
    challenges = Column(JSON, default=[])  # List of difficulties

    # Medication tracking
    medication_taken = Column(Boolean)
    medication_effective = Column(Integer)  # 1-5 effectiveness rating

    # Relationships
    user = relationship("User", back_populates="activities")
    tag = relationship("Tag", back_populates="activities")
    previous_activity = relationship("Activity", remote_side="Activity.id")
    interruptions = relationship("Interruption", back_populates="activity", cascade="all, delete-orphan")
