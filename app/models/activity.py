# app/models/activity.py
from sqlalchemy import Column, String, Integer, Boolean, Text, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.metrics import MetricTracker, ActivityMetricsMixin


class Activity(BaseModel, ActivityMetricsMixin):
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

    # ADHD-specific metrics using MetricTracker
    energy_level = MetricTracker.scale_column("Energy level at start (1-5)")
    energy_level_end = MetricTracker.scale_column("Energy level at end (1-5)")
    focus_level = MetricTracker.scale_column("Focus level at start (1-5)")
    focus_level_end = MetricTracker.scale_column("Focus level at end (1-5)")

    # Mood tracking
    mood_start = MetricTracker.mood_column("Mood at activity start")
    mood_end = MetricTracker.mood_column("Mood at activity end")
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
    perceived_productivity = MetricTracker.scale_column("Perceived productivity (1-5)")
    flow_state_achieved = Column(Boolean, default=False)

    # Notes and reflection
    notes = Column(Text)
    wins = Column(JSON, default=[])  # List of accomplishments
    challenges = Column(JSON, default=[])  # List of difficulties

    # Medication tracking
    medication_taken = Column(Boolean)
    medication_effective = MetricTracker.scale_column("Medication effectiveness (1-5)")

    # Relationships
    user = relationship("User", back_populates="activities")
    tag = relationship("Tag", back_populates="activities")
    previous_activity = relationship("Activity", remote_side="Activity.id")
    interruptions = relationship("Interruption", back_populates="activity", cascade="all, delete-orphan")
