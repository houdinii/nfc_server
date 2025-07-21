# app/routers/tags.py
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.activity import Activity
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate, TagResponse, TagWithStats
from app.utils import utc_now

router = APIRouter()


@router.post("/", response_model=TagResponse)
async def create_tag(
        tag: TagCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create a new NFC tag registration"""

    # Check if NFC ID already exists for this user
    existing = db.query(Tag).filter(
        and_(Tag.nfc_id == tag.nfc_id, Tag.user_id == current_user.id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Tag already registered")

    new_tag = Tag(
        user_id=current_user.id,
        **tag.model_dump()
    )

    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)

    return new_tag


@router.get("/", response_model=List[TagResponse])
async def get_tags(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all tags for the current user"""

    tags = db.query(Tag).filter(Tag.user_id == current_user.id).all()
    return tags


@router.get("/by-nfc/{nfc_id}", response_model=TagResponse)
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


@router.get("/{tag_id}", response_model=TagWithStats)
async def get_tag_with_stats(
        tag_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get tag with usage statistics"""

    tag = db.query(Tag).filter(
        and_(Tag.id == tag_id, Tag.user_id == current_user.id)
    ).first()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

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
    response = TagWithStats(
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

    return response


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
        tag_id: str,
        update: TagUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update tag properties"""

    tag = db.query(Tag).filter(
        and_(Tag.id == tag_id, Tag.user_id == current_user.id)
    ).first()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Update fields
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)

    return tag


@router.delete("/{tag_id}")
async def delete_tag(
        tag_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Delete a tag and all associated activities"""

    tag = db.query(Tag).filter(
        and_(Tag.id == tag_id, Tag.user_id == current_user.id)
    ).first()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()

    return {"message": "Tag deleted successfully"}
