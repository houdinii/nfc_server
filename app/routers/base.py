# app/routers/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.base import BaseModel as DBBaseModel
from app.models.user import User

# Type variables for generics
ModelType = TypeVar('ModelType', bound=DBBaseModel)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)
ResponseSchemaType = TypeVar('ResponseSchemaType', bound=BaseModel)


class BaseRouter(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    Abstract base class for all routers providing common functionality
    and patterns used across different router implementations.
    """

    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None):
        self.router = APIRouter(prefix=prefix, tags=tags or [])
        self._setup_routes()

    @property
    @abstractmethod
    def model_class(self) -> Type[ModelType]:
        """The database model class this router manages"""
        pass

    @property
    @abstractmethod
    def create_schema(self) -> Type[CreateSchemaType]:
        """Pydantic schema for creating new entities"""
        pass

    @property
    @abstractmethod
    def update_schema(self) -> Type[UpdateSchemaType]:
        """Pydantic schema for updating entities"""
        pass

    @property
    @abstractmethod
    def response_schema(self) -> Type[ResponseSchemaType]:
        """Pydantic schema for API responses"""
        pass

    def _setup_routes(self):
        """Set up common CRUD routes if needed by subclasses"""
        pass

    def _get_user_entity(
            self,
            entity_id: str,
            current_user: User,
            db: Session,
            raise_404: bool = True
    ) -> Optional[ModelType]:
        """
        Get an entity that belongs to the current user

        Args:
            entity_id: The ID of the entity to retrieve
            current_user: The authenticated user
            db: Database session
            raise_404: Whether to raise 404 if not found

        Returns:
            The entity if found, None if not found and raise_404=False

        Raises:
            HTTPException: If entity not found and raise_404=True
        """
        query = db.query(self.model_class)

        # Build filters
        filters = [self.model_class.id == entity_id]

        # Only filter by user_id if the model has that attribute
        if hasattr(self.model_class, 'user_id'):
            filters.append(self.model_class.user_id == current_user.id)

        query = query.filter(and_(*filters))

        entity = query.first()

        if not entity and raise_404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model_class.__name__} not found"
            )

        return entity

    def _get_user_entities(
            self,
            current_user: User,
            db: Session,
            filters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            offset: int = 0
    ) -> List[ModelType]:
        """
        Get all entities belonging to the current user with optional filtering

        Args:
            current_user: The authenticated user
            db: Database session
            filters: Additional filter conditions
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of entities
        """
        query = db.query(self.model_class)

        # Build filter conditions
        filter_conditions = []

        # Only filter by user_id if the model has that attribute
        if hasattr(self.model_class, 'user_id'):
            filter_conditions.append(self.model_class.user_id == current_user.id)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field) and value is not None:
                    filter_conditions.append(getattr(self.model_class, field) == value)

        # Apply filters if any exist
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

        query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def _create_entity(
            self,
            create_data: CreateSchemaType,
            current_user: User,
            db: Session,
            **additional_fields
    ) -> ModelType:
        """
        Create a new entity for the current user

        Args:
            create_data: The validated creation data
            current_user: The authenticated user
            db: Database session
            **additional_fields: Additional fields to set on the entity

        Returns:
            The created entity
        """
        entity_data = create_data.model_dump()
        entity_data.update(additional_fields)

        # Only set user_id if the model has that attribute
        if hasattr(self.model_class, 'user_id'):
            entity_data['user_id'] = current_user.id

        entity = self.model_class(**entity_data)
        db.add(entity)
        db.commit()
        db.refresh(entity)

        return entity

    def _update_entity(
            self,
            entity: ModelType,
            update_data: UpdateSchemaType,
            db: Session
    ) -> ModelType:
        """
        Update an entity with new data

        Args:
            entity: The entity to update
            update_data: The validated update data
            db: Database session

        Returns:
            The updated entity
        """
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)

        return entity

    def _delete_entity(self, entity: ModelType, db: Session) -> None:
        """
        Delete an entity

        Args:
            entity: The entity to delete
            db: Database session
        """
        db.delete(entity)
        db.commit()

    def _validate_entity_ownership(
            self,
            entity: ModelType,
            current_user: User
    ) -> None:
        """
        Validate that an entity belongs to the current user

        Args:
            entity: The entity to validate
            current_user: The authenticated user

        Raises:
            HTTPException: If the entity doesn't belong to the user
        """
        if hasattr(entity, 'user_id') and entity.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this resource"
            )

    def _handle_db_error(self, error: Exception, operation: str = "operation") -> None:
        """
        Handle database errors with appropriate HTTP responses

        Args:
            error: The database error
            operation: Description of the operation that failed

        Raises:
            HTTPException: Appropriate HTTP error for the database error
        """
        # This could be expanded to handle specific database errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during {operation}"
        )

    def add_dependency_routes(
            self,
            dependencies: Optional[List] = None
    ) -> APIRouter:
        """
        Get the router with additional dependencies applied to all routes

        Args:
            dependencies: Additional dependencies to apply

        Returns:
            The configured router
        """
        if dependencies:
            self.router.dependencies.extend(dependencies)
        return self.router


class CRUDRouter(BaseRouter[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType], ABC):
    """
    Base router that provides standard CRUD operations.
    Subclasses only need to define the schema properties and can override
    specific operations as needed.
    """

    def _setup_routes(self):
        """Setup standard CRUD routes"""
        self._setup_create_route()
        self._setup_list_route()
        self._setup_get_route()
        self._setup_update_route()
        self._setup_delete_route()

    def _setup_create_route(self):
        """Set up POST route for entity creation"""

        @self.router.post("/", response_model=self.response_schema)
        async def create_entity(
                create_data: CreateSchemaType,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            return await self.create_handler(create_data, current_user, db)

    def _setup_list_route(self):
        """Set up GET route for listing entities"""

        @self.router.get("/", response_model=List[self.response_schema])
        async def list_entities(
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            return await self.list_handler(current_user, db)

    def _setup_get_route(self):
        """Setup GET route for retrieving single entity"""

        @self.router.get("/{entity_id}", response_model=self.response_schema)
        async def get_entity(
                entity_id: str,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            return await self.get_handler(entity_id, current_user, db)

    def _setup_update_route(self):
        """Set up PATCH route for updating entities"""

        @self.router.patch("/{entity_id}", response_model=self.response_schema)
        async def update_entity(
                entity_id: str,
                update_data: UpdateSchemaType,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            return await self.update_handler(entity_id, update_data, current_user, db)

    def _setup_delete_route(self):
        """Setup DELETE route for deleting entities"""

        @self.router.delete("/{entity_id}")
        async def delete_entity(
                entity_id: str,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)
        ):
            return await self.delete_handler(entity_id, current_user, db)

    # Handler methods that subclasses can override

    async def create_handler(
            self,
            create_data: CreateSchemaType,
            current_user: User,
            db: Session
    ) -> ResponseSchemaType:
        """Handle entity creation - can be overridden"""
        return self._create_entity(create_data, current_user, db)

    async def list_handler(
            self,
            current_user: User,
            db: Session
    ) -> List[ResponseSchemaType]:
        """Handle entity listing - can be overridden"""
        return self._get_user_entities(current_user, db)

    async def get_handler(
            self,
            entity_id: str,
            current_user: User,
            db: Session
    ) -> ResponseSchemaType:
        """Handle single entity retrieval - can be overridden"""
        return self._get_user_entity(entity_id, current_user, db)

    async def update_handler(
            self,
            entity_id: str,
            update_data: UpdateSchemaType,
            current_user: User,
            db: Session
    ) -> ResponseSchemaType:
        """Handle entity updates - can be overridden"""
        entity = self._get_user_entity(entity_id, current_user, db)
        return self._update_entity(entity, update_data, db)

    async def delete_handler(
            self,
            entity_id: str,
            current_user: User,
            db: Session
    ) -> Dict[str, str]:
        """Handle entity deletion - can be overridden"""
        entity = self._get_user_entity(entity_id, current_user, db)
        self._delete_entity(entity, db)
        return {"message": f"{self.model_class.__name__} deleted successfully"}
