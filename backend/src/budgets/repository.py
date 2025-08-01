"""Repository for budget management."""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.repository import UserScopedRepository
from src.budgets.models import (
    Budget, BudgetCategory, BudgetAlert, BudgetTemplate, BudgetTemplateCategory,
    BudgetStatus, AlertType
)
from src.budgets.schemas import (
    BudgetCreate, BudgetUpdate,
    BudgetCategoryCreate, BudgetCategoryUpdate,
    BudgetTemplateCreate, BudgetTemplateUpdate
)
from src.exceptions import NotFoundError, DatabaseError, ValidationError


class BudgetRepository(UserScopedRepository[Budget, BudgetCreate, BudgetUpdate]):
    """Repository for managing budgets."""
    
    def __init__(self):
        super().__init__(Budget)
    
    async def get_active_budgets_for_user(self, user_id: str) -> List[Budget]:
        """Get all active budgets for a user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"status": BudgetStatus.ACTIVE},
            order_by="-created_at",
            load_relationships=["categories", "alerts"]
        )
    
    async def get_budgets_by_period(
        self, 
        user_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[Budget]:
        """Get budgets for a specific period."""
        async with await self.get_session() as session:
            try:
                query = (
                    select(Budget)
                    .where(
                        and_(
                            Budget.user_id == user_id,
                            or_(
                                and_(Budget.start_date >= start_date, Budget.start_date <= end_date),
                                and_(Budget.end_date >= start_date, Budget.end_date <= end_date),
                                and_(Budget.start_date <= start_date, Budget.end_date >= end_date)
                            )
                        )
                    )
                    .order_by(Budget.start_date)
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get budgets by period: {str(e)}")
    
    async def get_current_budget_for_user(self, user_id: str) -> Optional[Budget]:
        """Get current active budget for user."""
        today = date.today()
        async with await self.get_session() as session:
            try:
                query = (
                    select(Budget)
                    .where(
                        and_(
                            Budget.user_id == user_id,
                            Budget.status == BudgetStatus.ACTIVE,
                            Budget.start_date <= today,
                            Budget.end_date >= today
                        )
                    )
                    .order_by(Budget.created_at.desc())
                )
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
            except Exception as e:
                raise DatabaseError(f"Failed to get current budget: {str(e)}")
    
    async def update_spent_amount(self, budget_id: str, new_spent_amount: Decimal) -> Optional[Budget]:
        """Update budget spent amount and recalculate remaining."""
        async with await self.get_session() as session:
            try:
                # Get current budget
                budget = await session.get(Budget, budget_id)
                if not budget:
                    return None
                
                # Update amounts
                remaining_amount = budget.total_amount - new_spent_amount
                
                query = (
                    update(Budget)
                    .where(Budget.id == budget_id)
                    .values(
                        spent_amount=new_spent_amount,
                        remaining_amount=remaining_amount,
                        updated_at=func.now()
                    )
                    .returning(Budget)
                )
                
                result = await session.execute(query)
                updated_budget = result.scalar_one_or_none()
                
                if updated_budget:
                    await session.commit()
                    await session.refresh(updated_budget)
                else:
                    await session.rollback()
                
                return updated_budget
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update spent amount: {str(e)}")
    
    async def get_budget_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get budget analytics for user."""
        async with await self.get_session() as session:
            try:
                # Total budgets
                total_budgets_query = (
                    select(func.count(Budget.id))
                    .where(Budget.user_id == user_id)
                )
                total_budgets = await session.scalar(total_budgets_query) or 0
                
                # Active budgets
                active_budgets_query = (
                    select(func.count(Budget.id))
                    .where(
                        and_(
                            Budget.user_id == user_id,
                            Budget.status == BudgetStatus.ACTIVE
                        )
                    )
                )
                active_budgets = await session.scalar(active_budgets_query) or 0
                
                # Amount totals
                amounts_query = (
                    select(
                        func.sum(Budget.total_amount),
                        func.sum(Budget.spent_amount),
                        func.sum(Budget.remaining_amount)
                    )
                    .where(
                        and_(
                            Budget.user_id == user_id,
                            Budget.status == BudgetStatus.ACTIVE
                        )
                    )
                )
                amounts_result = await session.execute(amounts_query)
                amounts = amounts_result.first()
                
                total_budgeted = amounts[0] or Decimal(0)
                total_spent = amounts[1] or Decimal(0)
                total_remaining = amounts[2] or Decimal(0)
                
                # Average utilization
                avg_utilization = Decimal(0)
                if total_budgeted > 0:
                    avg_utilization = (total_spent / total_budgeted) * 100
                
                return {
                    "total_budgets": total_budgets,
                    "active_budgets": active_budgets,
                    "total_budgeted_amount": total_budgeted,
                    "total_spent_amount": total_spent,
                    "total_remaining_amount": total_remaining,
                    "average_utilization": avg_utilization
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get budget analytics: {str(e)}")


class BudgetCategoryRepository(UserScopedRepository[BudgetCategory, BudgetCategoryCreate, BudgetCategoryUpdate]):
    """Repository for managing budget categories."""
    
    def __init__(self):
        super().__init__(BudgetCategory, user_field="budget_id")  # Categories are scoped to budget
    
    async def get_categories_for_budget(self, budget_id: str) -> List[BudgetCategory]:
        """Get all categories for a budget."""
        return await self.get_multi(
            filters={"budget_id": budget_id},
            order_by="priority"
        )
    
    async def update_spent_amount(
        self, 
        category_id: str, 
        new_spent_amount: Decimal
    ) -> Optional[BudgetCategory]:
        """Update category spent amount and recalculate remaining."""
        async with await self.get_session() as session:
            try:
                # Get current category
                category = await session.get(BudgetCategory, category_id)
                if not category:
                    return None
                
                # Update amounts
                remaining_amount = category.allocated_amount - new_spent_amount
                
                query = (
                    update(BudgetCategory)
                    .where(BudgetCategory.id == category_id)
                    .values(
                        spent_amount=new_spent_amount,
                        remaining_amount=remaining_amount,
                        updated_at=func.now()
                    )
                    .returning(BudgetCategory)
                )
                
                result = await session.execute(query)
                updated_category = result.scalar_one_or_none()
                
                if updated_category:
                    await session.commit()
                    await session.refresh(updated_category)
                else:
                    await session.rollback()
                
                return updated_category
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update category spent amount: {str(e)}")
    
    async def get_category_by_name(self, budget_id: str, category_name: str) -> Optional[BudgetCategory]:
        """Get category by name within a budget."""
        return await self.get_by_field("category_name", category_name)


class BudgetAlertRepository(UserScopedRepository[BudgetAlert, dict, dict]):
    """Repository for managing budget alerts."""
    
    def __init__(self):
        super().__init__(BudgetAlert, user_field="budget_id")  # Alerts are scoped to budget
    
    async def get_unread_alerts_for_user(self, user_id: str) -> List[BudgetAlert]:
        """Get unread alerts for user's budgets."""
        async with await self.get_session() as session:
            try:
                query = (
                    select(BudgetAlert)
                    .join(Budget)
                    .where(
                        and_(
                            Budget.user_id == user_id,
                            BudgetAlert.is_read == False,
                            BudgetAlert.is_dismissed == False
                        )
                    )
                    .order_by(BudgetAlert.created_at.desc())
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get unread alerts: {str(e)}")
    
    async def mark_as_read(self, alert_id: str) -> bool:
        """Mark alert as read."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(BudgetAlert)
                    .where(BudgetAlert.id == alert_id)
                    .values(is_read=True, read_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to mark alert as read: {str(e)}")
    
    async def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss alert."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(BudgetAlert)
                    .where(BudgetAlert.id == alert_id)
                    .values(is_dismissed=True, dismissed_at=func.now())
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount > 0
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to dismiss alert: {str(e)}")


class BudgetTemplateRepository(UserScopedRepository[BudgetTemplate, BudgetTemplateCreate, BudgetTemplateUpdate]):
    """Repository for managing budget templates."""
    
    def __init__(self):
        super().__init__(BudgetTemplate)
    
    async def get_active_templates_for_user(self, user_id: str) -> List[BudgetTemplate]:
        """Get active templates for user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"is_active": True},
            order_by="-last_used_at",
            load_relationships=["template_categories"]
        )
    
    async def increment_use_count(self, template_id: str) -> Optional[BudgetTemplate]:
        """Increment template use count."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(BudgetTemplate)
                    .where(BudgetTemplate.id == template_id)
                    .values(
                        use_count=BudgetTemplate.use_count + 1,
                        last_used_at=func.now(),
                        updated_at=func.now()
                    )
                    .returning(BudgetTemplate)
                )
                
                result = await session.execute(query)
                template = result.scalar_one_or_none()
                
                if template:
                    await session.commit()
                    await session.refresh(template)
                else:
                    await session.rollback()
                
                return template
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to increment use count: {str(e)}")


class BudgetTemplateCategoryRepository(UserScopedRepository[BudgetTemplateCategory, dict, dict]):
    """Repository for managing budget template categories."""
    
    def __init__(self):
        super().__init__(BudgetTemplateCategory, user_field="template_id")
    
    async def get_categories_for_template(self, template_id: str) -> List[BudgetTemplateCategory]:
        """Get all categories for a template."""
        return await self.get_multi(
            filters={"template_id": template_id},
            order_by="priority"
        )