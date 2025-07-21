# app/utils.py
from datetime import datetime, timezone


def utc_now():
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)


def make_aware(dt: datetime) -> datetime:
    """Convert naive datetime to UTC-aware datetime"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
