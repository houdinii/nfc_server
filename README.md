# Base Classes for NFC Server

This document describes two base classes created to extract common patterns from the NFC server codebase:

1. **BaseRouter** - Abstract base for router classes
2. **MetricTracker** - Base for activity metrics tracking

## BaseRouter

### Overview

The `BaseRouter` class extracts common patterns found across different router implementations in the codebase. It provides:

- Common dependency injection patterns (`get_current_user`, `get_db`)
- Standard CRUD operation templates
- User ownership validation
- Database error handling
- Entity retrieval patterns

### Key Features

- **Abstract Base Class**: Enforces consistent router structure
- **CRUD Operations**: `CRUDRouter` provides standard Create, Read, Update, Delete endpoints
- **User Isolation**: Automatic filtering by `user_id` for multi-tenant security
- **Error Handling**: Standardized HTTP error responses
- **Extensibility**: Easy to override specific handlers for custom logic

### Usage Examples

#### Basic CRUD Router

```python
from app.routers.base import CRUDRouter
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse

class TagRouter(CRUDRouter):
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

# Usage
tag_router = TagRouter()
app.include_router(tag_router.router, prefix="/tags")
```

#### Custom Router with Additional Endpoints

```python
class TagRouter(CRUDRouter):
    # ... property definitions ...
    
    def __init__(self):
        super().__init__(prefix="/tags", tags=["tags"])
        self._setup_custom_routes()
    
    def _setup_custom_routes(self):
        @self.router.get("/by-nfc/{nfc_id}", response_model=TagResponse)
        async def get_tag_by_nfc(nfc_id: str, ...):
            # Custom endpoint logic
            pass
    
    async def create_handler(self, create_data, current_user, db):
        # Override default create logic
        # Custom validation, etc.
        return self._create_entity(create_data, current_user, db)
```

### Router Patterns Extracted

The BaseRouter identifies these common patterns from the existing codebase:

1. **User Filtering**: All entities filtered by `current_user.id`
2. **Standard Dependencies**: `Depends(get_current_user)`, `Depends(get_db)`
3. **Error Handling**: Consistent 404/403/400 responses
4. **Update Pattern**: `model_dump(exclude_unset=True)` for partial updates
5. **Entity Validation**: Check ownership before operations

## MetricTracker

### Overview

The `MetricTracker` class provides a foundation for tracking different types of metrics like energy, focus, and mood. Based on analysis of the Activity model, these metrics are commonly tracked:

- Energy levels (1-5 scale)
- Focus levels (1-5 scale) 
- Mood states (categorical: happy, anxious, calm, etc.)
- Productivity ratings (1-5 scale)

### Key Features

- **Type Safety**: Validates metric values against defined scales
- **Time-based Analysis**: Calculate averages, trends over time periods
- **Correlation Analysis**: Find relationships between different metrics
- **Flexible Storage**: JSON context and notes for each measurement
- **Summary Statistics**: Generate comprehensive metric summaries

### Concrete Implementations

#### EnergyTracker
```python
energy_tracker = EnergyTracker()
energy_tracker.add_entry(4, datetime.now(), notes="After morning coffee")
avg_energy = energy_tracker.calculate_average()
trend = energy_tracker.get_trend()
```

#### FocusTracker
```python
focus_tracker = FocusTracker()
focus_tracker.add_entry(3, datetime.now(), context={"activity": "coding"})
summary = focus_tracker.get_summary(start_time, end_time)
```

#### MoodTracker
```python
mood_tracker = MoodTracker()
mood_tracker.add_entry("calm", datetime.now())
distribution = mood_tracker.get_mood_distribution()
# Returns: {"happy": 5, "calm": 8, "anxious": 2, ...}
```

#### ProductivityTracker
```python
productivity_tracker = ProductivityTracker()
productivity_tracker.add_entry(4, datetime.now(), context={"duration": 3600})
correlations = energy_tracker.find_correlations(productivity_tracker)
```

### Integration with Activities

The `ActivityMetricsService` shows how to integrate metric tracking with the existing Activity model:

```python
# Initialize service for a user
metrics_service = ActivityMetricsService(user, db)

# Record activity start
metrics_service.record_activity_start(
    activity_id="123",
    energy_level=4,
    focus_level=3,
    mood="calm"
)

# Record activity end
metrics_service.record_activity_end(
    activity_id="123",
    energy_level_end=2,
    focus_level_end=4,
    mood_end="focused",
    productivity=4
)

# Analysis
daily_summary = metrics_service.get_daily_summary(datetime.now())
correlations = metrics_service.analyze_correlations()
optimal_times = metrics_service.get_optimal_times()
```

### Metric Analysis Capabilities

1. **Trend Analysis**: Identify if metrics are increasing, decreasing, or stable
2. **Correlation Detection**: Find relationships between different metrics
3. **Time Pattern Recognition**: Identify optimal times for high energy/focus
4. **Mood Pattern Analysis**: Understand mood variations by day of week
5. **Energy Depletion Tracking**: See how activities affect energy levels

## Benefits of These Base Classes

### Code Reuse
- Eliminates duplicated patterns across routers
- Provides consistent API structure
- Reduces boilerplate code

### Maintainability
- Central location for common logic
- Easier to update patterns across all routers
- Consistent error handling and validation

### Testing
- Base classes can be thoroughly tested once
- Subclasses inherit tested functionality
- Easier to mock and test specific behaviors

### Extensibility
- Easy to add new metric types by extending MetricTracker
- Router functionality can be customized while keeping common patterns
- New analysis methods can be added to base tracker classes

## Migration Strategy

### For Existing Routers

1. **Identify Common Patterns**: Look for repeated code across router files
2. **Extract to Base**: Move common logic to BaseRouter methods
3. **Inherit and Customize**: Create router subclasses that inherit from BaseRouter
4. **Override as Needed**: Customize specific handlers while keeping common patterns

### For Metric Tracking

1. **Audit Activity Model**: Identify all metrics currently tracked
2. **Create Tracker Instances**: Instantiate appropriate tracker classes
3. **Integrate with Endpoints**: Use trackers in activity CRUD operations
4. **Add Analysis Endpoints**: Create new endpoints for metric insights

## Example Integration

Here's how these base classes work together:

```python
# Router using BaseRouter pattern
class ActivityRouter(CRUDRouter):
    def __init__(self):
        super().__init__(prefix="/activities", tags=["activities"])
        self.metrics_service = None
    
    async def create_handler(self, create_data, current_user, db):
        # Create activity using base functionality
        activity = self._create_entity(create_data, current_user, db)
        
        # Initialize metrics tracking
        metrics_service = ActivityMetricsService(current_user, db)
        
        # Record starting metrics
        metrics_service.record_activity_start(
            activity.id,
            create_data.energy_level,
            create_data.focus_level,
            create_data.mood_start
        )
        
        return activity
    
    async def update_handler(self, activity_id, update_data, current_user, db):
        # Update using base functionality
        activity = super().update_handler(activity_id, update_data, current_user, db)
        
        # Record ending metrics if activity is completed
        if update_data.end_time:
            metrics_service = ActivityMetricsService(current_user, db)
            metrics_service.record_activity_end(
                activity_id,
                update_data.energy_level_end,
                update_data.focus_level_end,
                update_data.mood_end,
                update_data.perceived_productivity
            )
        
        return activity
```

This demonstrates how the base classes work together to provide a clean, maintainable architecture while reducing code duplication and providing powerful metric analysis capabilities.
