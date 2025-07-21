# app/routers/tags_refactored.py
"""
Example of how the tags router could be refactored to use the BaseRouter
"""
from datetime import timedelta
from typing import List, Optional
from fastapi import Depends, HTTPException

from app.auth import get_current_user
from app.database import get_db
from app.models.activity import Activity
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate, TagResponse, TagWithStats
from app.utils import utc_now
from app.routers.base import CRUDRouter
from sqlalchemy.orm import Session
from sqlalchemy import and_


class TagRouter(CRUDRouter):
    """
    Tag router using the BaseRouter pattern
    Provides CRUD operations plus custom tag-specific endpoints
    """
    
    @property
    def model_class(self):
        return Tag
    
    @property
    def create_schema(self):
        return TagCreate
    
    @property
    def update_schema(self):
        return TagUpdate
    
    @property
    def response_schema(self):
        return TagResponse
    
    def __init__(self):
        super().__init__(prefix="/tags", tags=["tags"])
        self._setup_custom_routes()
    
    def _setup_custom_routes(self):
        """Setup tag-specific routes beyond basic CRUD"""
        
        @self.router.get("/by-nfc/{nfc_id}", response_model=TagResponse)
        async def get_tag_by_nfc(
            nfc_id: str,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            """Get tag by NFC ID"""
            tag = db.query(Tag).filter(
                and_(Tag.nfc_id == nfc_id, Tag.user_id == current_user.id)
            ).first()

            if not tag:
                raise HTTPException(status_code=404, detail="Tag not found")

            return tag
        
        @self.router.get("/{tag_id}/stats", response_model=TagWithStats)
        async def get_tag_with_stats(
            tag_id: str,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            """Get tag with usage statistics"""
            return await self._get_tag_with_stats(tag_id, current_user, db)
    
    async def create_handler(self, create_data: TagCreate, current_user: User, db: Session) -> Tag:
        """Override create to check for duplicate NFC IDs"""
        # Check if NFC ID already exists for this user
        existing = db.query(Tag).filter(
            and_(Tag.nfc_id == create_data.nfc_id, Tag.user_id == current_user.id)
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Tag already registered")

        return self._create_entity(create_data, current_user, db)
    
    async def _get_tag_with_stats(self, tag_id: str, current_user: User, db: Session) -> TagWithStats:
        """Generate comprehensive tag statistics"""
        tag = self._get_user_entity(tag_id, current_user, db)
        
        # Calculate statistics
        now = utc_now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        # Get activities for this tag
        activities = db.query(Activity).filter(
            and_(
                Activity.tag_id == tag_id,
                Activity.user_id == current_user.id
            )
        ).all()

        # Calculate durations
        total_duration_today = sum(
            a.duration or 0 for a in activities
            if a.start_time >= today_start
        )

        total_duration_week = sum(
            a.duration or 0 for a in activities
            if a.start_time >= week_start
        )

        completed_activities = [a for a in activities if a.duration]
        average_duration = (
            sum(a.duration for a in completed_activities) / len(completed_activities)
            if completed_activities else 0
        )

        # Get transition patterns (simplified)
        transitions_to = {}
        transitions_from = {}

        for activity in activities:
            if activity.previous_activity_id:
                prev = db.query(Activity).filter(Activity.id == activity.previous_activity_id).first()
                if prev:
                    prev_tag = db.query(Tag).filter(Tag.id == prev.tag_id).first()
                    if prev_tag:
                        transitions_from[prev_tag.name] = transitions_from.get(prev_tag.name, 0) + 1

            # Find next activity
            next_activity = db.query(Activity).filter(
                Activity.previous_activity_id == activity.id
            ).first()
            if next_activity:
                next_tag = db.query(Tag).filter(Tag.id == next_activity.tag_id).first()
                if next_tag:
                    transitions_to[next_tag.name] = transitions_to.get(next_tag.name, 0) + 1

        # Peak usage hours
        hour_counts = {}
        for activity in activities:
            hour = activity.start_time.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        peak_hours = sorted(hour_counts.keys(), key=lambda h: hour_counts[h], reverse=True)[:3]

        # Create response
        return TagWithStats(
            **tag.__dict__,
            total_duration_today=total_duration_today,
            total_duration_week=total_duration_week,
            average_session_duration=average_duration,
            common_transitions_to=[
                {"tag": k, "count": v}
                for k, v in sorted(transitions_to.items(), key=lambda x: x[1], reverse=True)[:3]
            ],
            common_transitions_from=[
                {"tag": k, "count": v}
                for k, v in sorted(transitions_from.items(), key=lambda x: x[1], reverse=True)[:3]
            ],
            peak_usage_hours=peak_hours
        )


# Usage:
# tag_router = TagRouter()
# app.include_router(tag_router.router)
