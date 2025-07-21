# app/models/interruption.py
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Interruption(BaseModel):
    __tablename__ = "interruptions"

    # Foreign keys
    activity_id = Column(String, ForeignKey("activities.id"), nullable=False)

    # Interruption details
    timestamp = Column(DateTime(timezone=True), nullable=False)
    duration = Column(Integer)  # seconds if resumed

    # Type and source
    internal = Column(Boolean, default=True)  # Internal vs external
    category = Column(String)  # phone, person, thought, bathroom, etc.
    description = Column(Text)

    # Impact
    resumed = Column(Boolean, default=False)
    resume_time = Column(DateTime(timezone=True))
    context_switch_cost = Column(Integer)  # Perceived cost 1-5

    # Coping
    coping_strategy = Column(String)  # What helped get back on track

    # Relationships
    activity = relationship("Activity", back_populates="interruptions")
