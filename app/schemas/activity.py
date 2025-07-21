# app/schemas/activity.py
from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class MoodType(str, Enum):
    happy = "happy"
    neutral = "neutral"
    anxious = "anxious"
    frustrated = "frustrated"
    calm = "calm"
    energetic = "energetic"


class ActivityBase(BaseModel):
    tag_id: str
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    focus_level: Optional[int] = Field(None, ge=1, le=5)
    mood_start: Optional[MoodType] = None
    planned: bool = False
    notes: Optional[str] = None
    medication_taken: Optional[bool] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    end_time: Optional[datetime] = None
    energy_level_end: Optional[int] = Field(None, ge=1, le=5)
    focus_level_end: Optional[int] = Field(None, ge=1, le=5)
    mood_end: Optional[MoodType] = None
    completed: Optional[bool] = None
    interrupted: Optional[bool] = None
    perceived_productivity: Optional[int] = Field(None, ge=1, le=5)
    flow_state_achieved: Optional[bool] = None
    medication_effective: Optional[int] = Field(None, ge=1, le=5)
    wins: Optional[List[str]] = None
    challenges: Optional[List[str]] = None


class InterruptionCreate(BaseModel):
    internal: bool = True
    category: Optional[str] = None
    description: Optional[str] = None


class InterruptionEnd(BaseModel):
    resumed: bool
    context_switch_cost: Optional[int] = Field(None, ge=1, le=5)
    coping_strategy: Optional[str] = None


class ActivityResponse(BaseModel):
    id: str
    user_id: str
    tag_id: str
    tag_name: Optional[str] = None
    tag_type: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[int]
    energy_level: Optional[int]
    energy_level_end: Optional[int]
    focus_level: Optional[int]
    focus_level_end: Optional[int]
    mood_start: Optional[str]
    mood_end: Optional[str]
    planned: bool
    completed: bool
    interrupted: bool
    interruption_count: int
    perceived_productivity: Optional[int]
    flow_state_achieved: bool
    hyperfocus_detected: bool
    notes: Optional[str]
    wins: List[str]
    challenges: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityStats(BaseModel):
    total_duration: int
    average_duration: float
    total_activities: int
    completed_activities: int
    interruption_rate: float
    flow_state_rate: float
    average_energy_change: float
    average_focus_change: float
