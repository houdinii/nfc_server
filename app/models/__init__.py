# app/models/__init__.py
# Import all models here to ensure they're loaded in the correct order
# This prevents circular import issues with SQLAlchemy relationships

from app.models.base import Base, BaseModel
from app.models.user import User
from app.models.tag import Tag, TagType
from app.models.pattern import Pattern, PatternType
from app.models.activity import Activity
from app.models.interruption import Interruption
from app.models.insight import Insight, InsightType, InsightPriority
from app.models.routine import Routine, RoutineType

# This ensures all models are imported when the models package is imported
__all__ = [
    "Base",
    "BaseModel",
    "User",
    "Tag",
    "TagType",
    "Pattern",
    "PatternType",
    "Activity",
    "Interruption",
    "Insight",
    "InsightType",
    "InsightPriority",
    "Routine",
    "RoutineType"
]
