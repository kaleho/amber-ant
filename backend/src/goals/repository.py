"""Repository for goal management."""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.repository import UserScopedRepository
from src.goals.models import (
    Goal, GoalMilestone, GoalContribution, GoalCategory, GoalTemplate,
    GoalStatus, GoalType, MilestoneStatus
)
from src.goals.schemas import (
    GoalCreate, GoalUpdate,
    GoalMilestoneCreate, GoalMilestoneUpdate,
    GoalContributionCreate,
    GoalCategoryCreate, GoalCategoryUpdate,
    GoalTemplateCreate, GoalTemplateUpdate
)
from src.exceptions import NotFoundError, DatabaseError, ValidationError


class GoalRepository(UserScopedRepository[Goal, GoalCreate, GoalUpdate]):
    """Repository for managing financial goals."""
    
    def __init__(self):
        super().__init__(Goal)
    
    async def get_active_goals_for_user(self, user_id: str) -> List[Goal]:
        """Get all active goals for a user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"status": GoalStatus.ACTIVE},
            order_by="-created_at",
            load_relationships=["milestones", "contributions"]
        )
    
    async def get_goals_by_type(self, user_id: str, goal_type: GoalType) -> List[Goal]:
        """Get goals by type for a user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"goal_type": goal_type},
            order_by="-created_at",
            load_relationships=["milestones", "contributions"]
        )
    
    async def get_goals_by_status(self, user_id: str, status: GoalStatus) -> List[Goal]:
        """Get goals by status for a user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"status": status},
            order_by="-updated_at",
            load_relationships=["milestones", "contributions"]
        )
    
    async def get_goals_due_soon(self, user_id: str, days: int = 30) -> List[Goal]:
        """Get goals due within specified days."""
        future_date = date.today() + timedelta(days=days)
        
        async with await self.get_session() as session:
            try:
                query = (
                    select(Goal)
                    .where(
                        and_(
                            Goal.user_id == user_id,
                            Goal.status == GoalStatus.ACTIVE,
                            Goal.target_date.isnot(None),
                            Goal.target_date <= future_date
                        )
                    )
                    .order_by(Goal.target_date)
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get goals due soon: {str(e)}")
    
    async def update_goal_amount(self, goal_id: str, new_amount: Decimal) -> Optional[Goal]:
        """Update goal current amount."""
        async with await self.get_session() as session:
            try:
                goal = await session.get(Goal, goal_id)
                if not goal:
                    return None
                
                # Check if goal should be marked as completed
                should_complete = (
                    new_amount >= goal.target_amount and 
                    goal.status == GoalStatus.ACTIVE
                )
                
                update_values = {"current_amount": new_amount, "updated_at": func.now()}
                
                if should_complete:
                    update_values.update({
                        "status": GoalStatus.COMPLETED,
                        "completed_at": func.now()
                    })
                
                query = (
                    update(Goal)
                    .where(Goal.id == goal_id)
                    .values(**update_values)
                    .returning(Goal)
                )
                
                result = await session.execute(query)
                updated_goal = result.scalar_one_or_none()
                
                if updated_goal:
                    await session.commit()
                    await session.refresh(updated_goal)
                else:
                    await session.rollback()
                
                return updated_goal
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update goal amount: {str(e)}")
    
    async def get_goal_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get goal analytics for user."""
        async with await self.get_session() as session:
            try:
                # Total goals
                total_goals_query = (
                    select(func.count(Goal.id))
                    .where(Goal.user_id == user_id)
                )
                total_goals = await session.scalar(total_goals_query) or 0
                
                # Active goals
                active_goals_query = (
                    select(func.count(Goal.id))
                    .where(
                        and_(
                            Goal.user_id == user_id,
                            Goal.status == GoalStatus.ACTIVE
                        )
                    )
                )
                active_goals = await session.scalar(active_goals_query) or 0
                
                # Completed goals
                completed_goals_query = (
                    select(func.count(Goal.id))
                    .where(
                        and_(
                            Goal.user_id == user_id,
                            Goal.status == GoalStatus.COMPLETED
                        )
                    )
                )
                completed_goals = await session.scalar(completed_goals_query) or 0
                
                # Amount totals
                amounts_query = (
                    select(
                        func.sum(Goal.target_amount),
                        func.sum(Goal.current_amount),
                        func.avg(Goal.monthly_contribution)
                    )
                    .where(
                        and_(
                            Goal.user_id == user_id,
                            Goal.status == GoalStatus.ACTIVE
                        )
                    )
                )
                amounts_result = await session.execute(amounts_query)
                amounts = amounts_result.first()
                
                total_target = amounts[0] or Decimal(0)
                total_current = amounts[1] or Decimal(0)
                avg_monthly = amounts[2] or Decimal(0)
                
                # Progress percentage
                total_progress = Decimal(0)
                if total_target > 0:
                    total_progress = (total_current / total_target) * 100
                
                return {
                    "total_goals": total_goals,
                    "active_goals": active_goals,
                    "completed_goals": completed_goals,
                    "total_target_amount": total_target,
                    "total_current_amount": total_current,
                    "total_progress_percentage": total_progress,
                    "average_monthly_contribution": avg_monthly
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get goal analytics: {str(e)}")


class GoalMilestoneRepository(UserScopedRepository[GoalMilestone, GoalMilestoneCreate, GoalMilestoneUpdate]):
    """Repository for managing goal milestones."""
    
    def __init__(self):
        super().__init__(GoalMilestone, user_field="goal_id")  # Milestones are scoped to goal
    
    async def get_milestones_for_goal(self, goal_id: str) -> List[GoalMilestone]:
        """Get all milestones for a goal."""
        return await self.get_multi(
            filters={"goal_id": goal_id},
            order_by="target_date"
        )
    
    async def get_overdue_milestones(self, user_id: str) -> List[GoalMilestone]:
        """Get overdue milestones for user's goals."""
        today = date.today()
        
        async with await self.get_session() as session:
            try:
                query = (
                    select(GoalMilestone)
                    .join(Goal)
                    .where(
                        and_(
                            Goal.user_id == user_id,
                            GoalMilestone.target_date.isnot(None),
                            GoalMilestone.target_date < today,
                            GoalMilestone.status != MilestoneStatus.COMPLETED
                        )
                    )
                    .order_by(GoalMilestone.target_date)
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get overdue milestones: {str(e)}")
    
    async def complete_milestone(self, milestone_id: str, actual_amount: Optional[Decimal] = None) -> Optional[GoalMilestone]:
        """Mark milestone as completed."""
        async with await self.get_session() as session:
            try:
                update_values = {
                    "status": MilestoneStatus.COMPLETED,
                    "completed_at": func.now(),
                    "updated_at": func.now()
                }
                
                if actual_amount is not None:
                    update_values["actual_amount"] = actual_amount
                
                query = (
                    update(GoalMilestone)
                    .where(GoalMilestone.id == milestone_id)
                    .values(**update_values)
                    .returning(GoalMilestone)
                )
                
                result = await session.execute(query)
                milestone = result.scalar_one_or_none()
                
                if milestone:
                    await session.commit()
                    await session.refresh(milestone)
                else:
                    await session.rollback()
                
                return milestone
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to complete milestone: {str(e)}")


class GoalContributionRepository(UserScopedRepository[GoalContribution, GoalContributionCreate, dict]):
    """Repository for managing goal contributions."""
    
    def __init__(self):
        super().__init__(GoalContribution, user_field="goal_id")  # Contributions are scoped to goal
    
    async def get_contributions_for_goal(
        self, 
        goal_id: str, 
        limit: int = 50
    ) -> List[GoalContribution]:
        """Get contributions for a goal."""
        return await self.get_multi(
            filters={"goal_id": goal_id},
            order_by="-contribution_date",
            limit=limit
        )
    
    async def get_contributions_by_date_range(
        self,
        goal_id: str,
        start_date: date,
        end_date: date
    ) -> List[GoalContribution]:
        """Get contributions within date range."""
        async with await self.get_session() as session:
            try:
                query = (
                    select(GoalContribution)
                    .where(
                        and_(
                            GoalContribution.goal_id == goal_id,
                            GoalContribution.contribution_date >= start_date,
                            GoalContribution.contribution_date <= end_date
                        )
                    )
                    .order_by(GoalContribution.contribution_date.desc())
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get contributions by date range: {str(e)}")
    
    async def get_total_contributions_for_goal(self, goal_id: str) -> Decimal:
        """Get total contributions for a goal."""
        async with await self.get_session() as session:
            try:
                query = (
                    select(func.sum(GoalContribution.amount))
                    .where(GoalContribution.goal_id == goal_id)
                )
                
                result = await session.execute(query)
                total = result.scalar()
                return total or Decimal(0)
                
            except Exception as e:
                raise DatabaseError(f"Failed to get total contributions: {str(e)}")


class GoalCategoryRepository(UserScopedRepository[GoalCategory, GoalCategoryCreate, GoalCategoryUpdate]):
    """Repository for managing goal categories."""
    
    def __init__(self):
        super().__init__(GoalCategory)
    
    async def get_active_categories_for_user(self, user_id: str) -> List[GoalCategory]:
        """Get active categories for user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"is_active": True},
            order_by="sort_order"
        )


class GoalTemplateRepository(UserScopedRepository[GoalTemplate, GoalTemplateCreate, GoalTemplateUpdate]):
    """Repository for managing goal templates."""
    
    def __init__(self):
        super().__init__(GoalTemplate, user_field="created_by")
    
    async def get_public_templates(self) -> List[GoalTemplate]:
        """Get all public templates."""
        return await self.get_multi(
            filters={"is_public": True, "is_active": True},
            order_by="-use_count"
        )
    
    async def get_templates_by_type(self, goal_type: GoalType) -> List[GoalTemplate]:
        """Get templates by goal type."""
        return await self.get_multi(
            filters={
                "goal_type": goal_type,
                "is_public": True,
                "is_active": True
            },
            order_by="-use_count"
        )
    
    async def increment_use_count(self, template_id: str) -> Optional[GoalTemplate]:
        """Increment template use count."""
        async with await self.get_session() as session:
            try:
                query = (
                    update(GoalTemplate)
                    .where(GoalTemplate.id == template_id)
                    .values(
                        use_count=GoalTemplate.use_count + 1,
                        updated_at=func.now()
                    )
                    .returning(GoalTemplate)
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