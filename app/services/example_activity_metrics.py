# app/services/activity_metrics.py
"""
Example of how to integrate MetricTracker classes with Activity tracking
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.user import User
from app.metrics.base import (
    EnergyTracker, FocusTracker, MoodTracker, ProductivityTracker,
    MetricEntry, MetricSummary
)


class ActivityMetricsService:
    """
    Service class that integrates metric tracking with activities
    Provides methods to analyze user patterns and generate insights
    """
    
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db
        
        # Initialize metric trackers
        self.energy_tracker = EnergyTracker()
        self.focus_tracker = FocusTracker()
        self.mood_tracker = MoodTracker()
        self.productivity_tracker = ProductivityTracker()
        
        # Load historical data
        self._load_historical_metrics()
    
    def _load_historical_metrics(self):
        """Load historical activity data into metric trackers"""
        activities = self.db.query(Activity).filter(
            Activity.user_id == self.user.id
        ).order_by(Activity.start_time).all()
        
        for activity in activities:
            # Load start metrics
            if activity.energy_level:
                self.energy_tracker.add_entry(
                    activity.energy_level,
                    activity.start_time,
                    context={"activity_id": activity.id, "phase": "start"}
                )
            
            if activity.focus_level:
                self.focus_tracker.add_entry(
                    activity.focus_level,
                    activity.start_time,
                    context={"activity_id": activity.id, "phase": "start"}
                )
            
            if activity.mood_start:
                self.mood_tracker.add_entry(
                    activity.mood_start,
                    activity.start_time,
                    context={"activity_id": activity.id, "phase": "start"}
                )
            
            # Load end metrics (if activity is completed)
            if activity.end_time:
                if activity.energy_level_end:
                    self.energy_tracker.add_entry(
                        activity.energy_level_end,
                        activity.end_time,
                        context={"activity_id": activity.id, "phase": "end"}
                    )
                
                if activity.focus_level_end:
                    self.focus_tracker.add_entry(
                        activity.focus_level_end,
                        activity.end_time,
                        context={"activity_id": activity.id, "phase": "end"}
                    )
                
                if activity.mood_end:
                    self.mood_tracker.add_entry(
                        activity.mood_end,
                        activity.end_time,
                        context={"activity_id": activity.id, "phase": "end"}
                    )
                
                if activity.perceived_productivity:
                    self.productivity_tracker.add_entry(
                        activity.perceived_productivity,
                        activity.end_time,
                        context={"activity_id": activity.id, "duration": activity.duration}
                    )
    
    def record_activity_start(
        self,
        activity_id: str,
        energy_level: Optional[int] = None,
        focus_level: Optional[int] = None,
        mood: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        """Record metrics at the start of an activity"""
        timestamp = timestamp or datetime.now()
        context = {"activity_id": activity_id, "phase": "start"}
        
        if energy_level:
            self.energy_tracker.add_entry(energy_level, timestamp, context)
        
        if focus_level:
            self.focus_tracker.add_entry(focus_level, timestamp, context)
        
        if mood:
            self.mood_tracker.add_entry(mood, timestamp, context)
    
    def record_activity_end(
        self,
        activity_id: str,
        energy_level_end: Optional[int] = None,
        focus_level_end: Optional[int] = None,
        mood_end: Optional[str] = None,
        productivity: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ):
        """Record metrics at the end of an activity"""
        timestamp = timestamp or datetime.now()
        context = {
            "activity_id": activity_id, 
            "phase": "end",
            "duration": duration_seconds
        }
        
        if energy_level_end:
            self.energy_tracker.add_entry(energy_level_end, timestamp, context)
        
        if focus_level_end:
            self.focus_tracker.add_entry(focus_level_end, timestamp, context)
        
        if mood_end:
            self.mood_tracker.add_entry(mood_end, timestamp, context)
        
        if productivity:
            self.productivity_tracker.add_entry(productivity, timestamp, context)
    
    def get_daily_summary(self, date: datetime) -> Dict[str, MetricSummary]:
        """Get metric summaries for a specific day"""
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        return {
            "energy": self.energy_tracker.get_summary(day_start, day_end),
            "focus": self.focus_tracker.get_summary(day_start, day_end),
            "mood": self.mood_tracker.get_summary(day_start, day_end),
            "productivity": self.productivity_tracker.get_summary(day_start, day_end)
        }
    
    def get_weekly_summary(self, week_start: datetime) -> Dict[str, MetricSummary]:
        """Get metric summaries for a week"""
        week_end = week_start + timedelta(days=7)
        
        return {
            "energy": self.energy_tracker.get_summary(week_start, week_end),
            "focus": self.focus_tracker.get_summary(week_start, week_end),
            "mood": self.mood_tracker.get_summary(week_start, week_end),
            "productivity": self.productivity_tracker.get_summary(week_start, week_end)
        }
    
    def analyze_correlations(self) -> Dict[str, Dict[str, any]]:
        """Analyze correlations between different metrics"""
        return {
            "energy_focus": self.energy_tracker.find_correlations(self.focus_tracker),
            "energy_productivity": self.energy_tracker.find_correlations(self.productivity_tracker),
            "focus_productivity": self.focus_tracker.find_correlations(self.productivity_tracker),
            "energy_mood": self.energy_tracker.find_correlations(self.mood_tracker),
            "focus_mood": self.focus_tracker.find_correlations(self.mood_tracker)
        }
    
    def get_optimal_times(self) -> Dict[str, List[int]]:
        """Find optimal times for different metrics based on historical data"""
        # Get last 30 days of data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        energy_entries = self.energy_tracker.get_entries_in_range(start_time, end_time)
        focus_entries = self.focus_tracker.get_entries_in_range(start_time, end_time)
        productivity_entries = self.productivity_tracker.get_entries_in_range(start_time, end_time)
        
        # Group by hour and calculate averages
        def get_hourly_averages(entries):
            hourly_data = {}
            for entry in entries:
                if isinstance(entry.value, (int, float)):
                    hour = entry.timestamp.hour
                    if hour not in hourly_data:
                        hourly_data[hour] = []
                    hourly_data[hour].append(float(entry.value))
            
            hourly_averages = {
                hour: sum(values) / len(values)
                for hour, values in hourly_data.items()
                if len(values) >= 3  # Need at least 3 data points
            }
            
            # Return top 3 hours
            return sorted(hourly_averages.keys(), 
                         key=lambda h: hourly_averages[h], 
                         reverse=True)[:3]
        
        return {
            "high_energy_hours": get_hourly_averages(energy_entries),
            "high_focus_hours": get_hourly_averages(focus_entries),
            "high_productivity_hours": get_hourly_averages(productivity_entries)
        }
    
    def get_mood_patterns(self) -> Dict[str, any]:
        """Analyze mood patterns and triggers"""
        # Get last 30 days
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        mood_distribution = self.mood_tracker.get_mood_distribution(start_time, end_time)
        
        # Analyze day-of-week patterns
        mood_entries = self.mood_tracker.get_entries_in_range(start_time, end_time)
        weekday_moods = {}
        
        for entry in mood_entries:
            weekday = entry.timestamp.strftime("%A")
            if weekday not in weekday_moods:
                weekday_moods[weekday] = []
            weekday_moods[weekday].append(entry.value)
        
        # Find most common mood per weekday
        weekday_patterns = {}
        for weekday, moods in weekday_moods.items():
            mood_counts = {}
            for mood in moods:
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
            if mood_counts:
                weekday_patterns[weekday] = max(mood_counts.keys(), 
                                              key=lambda m: mood_counts[m])
        
        return {
            "overall_distribution": mood_distribution,
            "weekday_patterns": weekday_patterns,
            "total_mood_entries": len(mood_entries)
        }
    
    def get_energy_depletion_patterns(self) -> Dict[str, any]:
        """Analyze how energy changes throughout activities"""
        energy_changes = []
        
        for entry in self.energy_tracker.entries:
            context = entry.context or {}
            if context.get("phase") == "start":
                # Find corresponding end entry for same activity
                activity_id = context.get("activity_id")
                if activity_id:
                    end_entries = [
                        e for e in self.energy_tracker.entries
                        if (e.context or {}).get("activity_id") == activity_id 
                        and (e.context or {}).get("phase") == "end"
                    ]
                    
                    if end_entries:
                        end_entry = end_entries[0]  # Take first match
                        change = float(end_entry.value) - float(entry.value)
                        duration = (end_entry.context or {}).get("duration", 0)
                        
                        energy_changes.append({
                            "start_energy": float(entry.value),
                            "end_energy": float(end_entry.value),
                            "change": change,
                            "duration_minutes": duration / 60 if duration else 0,
                            "activity_id": activity_id
                        })
        
        if not energy_changes:
            return {"message": "No complete energy change data available"}
        
        # Calculate patterns
        avg_change = sum(c["change"] for c in energy_changes) / len(energy_changes)
        
        # Group by starting energy level
        by_start_level = {}
        for change in energy_changes:
            level = int(change["start_energy"])
            if level not in by_start_level:
                by_start_level[level] = []
            by_start_level[level].append(change["change"])
        
        level_patterns = {
            level: {
                "average_change": sum(changes) / len(changes),
                "sample_size": len(changes)
            }
            for level, changes in by_start_level.items()
        }
        
        return {
            "overall_average_change": avg_change,
            "by_starting_energy_level": level_patterns,
            "total_activities_analyzed": len(energy_changes),
            "activities_with_energy_gain": len([c for c in energy_changes if c["change"] > 0]),
            "activities_with_energy_loss": len([c for c in energy_changes if c["change"] < 0])
        }


# Example usage:
"""
# In an activity endpoint or service
def track_activity_metrics(user: User, db: Session):
    metrics_service = ActivityMetricsService(user, db)
    
    # Record start of new activity
    metrics_service.record_activity_start(
        activity_id="123",
        energy_level=4,
        focus_level=3,
        mood="calm"
    )
    
    # Later, record end of activity
    metrics_service.record_activity_end(
        activity_id="123",
        energy_level_end=2,
        focus_level_end=4,
        mood_end="focused",
        productivity=4,
        duration_seconds=3600
    )
    
    # Get insights
    daily_summary = metrics_service.get_daily_summary(datetime.now())
    correlations = metrics_service.analyze_correlations()
    optimal_times = metrics_service.get_optimal_times()
    mood_patterns = metrics_service.get_mood_patterns()
    energy_patterns = metrics_service.get_energy_depletion_patterns()
"""
