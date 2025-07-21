# app/schemas/tag.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.tag import TagType


class TagBase(BaseModel):
    name: str
    location: Optional[str] = None
    type: TagType
    color: str = "#3B82F6"
    icon: str = "tag"
    emoji: Optional[str] = None
    energy_cost: float = Field(0.5, ge=0, le=1)
    focus_required: float = Field(0.5, ge=0, le=1)
    typical_duration: Optional[int] = None
    entry_ritual: Optional[str] = None
    exit_ritual: Optional[str] = None
    environment_prep: List[str] = []
    is_interruptible: bool = True
    requires_medication: bool = False


class TagCreate(TagBase):
    nfc_id: str


class TagUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    type: Optional[TagType] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    emoji: Optional[str] = None
    energy_cost: Optional[float] = Field(None, ge=0, le=1)
    focus_required: Optional[float] = Field(None, ge=0, le=1)
    typical_duration: Optional[int] = None
    entry_ritual: Optional[str] = None
    exit_ritual: Optional[str] = None
    environment_prep: Optional[List[str]] = None
    is_interruptible: Optional[bool] = None
    requires_medication: Optional[bool] = None


class TagResponse(TagBase):
    id: str
    nfc_id: str
    user_id: str
    total_scans: int
    last_scanned: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagWithStats(TagResponse):
    total_duration_today: int
    total_duration_week: int
    average_session_duration: float
    common_transitions_to: List[Dict[str, Any]]
    common_transitions_from: List[Dict[str, Any]]
    peak_usage_hours: List[int]
