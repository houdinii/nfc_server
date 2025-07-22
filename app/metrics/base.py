# app/metrics/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel


class MetricType(str, Enum):
    """Types of metrics that can be tracked"""
    ENERGY = "energy"
    FOCUS = "focus"
    MOOD = "mood"
    PRODUCTIVITY = "productivity"
    STRESS = "stress"
    MOTIVATION = "motivation"


class MetricScale(str, Enum):
    """Different scales for metric measurement"""
    SCALE_1_5 = "1-5"  # 1-5 numeric scale
    SCALE_1_10 = "1-10"  # 1-10 numeric scale
    CATEGORICAL = "categorical"  # String categories
    BOOLEAN = "boolean"  # True/False
    PERCENTAGE = "percentage"  # 0-100


class MetricEntry(BaseModel):
    """A single metric measurement"""
    value: Union[int, float, str, bool]
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class MetricSummary(BaseModel):
    """Summary statistics for a metric over a time period"""
    metric_type: MetricType
    period_start: datetime
    period_end: datetime
    total_entries: int
    average_value: Optional[float] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    trend_direction: Optional[str] = None  # "increasing", "decreasing", "stable"
    variance: Optional[float] = None


class MetricTracker(ABC):
    """
    Abstract base class for tracking different types of metrics
    like energy, mood, focus, etc. Provides common functionality
    for metric collection, validation, and analysis.
    """

    def __init__(self, metric_type: MetricType, scale: MetricScale):
        self.metric_type = metric_type
        self.scale = scale
        self.entries: List[MetricEntry] = []

    @property
    @abstractmethod
    def valid_values(self) -> Union[range, List[str], List[bool]]:
        """Define valid values for this metric type"""
        pass

    @property
    def latest_entry(self) -> Optional[MetricEntry]:
        """Get the most recent metric entry"""
        return self.entries[-1] if self.entries else None

    @property
    def latest_value(self) -> Optional[Union[int, float, str, bool]]:
        """Get the most recent metric value"""
        latest = self.latest_entry
        return latest.value if latest else None

    def add_entry(
            self,
            value: Union[int, float, str, bool],
            timestamp: Optional[datetime] = None,
            context: Optional[Dict[str, Any]] = None,
            notes: Optional[str] = None
    ) -> MetricEntry:
        """
        Add a new metric measurement
        
        Args:
            value: The metric value
            timestamp: When the measurement was taken (defaults to now)
            context: Additional context information
            notes: Optional notes about the measurement
            
        Returns:
            The created MetricEntry
            
        Raises:
            ValueError: If the value is not valid for this metric type
        """
        if not self.is_valid_value(value):
            raise ValueError(f"Invalid value {value} for {self.metric_type.value} metric")

        if timestamp is None:
            timestamp = datetime.now()

        entry = MetricEntry(
            value=value,
            timestamp=timestamp,
            context=context or {},
            notes=notes
        )

        self.entries.append(entry)
        return entry

    @abstractmethod
    def is_valid_value(self, value: Union[int, float, str, bool]) -> bool:
        """
        Validate if a value is appropriate for this metric type
        
        Args:
            value: The value to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass

    def get_entries_in_range(
            self,
            start_time: datetime,
            end_time: datetime
    ) -> List[MetricEntry]:
        """
        Get all entries within a specified time range
        
        Args:
            start_time: Start of the time range
            end_time: End of the time range
            
        Returns:
            List of entries in the time range
        """
        return [
            entry for entry in self.entries
            if start_time <= entry.timestamp <= end_time
        ]

    def calculate_average(
            self,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Calculate average value over a time period
        
        Args:
            start_time: Start of period (None for all time)
            end_time: End of period (None for all time)
            
        Returns:
            Average value or None if no numeric entries
        """
        entries = self.entries
        if start_time and end_time:
            entries = self.get_entries_in_range(start_time, end_time)

        numeric_values = [
            float(entry.value) for entry in entries
            if isinstance(entry.value, (int, float))
        ]

        return sum(numeric_values) / len(numeric_values) if numeric_values else None

    def get_trend(
            self,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            window_size: int = 5
    ) -> Optional[str]:
        """
        Calculate trend direction over time
        
        Args:
            start_time: Start of period
            end_time: End of period  
            window_size: Number of recent entries to consider for trend
            
        Returns:
            "increasing", "decreasing", "stable", or None
        """
        entries = self.entries
        if start_time and end_time:
            entries = self.get_entries_in_range(start_time, end_time)

        # Get recent numeric entries
        numeric_entries = [
            entry for entry in entries[-window_size:]
            if isinstance(entry.value, (int, float))
        ]

        if len(numeric_entries) < 2:
            return None

        # Simple trend calculation
        first_half = numeric_entries[:len(numeric_entries) // 2]
        second_half = numeric_entries[len(numeric_entries) // 2:]

        if not first_half or not second_half:
            return None

        avg_first = sum(float(e.value) for e in first_half) / len(first_half)
        avg_second = sum(float(e.value) for e in second_half) / len(second_half)

        diff = avg_second - avg_first

        if abs(diff) < 0.1:  # Threshold for "stable"
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"

    def get_summary(
            self,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
    ) -> MetricSummary:
        """
        Get summary statistics for this metric
        
        Args:
            start_time: Start of period
            end_time: End of period
            
        Returns:
            MetricSummary with statistics
        """
        entries = self.entries
        if start_time and end_time:
            entries = self.get_entries_in_range(start_time, end_time)

        numeric_values = [
            float(entry.value) for entry in entries
            if isinstance(entry.value, (int, float))
        ]

        return MetricSummary(
            metric_type=self.metric_type,
            period_start=start_time or (entries[0].timestamp if entries else datetime.now()),
            period_end=end_time or (entries[-1].timestamp if entries else datetime.now()),
            total_entries=len(entries),
            average_value=sum(numeric_values) / len(numeric_values) if numeric_values else None,
            min_value=min(numeric_values) if numeric_values else None,
            max_value=max(numeric_values) if numeric_values else None,
            trend_direction=self.get_trend(start_time, end_time),
            variance=self._calculate_variance(numeric_values) if numeric_values else None
        )

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of numeric values"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def find_correlations(
            self,
            other_tracker: 'MetricTracker',
            time_window_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Find correlations between this metric and another metric
        
        Args:
            other_tracker: Another MetricTracker to correlate with
            time_window_minutes: Time window for matching entries
            
        Returns:
            Dictionary with correlation information
        """
        from datetime import timedelta

        correlations = []

        for entry in self.entries:
            # Find entries in the other tracker within the time window
            window_start = entry.timestamp - timedelta(minutes=time_window_minutes)
            window_end = entry.timestamp + timedelta(minutes=time_window_minutes)

            nearby_entries = other_tracker.get_entries_in_range(window_start, window_end)

            for other_entry in nearby_entries:
                if (isinstance(entry.value, (int, float)) and
                        isinstance(other_entry.value, (int, float))):
                    correlations.append({
                        'value1': float(entry.value),
                        'value2': float(other_entry.value),
                        'time_diff_minutes': abs(
                            (entry.timestamp - other_entry.timestamp).total_seconds() / 60
                        )
                    })

        if len(correlations) < 2:
            return {
                'correlation_coefficient': None,
                'sample_size': len(correlations),
                'significant': False
            }

        # Simple correlation calculation
        values1 = [c['value1'] for c in correlations]
        values2 = [c['value2'] for c in correlations]

        correlation_coeff = self._calculate_correlation(values1, values2)

        return {
            'correlation_coefficient': correlation_coeff,
            'sample_size': len(correlations),
            'significant': abs(correlation_coeff) > 0.3 if correlation_coeff else False,
            'strength': self._interpret_correlation(correlation_coeff)
        }

    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> Optional[float]:
        """Calculate Pearson correlation coefficient"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return None

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5

        if denominator == 0:
            return None

        return numerator / denominator

    def _interpret_correlation(self, correlation: Optional[float]) -> str:
        """Interpret correlation coefficient strength"""
        if correlation is None:
            return "unknown"

        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.3:
            return "moderate"
        else:
            return "weak"


# Concrete implementations for specific metrics

class EnergyTracker(MetricTracker):
    """Track energy levels on a 1-5 scale"""

    def __init__(self):
        super().__init__(MetricType.ENERGY, MetricScale.SCALE_1_5)

    @property
    def valid_values(self) -> range:
        return range(1, 6)

    def is_valid_value(self, value: Union[int, float, str, bool]) -> bool:
        return isinstance(value, (int, float)) and 1 <= value <= 5


class FocusTracker(MetricTracker):
    """Track focus levels on a 1-5 scale"""

    def __init__(self):
        super().__init__(MetricType.FOCUS, MetricScale.SCALE_1_5)

    @property
    def valid_values(self) -> range:
        return range(1, 6)

    def is_valid_value(self, value: Union[int, float, str, bool]) -> bool:
        return isinstance(value, (int, float)) and 1 <= value <= 5


class MoodTracker(MetricTracker):
    """Track mood using categorical values"""

    MOOD_VALUES = ["happy", "neutral", "anxious", "frustrated", "calm", "energetic", "sad", "excited"]

    def __init__(self):
        super().__init__(MetricType.MOOD, MetricScale.CATEGORICAL)

    @property
    def valid_values(self) -> List[str]:
        return self.MOOD_VALUES

    def is_valid_value(self, value: Union[int, float, str, bool]) -> bool:
        return isinstance(value, str) and value in self.MOOD_VALUES

    def get_mood_distribution(
            self,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get distribution of different mood states"""
        entries = self.entries
        if start_time and end_time:
            entries = self.get_entries_in_range(start_time, end_time)

        distribution = {mood: 0 for mood in self.MOOD_VALUES}
        for entry in entries:
            if isinstance(entry.value, str) and entry.value in distribution:
                distribution[entry.value] += 1

        return distribution


class ProductivityTracker(MetricTracker):
    """Track perceived productivity on a 1-5 scale"""

    def __init__(self):
        super().__init__(MetricType.PRODUCTIVITY, MetricScale.SCALE_1_5)

    @property
    def valid_values(self) -> range:
        return range(1, 6)

    def is_valid_value(self, value: Union[int, float, str, bool]) -> bool:
        return isinstance(value, (int, float)) and 1 <= value <= 5
