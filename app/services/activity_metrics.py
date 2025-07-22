# app/services/activity_metrics.py
"""
Simple service to calculate metrics from Activity data
"""
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.user import User


class ActivityMetricsService:
    """Simple service to query and calculate metrics from activity data."""

    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db

    def get_daily_metrics(self, date: datetime) -> Dict:
        """Get metric averages for a specific day"""
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # Query activities for the day
        activities = self.db.query(Activity).filter(
            and_(
                Activity.user_id == self.user.id,
                Activity.start_time >= day_start,
                Activity.start_time < day_end
            )
        ).all()

        if not activities:
            return {
                "date": date.date().isoformat(),
                "total_activities": 0,
                "total_duration": 0,
                "avg_energy": None,
                "avg_focus": None,
                "avg_productivity": None,
                "mood_counts": {}
            }

        # Calculate averages
        energy_values = [a.energy_level for a in activities if a.energy_level]
        focus_values = [a.focus_level for a in activities if a.focus_level]
        productivity_values = [a.perceived_productivity for a in activities
                               if a.perceived_productivity and a.end_time]

        # Count moods
        mood_counts = {}
        for activity in activities:
            if activity.mood_start:
                mood_counts[activity.mood_start] = mood_counts.get(activity.mood_start, 0) + 1

        total_duration = sum(a.duration or 0 for a in activities)

        return {
            "date": date.date().isoformat(),
            "total_activities": len(activities),
            "total_duration": total_duration,
            "avg_energy": sum(energy_values) / len(energy_values) if energy_values else None,
            "avg_focus": sum(focus_values) / len(focus_values) if focus_values else None,
            "avg_productivity": sum(productivity_values) / len(productivity_values) if productivity_values else None,
            "mood_counts": mood_counts
        }

    def get_weekly_metrics(self, week_start: datetime) -> Dict:
        """Get metric averages for a week"""
        week_end = week_start + timedelta(days=7)

        # Use database aggregation for efficiency
        result = self.db.query(
            func.count(Activity.id).label('count'),
            func.sum(Activity.duration).label('total_duration'),
            func.avg(Activity.energy_level).label('avg_energy'),
            func.avg(Activity.focus_level).label('avg_focus'),
            func.avg(Activity.perceived_productivity).label('avg_productivity')
        ).filter(
            and_(
                Activity.user_id == self.user.id,
                Activity.start_time >= week_start,
                Activity.start_time < week_end
            )
        ).first()

        return {
            "week_start": week_start.date().isoformat(),
            "week_end": (week_end - timedelta(days=1)).date().isoformat(),
            "total_activities": result.count or 0,
            "total_duration": result.total_duration or 0,
            "avg_energy": float(result.avg_energy) if result.avg_energy else None,
            "avg_focus": float(result.avg_focus) if result.avg_focus else None,
            "avg_productivity": float(result.avg_productivity) if result.avg_productivity else None
        }

    def get_energy_changes(self, days: int = 30) -> Dict:
        """Calculate average energy changes during activities"""
        cutoff = datetime.now() - timedelta(days=days)

        # Get completed activities with both energy values
        activities = self.db.query(Activity).filter(
            and_(
                Activity.user_id == self.user.id,
                Activity.start_time >= cutoff,
                Activity.energy_level.isnot(None),
                Activity.energy_level_end.isnot(None),
                Activity.end_time.isnot(None)
            )
        ).all()

        if not activities:
            return {"message": "No energy data available"}

        changes = [a.energy_level_end - a.energy_level for a in activities]
        avg_change = sum(changes) / len(changes)

        return {
            "period_days": days,
            "activities_analyzed": len(activities),
            "average_energy_change": avg_change,
            "energy_gains": len([c for c in changes if c > 0]),
            "energy_losses": len([c for c in changes if c < 0]),
            "energy_stable": len([c for c in changes if c == 0])
        }

    def get_productivity_by_time(self, days: int = 30) -> Dict:
        """Get average productivity by hour of day"""
        cutoff = datetime.now() - timedelta(days=days)

        # Query productivity by hour
        hourly_data = {}

        activities = self.db.query(
            Activity.start_time,
            Activity.perceived_productivity
        ).filter(
            and_(
                Activity.user_id == self.user.id,
                Activity.start_time >= cutoff,
                Activity.perceived_productivity.isnot(None)
            )
        ).all()

        # Group by hour
        for activity in activities:
            hour = activity.start_time.hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(activity.perceived_productivity)

        # Calculate averages
        hourly_averages = {}
        for hour, values in hourly_data.items():
            if len(values) >= 3:  # Need at least 3 data points
                hourly_averages[hour] = sum(values) / len(values)

        # Find best hours
        sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)

        return {
            "period_days": days,
            "hourly_averages": hourly_averages,
            "best_hours": [h for h, _ in sorted_hours[:3]],
            "worst_hours": [h for h, _ in sorted_hours[-3:]] if len(sorted_hours) >= 3 else []
        }

    def get_tag_metrics(self, tag_id: str, days: int = 30) -> Dict:
        """Get metrics for a specific tag/activity type"""
        cutoff = datetime.now() - timedelta(days=days)

        activities = self.db.query(Activity).filter(
            and_(
                Activity.user_id == self.user.id,
                Activity.tag_id == tag_id,
                Activity.start_time >= cutoff
            )
        ).all()

        if not activities:
            return {"message": "No activities found for this tag"}

        # Calculate metrics
        completed = [a for a in activities if a.completed]
        interrupted = [a for a in activities if a.interrupted]

        energy_values = [a.energy_level for a in activities if a.energy_level]
        focus_values = [a.focus_level for a in activities if a.focus_level]
        productivity_values = [a.perceived_productivity for a in activities
                               if a.perceived_productivity]

        return {
            "tag_id": tag_id,
            "period_days": days,
            "total_activities": len(activities),
            "completion_rate": len(completed) / len(activities) if activities else 0,
            "interruption_rate": len(interrupted) / len(activities) if activities else 0,
            "avg_energy": sum(energy_values) / len(energy_values) if energy_values else None,
            "avg_focus": sum(focus_values) / len(focus_values) if focus_values else None,
            "avg_productivity": sum(productivity_values) / len(productivity_values) if productivity_values else None
        }
