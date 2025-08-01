"""Base repository pattern with tenant-aware data access."""
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any, Sequence
from abc import ABC, abstractmethod
from uuid import uuid4

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.database import TenantBase, get_tenant_database_session
from src.tenant.manager import tenant_db_manager
from src.tenant.context import get_tenant_context
from src.exceptions import NotFoundError, ValidationError, DatabaseError

# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=TenantBase)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Base repository class with tenant-aware CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_session(self) -> AsyncSession:
        """Get tenant-aware database session."""
        tenant_context = get_tenant_context()
        return await tenant_db_manager.get_tenant_session(tenant_context)
    
    async def create(self, data: CreateSchemaType, **kwargs) -> ModelType:
        """Create a new entity."""
        async with await self.get_session() as session:
            try:
                # Convert Pydantic model to dict
                if hasattr(data, 'model_dump'):
                    entity_data = data.model_dump(exclude_unset=True)
                else:
                    entity_data = data.dict(exclude_unset=True)
                
                # Add any additional kwargs
                entity_data.update(kwargs)
                
                # Ensure ID is set
                if 'id' not in entity_data:
                    entity_data['id'] = str(uuid4())
                
                # Create entity
                entity = self.model(**entity_data)
                session.add(entity)
                
                await session.commit()
                await session.refresh(entity)
                
                return entity
                
            except IntegrityError as e:
                await session.rollback()
                raise ValidationError(f"Data integrity error: {str(e)}")
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to create {self.model.__name__}: {str(e)}")
    
    async def get_by_id(
        self, 
        entity_id: str, 
        load_relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Get entity by ID with optional relationship loading."""
        async with await self.get_session() as session:
            try:
                query = select(self.model).where(self.model.id == entity_id)
                
                # Add relationship loading if specified
                if load_relationships:
                    for relationship in load_relationships:
                        if hasattr(self.model, relationship):
                            query = query.options(selectinload(getattr(self.model, relationship)))
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get {self.model.__name__} by ID: {str(e)}")
    
    async def get_by_field(
        self, 
        field_name: str, 
        field_value: Any,
        load_relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Get entity by specific field."""
        async with await self.get_session() as session:
            try:
                if not hasattr(self.model, field_name):
                    raise ValidationError(f"Field '{field_name}' not found on {self.model.__name__}")
                
                field = getattr(self.model, field_name)
                query = select(self.model).where(field == field_value)
                
                # Add relationship loading if specified
                if load_relationships:
                    for relationship in load_relationships:
                        if hasattr(self.model, relationship):
                            query = query.options(selectinload(getattr(self.model, relationship)))
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get {self.model.__name__} by {field_name}: {str(e)}")
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        load_relationships: Optional[List[str]] = None
    ) -> List[ModelType]:
        """Get multiple entities with filtering and pagination."""
        async with await self.get_session() as session:
            try:
                query = select(self.model)
                
                # Apply filters
                if filters:
                    conditions = []
                    for field_name, field_value in filters.items():
                        if hasattr(self.model, field_name):
                            field = getattr(self.model, field_name)
                            if isinstance(field_value, list):
                                conditions.append(field.in_(field_value))
                            elif isinstance(field_value, dict):
                                # Handle range queries
                                if 'gte' in field_value:
                                    conditions.append(field >= field_value['gte'])
                                if 'lte' in field_value:
                                    conditions.append(field <= field_value['lte'])
                                if 'gt' in field_value:
                                    conditions.append(field > field_value['gt'])
                                if 'lt' in field_value:
                                    conditions.append(field < field_value['lt'])
                            else:
                                conditions.append(field == field_value)
                    
                    if conditions:
                        query = query.where(and_(*conditions))
                
                # Apply ordering
                if order_by:
                    if order_by.startswith('-'):
                        # Descending order
                        field_name = order_by[1:]
                        if hasattr(self.model, field_name):
                            query = query.order_by(getattr(self.model, field_name).desc())
                    else:
                        # Ascending order
                        if hasattr(self.model, order_by):
                            query = query.order_by(getattr(self.model, order_by))
                
                # Add relationship loading if specified
                if load_relationships:
                    for relationship in load_relationships:
                        if hasattr(self.model, relationship):
                            query = query.options(selectinload(getattr(self.model, relationship)))
                
                # Apply pagination
                query = query.offset(skip).limit(limit)
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get {self.model.__name__} list: {str(e)}")
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        async with await self.get_session() as session:
            try:
                query = select(func.count(self.model.id))
                
                # Apply filters
                if filters:
                    conditions = []
                    for field_name, field_value in filters.items():
                        if hasattr(self.model, field_name):
                            field = getattr(self.model, field_name)
                            if isinstance(field_value, list):
                                conditions.append(field.in_(field_value))
                            else:
                                conditions.append(field == field_value)
                    
                    if conditions:
                        query = query.where(and_(*conditions))
                
                result = await session.execute(query)
                return result.scalar() or 0
                
            except Exception as e:
                raise DatabaseError(f"Failed to count {self.model.__name__}: {str(e)}")
    
    async def update(
        self, 
        entity_id: str, 
        data: UpdateSchemaType,
        **kwargs
    ) -> Optional[ModelType]:
        """Update an entity by ID."""
        async with await self.get_session() as session:
            try:
                # Convert Pydantic model to dict
                if hasattr(data, 'model_dump'):
                    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
                else:
                    update_data = data.dict(exclude_unset=True, exclude_none=True)
                
                # Add any additional kwargs
                update_data.update(kwargs)
                
                if not update_data:
                    # No data to update
                    return await self.get_by_id(entity_id)
                
                # Update entity
                query = (
                    update(self.model)
                    .where(self.model.id == entity_id)
                    .values(**update_data)
                    .returning(self.model)
                )
                
                result = await session.execute(query)
                entity = result.scalar_one_or_none()
                
                if entity:
                    await session.commit()
                    await session.refresh(entity)
                else:
                    await session.rollback()
                
                return entity
                
            except IntegrityError as e:
                await session.rollback()
                raise ValidationError(f"Data integrity error: {str(e)}")
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update {self.model.__name__}: {str(e)}")
    
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        async with await self.get_session() as session:
            try:
                query = delete(self.model).where(self.model.id == entity_id)
                result = await session.execute(query)
                
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to delete {self.model.__name__}: {str(e)}")
    
    async def bulk_create(self, entities_data: List[CreateSchemaType], **kwargs) -> List[ModelType]:
        """Create multiple entities in bulk."""
        async with await self.get_session() as session:
            try:
                entities = []
                
                for data in entities_data:
                    # Convert Pydantic model to dict
                    if hasattr(data, 'model_dump'):
                        entity_data = data.model_dump(exclude_unset=True)
                    else:
                        entity_data = data.dict(exclude_unset=True)
                    
                    # Add any additional kwargs
                    entity_data.update(kwargs)
                    
                    # Ensure ID is set
                    if 'id' not in entity_data:
                        entity_data['id'] = str(uuid4())
                    
                    entities.append(self.model(**entity_data))
                
                session.add_all(entities)
                await session.commit()
                
                # Refresh all entities
                for entity in entities:
                    await session.refresh(entity)
                
                return entities
                
            except IntegrityError as e:
                await session.rollback()
                raise ValidationError(f"Data integrity error: {str(e)}")
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to bulk create {self.model.__name__}: {str(e)}")
    
    async def exists(self, entity_id: str) -> bool:
        """Check if entity exists by ID."""
        async with await self.get_session() as session:
            try:
                query = select(func.count(self.model.id)).where(self.model.id == entity_id)
                result = await session.execute(query)
                count = result.scalar() or 0
                return count > 0
                
            except Exception as e:
                raise DatabaseError(f"Failed to check {self.model.__name__} existence: {str(e)}")


