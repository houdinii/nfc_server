# app/routers/activities.py
from typing import List, Optional, Dict

from fastapi import Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.activity import Activity
from app.models.interruption import Interruption
from app.models.tag import Tag
from app.models.user import User
from app.routers.base import CRUDRouter
from app.schemas.activity import (
    ActivityCreate, ActivityUpdate, ActivityResponse,
    InterruptionCreate, ActivityStats
)
from app.utils import utc_now, make_aware


class ActivityRouter(CRUDRouter[Activity, ActivityCreate, ActivityUpdate, ActivityResponse]):
    @property
    def model_class(self):
        return Activity

    @property
    def create_schema(self):
        return ActivityCreate

    @property
    def update_schema(self):
        return ActivityUpdate

    @property
    def response_schema(self):
        return ActivityResponse

    def __init__(self):
        super().__init__(tags=["activities"])
        self._setup_custom_routes()

    def _setup_custom_routes(self):
        """Setup activity-specific routes beyond basic CRUD"""

        @self.router.get("/current", response_model=Optional[ActivityResponse])
        async def get_current_activity(
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            """Get the current active activity"""
            activity = db.query(Activity).filter(
                and_(
                    Activity.user_id == current_user.id,
                    Activity.end_time.is_(None)
                )
            ).first()

            if not activity:
                return None

            # Add tag info
            tag = db.query(Tag).filter(Tag.id == activity.tag_id).first()
            response = ActivityResponse.model_validate(activity)
            response.tag_name = tag.name
            response.tag_type = tag.type.value

            return response

        @self.router.post("/{activity_id}/interrupt", response_model=Dict[str, str])
        async def add_interruption(
                activity_id: str,
                interruption: InterruptionCreate,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            """Record an interruption"""
            activity = self._get_user_entity(activity_id, current_user, db)

            # Create interruption
            new_interruption = Interruption(
                activity_id=activity_id,
                timestamp=utc_now(),
                **interruption.model_dump()
            )

            # Update activity
            activity.interrupted = True
            activity.interruption_count += 1

            db.add(new_interruption)
            db.commit()

            return {"interruption_id": new_interruption.id, "message": "Interruption recorded"}

        @self.router.get("/{activity_id}/stats", response_model=ActivityStats)
        async def get_activity_stats(
                activity_id: str,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            """Get statistics for a specific activity type"""
            # Get the activity to find its tag
            activity = self._get_user_entity(activity_id, current_user, db)

            # Get all activities with the same tag
            activities = db.query(Activity).filter(
                and_(
                    Activity.user_id == current_user.id,
                    Activity.tag_id == activity.tag_id,
                    Activity.duration.isnot(None)
                )
            ).all()

            if not activities:
                return ActivityStats(
                    total_duration=0,
                    average_duration=0,
                    total_activities=0,
                    completed_activities=0,
                    interruption_rate=0,
                    flow_state_rate=0,
                    average_energy_change=0,
                    average_focus_change=0
                )

            # Calculate stats
            total_duration = sum(a.duration for a in activities if a.duration)
            completed = len([a for a in activities if a.completed])
            interrupted = len([a for a in activities if a.interrupted])
            flow_states = len([a for a in activities if a.flow_state_achieved])

            # Energy and focus changes
            energy_changes = []
            focus_changes = []
            for a in activities:
                if a.energy_level and a.energy_level_end:
                    energy_changes.append(a.energy_level_end - a.energy_level)
                if a.focus_level and a.focus_level_end:
                    focus_changes.append(a.focus_level_end - a.focus_level)

            return ActivityStats(
                total_duration=total_duration,
                average_duration=total_duration / len(activities) if activities else 0,
                total_activities=len(activities),
                completed_activities=completed,
                interruption_rate=interrupted / len(activities) if activities else 0,
                flow_state_rate=flow_states / len(activities) if activities else 0,
                average_energy_change=sum(energy_changes) / len(energy_changes) if energy_changes else 0,
                average_focus_change=sum(focus_changes) / len(focus_changes) if focus_changes else 0
            )

    async def create_handler(self, create_data: ActivityCreate, current_user: User, db: Session) -> ActivityResponse:
        """Override to handle tag validation and activity transitions"""
        # Verify tag belongs to user
        tag = db.query(Tag).filter(
            and_(Tag.id == create_data.tag_id, Tag.user_id == current_user.id)
        ).first()

        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        # End any current activity
        current_activity = db.query(Activity).filter(
            and_(
                Activity.user_id == current_user.id,
                Activity.end_time.is_(None)
            )
        ).first()

        if current_activity:
            current_activity.end_time = utc_now()
            current_activity.duration = int(
                (current_activity.end_time - make_aware(current_activity.start_time)).total_seconds()
            )

        # Create new activity
        new_activity = Activity(
            user_id=current_user.id,
            tag_id=str(tag.id),
            start_time=utc_now(),
            previous_activity_id=str(current_activity.id) if current_activity else None,
            **create_data.model_dump(exclude={'tag_id'})
        )

        # Update tag stats
        tag.total_scans += 1
        tag.last_scanned = utc_now()

        db.add(new_activity)
        db.commit()
        db.refresh(new_activity)

        # Add tag info to response
        response = ActivityResponse.model_validate(new_activity)
        response.tag_name = str(tag.name) if tag.name else None
        response.tag_type = tag.type.value

        return response

    async def update_handler(self, entity_id: str, update_data: ActivityUpdate, current_user: User, db: Session) -> ActivityResponse:
        """Override to handle duration calculation and hyperfocus detection"""
        activity = self._get_user_entity(entity_id, current_user, db)

        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(activity, field, value)

        # Calculate duration if ending
        if update_data.end_time and not activity.end_time:
            activity.end_time = update_data.end_time or utc_now()
            activity.duration = int(
                (activity.end_time - make_aware(activity.start_time)).total_seconds()
            )

            # Detect hyperfocus (activity > 90 minutes without interruption)
            if activity.duration > 5400 and activity.interruption_count == 0:
                activity.hyperfocus_detected = True
                activity.hyperfocus_duration = activity.duration

        db.commit()
        db.refresh(activity)

        # Add tag info
        tag = db.query(Tag).filter(Tag.id == activity.tag_id).first()
        response = ActivityResponse.model_validate(activity)
        response.tag_name = tag.name
        response.tag_type = tag.type.value

        return response

    async def list_handler(self, current_user: User, db: Session) -> List[ActivityResponse]:
        """Override to add filtering and tag info"""
        # This is simplified - in production you'd parse query params
        activities = self._get_user_entities(current_user, db)

        # Add tag info to each activity
        responses = []
        for activity in activities:
            tag = db.query(Tag).filter(Tag.id == activity.tag_id).first()
            response = ActivityResponse.model_validate(activity)
            response.tag_name = tag.name
            response.tag_type = tag.type.value
            responses.append(response)

        return responses


# Create router instance
activity_router = ActivityRouter()
router = activity_router.router
