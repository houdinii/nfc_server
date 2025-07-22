# app/models/metrics.py
from typing import Optional
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import validates
from enum import Enum


class MoodType(str, Enum):
    """Valid mood values for the Activity model"""
    HAPPY = "happy"
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    CALM = "calm"
    ENERGETIC = "energetic"


class MetricTracker:
    """
    Base class for activity metrics that provides validation
    and column creation for the Activity model.
    """

    @staticmethod
    def scale_column(comment: str) -> Column:
        """Create a 1-5 scale integer column"""
        return Column(Integer, nullable=True, comment=comment)

    @staticmethod
    def mood_column(comment: str) -> Column:
        """Create a mood string column"""
        return Column(String, nullable=True, comment=comment)

    @staticmethod
    def validate_scale(value: Optional[int], field_name: str) -> Optional[int]:
        """Validate a 1-5 scale value"""
        if value is not None and not (1 <= value <= 5):
            raise ValueError(f"{field_name} must be between 1 and 5")
        return value

    @staticmethod
    def validate_mood(value: Optional[str]) -> Optional[str]:
        """Validate a mood value"""
        if value is not None and value not in [m.value for m in MoodType]:
            valid_moods = ", ".join([m.value for m in MoodType])
            raise ValueError(f"Mood must be one of: {valid_moods}")
        return value


# Mixin for Activity model to add metric validation
class ActivityMetricsMixin:
    """
    Mixin that adds metric validation to the Activity model.
    This extracts the common validation patterns for metrics.
    """

    @validates('energy_level', 'energy_level_end',
               'focus_level', 'focus_level_end',
               'perceived_productivity', 'medication_effective')
    def validate_scale_metric(self, key, value):
        """Validate all 1-5 scale metrics"""
        return MetricTracker.validate_scale(value, key)

    @validates('mood_start', 'mood_end')
    def validate_mood_metric(self, key, value):
        """Validate mood values"""
        return MetricTracker.validate_mood(value)