class UserScopedRepository(BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Repository for entities that are scoped to a specific user."""
    
    def __init__(self, model: Type[ModelType], user_field: str = "user_id"):
        super().__init__(model)
        self.user_field = user_field
    
    async def get_by_id_for_user(
        self, 
        entity_id: str, 
        user_id: str,
        load_relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Get entity by ID for specific user."""
        async with await self.get_session() as session:
            try:
                user_field = getattr(self.model, self.user_field)
                query = select(self.model).where(
                    and_(
                        self.model.id == entity_id,
                        user_field == user_id
                    )
                )
                
                # Add relationship loading if specified
                if load_relationships:
                    for relationship in load_relationships:
                        if hasattr(self.model, relationship):
                            query = query.options(selectinload(getattr(self.model, relationship)))
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get {self.model.__name__} by ID for user: {str(e)}")
    
    async def get_multi_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        load_relationships: Optional[List[str]] = None
    ) -> List[ModelType]:
        """Get multiple entities for specific user."""
        # Add user filter to filters
        if filters is None:
            filters = {}
        filters[self.user_field] = user_id
        
        return await self.get_multi(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=order_by,
            load_relationships=load_relationships
        )
    
    async def count_for_user(self, user_id: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities for specific user."""
        # Add user filter to filters
        if filters is None:
            filters = {}
        filters[self.user_field] = user_id
        
        return await self.count(filters=filters)
    
    async def create_for_user(self, data: CreateSchemaType, user_id: str, **kwargs) -> ModelType:
        """Create entity for specific user."""
        kwargs[self.user_field] = user_id
        return await self.create(data, **kwargs)