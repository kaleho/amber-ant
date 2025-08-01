"""Budget management service."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.budgets.repository import (
    BudgetRepository, BudgetCategoryRepository, BudgetAlertRepository,
    BudgetTemplateRepository, BudgetTemplateCategoryRepository
)
from src.budgets.schemas import (
    BudgetCreate, BudgetUpdate, Budget, BudgetSummary,
    BudgetCategoryCreate, BudgetCategoryUpdate, BudgetCategory,
    BudgetTemplateCreate, BudgetTemplateUpdate, BudgetTemplate,
    BudgetAnalytics, CreateBudgetFromTemplate
)
from src.budgets.models import BudgetStatus, AlertType, BudgetPeriod
from src.exceptions import NotFoundError, ValidationError, DatabaseError, BusinessLogicError

logger = logging.getLogger(__name__)


class BudgetService:
    """Service for managing budgets."""
    
    def __init__(self):
        self.budget_repo = BudgetRepository()
        self.category_repo = BudgetCategoryRepository()
        self.alert_repo = BudgetAlertRepository()
        self.template_repo = BudgetTemplateRepository()
        self.template_category_repo = BudgetTemplateCategoryRepository()
    
    async def create_budget(self, budget_data: BudgetCreate, user_id: str, created_by: str) -> Budget:
        """Create a new budget with categories."""
        try:
            # Validate category allocations
            if budget_data.categories:
                total_allocated = sum(cat.allocated_amount for cat in budget_data.categories)
                if total_allocated > budget_data.total_amount:
                    raise ValidationError("Total category allocations exceed budget total")
            
            # Create budget
            budget_dict = budget_data.model_dump(exclude={"categories"})
            budget = await self.budget_repo.create_for_user(
                BudgetCreate(**budget_dict),
                user_id=user_id,
                created_by=created_by
            )
            
            # Create categories if provided
            if budget_data.categories:
                for category_data in budget_data.categories:
                    category_dict = category_data.model_dump()
                    category_dict["remaining_amount"] = category_data.allocated_amount
                    
                    await self.category_repo.create(
                        BudgetCategoryCreate(**category_dict),
                        budget_id=budget.id
                    )
            
            # Load full budget with relationships
            full_budget = await self.budget_repo.get_by_id(
                budget.id, 
                load_relationships=["categories", "alerts"]
            )
            
            logger.info("Created budget", budget_id=budget.id, user_id=user_id)
            return Budget.model_validate(full_budget)
            
        except Exception as e:
            logger.error("Failed to create budget", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to create budget: {str(e)}")
    
    async def get_budget(self, budget_id: str, user_id: str) -> Optional[Budget]:
        """Get budget by ID for user."""
        budget = await self.budget_repo.get_by_id_for_user(
            budget_id, 
            user_id,
            load_relationships=["categories", "alerts"]
        )
        return Budget.model_validate(budget) if budget else None
    
    async def get_user_budgets(self, user_id: str, status: Optional[BudgetStatus] = None) -> List[Budget]:
        """Get all budgets for user, optionally filtered by status."""
        filters = {"status": status} if status else None
        budgets = await self.budget_repo.get_multi_for_user(
            user_id=user_id,
            filters=filters,
            order_by="-created_at",
            load_relationships=["categories", "alerts"]
        )
        return [Budget.model_validate(budget) for budget in budgets]
    
    async def get_current_budget(self, user_id: str) -> Optional[Budget]:
        """Get current active budget for user."""
        budget = await self.budget_repo.get_current_budget_for_user(user_id)
        return Budget.model_validate(budget) if budget else None
    
    async def update_budget(self, budget_id: str, budget_data: BudgetUpdate, user_id: str) -> Optional[Budget]:
        """Update budget."""
        budget = await self.budget_repo.get_by_id_for_user(budget_id, user_id)
        if not budget:
            raise NotFoundError("Budget not found")
        
        updated_budget = await self.budget_repo.update(budget_id, budget_data)
        if not updated_budget:
            return None
        
        # Load full budget with relationships
        full_budget = await self.budget_repo.get_by_id(
            budget_id,
            load_relationships=["categories", "alerts"]
        )
        
        logger.info("Updated budget", budget_id=budget_id, user_id=user_id)
        return Budget.model_validate(full_budget)
    
    async def delete_budget(self, budget_id: str, user_id: str) -> bool:
        """Delete budget (soft delete - set status to inactive)."""
        budget = await self.budget_repo.get_by_id_for_user(budget_id, user_id)
        if not budget:
            raise NotFoundError("Budget not found")
        
        # Soft delete by setting status to inactive
        await self.budget_repo.update(budget_id, BudgetUpdate(status=BudgetStatus.INACTIVE))
        
        logger.info("Deleted budget", budget_id=budget_id, user_id=user_id)
        return True
    
    async def update_budget_spending(self, budget_id: str, new_spent_amount: Decimal) -> Optional[Budget]:
        """Update budget spent amount and check for alerts."""
        budget = await self.budget_repo.update_spent_amount(budget_id, new_spent_amount)
        if not budget:
            return None
        
        # Check for alert thresholds
        await self._check_and_create_alerts(budget)
        
        # Load full budget with relationships
        full_budget = await self.budget_repo.get_by_id(
            budget_id,
            load_relationships=["categories", "alerts"]
        )
        
        return Budget.model_validate(full_budget)
    
    async def get_budget_analytics(self, user_id: str) -> BudgetAnalytics:
        """Get budget analytics for user."""
        analytics_data = await self.budget_repo.get_budget_analytics(user_id)
        
        # Add additional computed metrics
        analytics_data.update({
            "budgets_over_threshold": 0,  # TODO: Calculate from actual data
            "budgets_over_budget": 0,     # TODO: Calculate from actual data
            "most_overspent_category": None,  # TODO: Calculate from category data
            "best_performing_category": None, # TODO: Calculate from category data
            "spending_trend": "stable"    # TODO: Calculate from historical data
        })
        
        return BudgetAnalytics(**analytics_data)
    
    # Category management
    async def add_category_to_budget(
        self, 
        budget_id: str, 
        category_data: BudgetCategoryCreate,
        user_id: str
    ) -> BudgetCategory:
        """Add category to budget."""
        # Verify budget exists and belongs to user
        budget = await self.budget_repo.get_by_id_for_user(budget_id, user_id)
        if not budget:
            raise NotFoundError("Budget not found")
        
        # Check total allocations don't exceed budget
        existing_categories = await self.category_repo.get_categories_for_budget(budget_id)
        total_allocated = sum(cat.allocated_amount for cat in existing_categories)
        
        if total_allocated + category_data.allocated_amount > budget.total_amount:
            raise ValidationError("Adding this category would exceed budget total")
        
        category_dict = category_data.model_dump()
        category_dict["remaining_amount"] = category_data.allocated_amount
        
        category = await self.category_repo.create(
            BudgetCategoryCreate(**category_dict),
            budget_id=budget_id
        )
        
        logger.info("Added category to budget", budget_id=budget_id, category_id=category.id)
        return BudgetCategory.model_validate(category)
    
    async def update_category(
        self, 
        category_id: str, 
        category_data: BudgetCategoryUpdate,
        user_id: str
    ) -> Optional[BudgetCategory]:
        """Update budget category."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")
        
        # Verify budget belongs to user
        budget = await self.budget_repo.get_by_id_for_user(category.budget_id, user_id)
        if not budget:
            raise NotFoundError("Budget not found")
        
        updated_category = await self.category_repo.update(category_id, category_data)
        return BudgetCategory.model_validate(updated_category) if updated_category else None
    
    async def delete_category(self, category_id: str, user_id: str) -> bool:
        """Delete budget category."""
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")
        
        # Verify budget belongs to user
        budget = await self.budget_repo.get_by_id_for_user(category.budget_id, user_id)
        if not budget:
            raise NotFoundError("Budget not found")
        
        success = await self.category_repo.delete(category_id)
        if success:
            logger.info("Deleted budget category", category_id=category_id)
        
        return success
    
    # Template management
    async def create_template(
        self, 
        template_data: BudgetTemplateCreate, 
        user_id: str, 
        created_by: str
    ) -> BudgetTemplate:
        """Create budget template."""
        try:
            # Create template
            template_dict = template_data.model_dump(exclude={"categories"})
            template = await self.template_repo.create_for_user(
                BudgetTemplateCreate(**template_dict),
                user_id=user_id,
                created_by=created_by
            )
            
            # Create template categories
            if template_data.categories:
                for category_data in template_data.categories:
                    # Calculate percentage of total
                    percentage = (category_data.allocated_amount / template_data.total_amount) * 100
                    
                    category_dict = category_data.model_dump()
                    category_dict["percentage_of_total"] = percentage
                    
                    await self.template_category_repo.create(
                        category_dict,
                        template_id=template.id
                    )
            
            logger.info("Created budget template", template_id=template.id, user_id=user_id)
            return BudgetTemplate.model_validate(template)
            
        except Exception as e:
            logger.error("Failed to create template", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to create template: {str(e)}")
    
    async def create_budget_from_template(
        self, 
        request: CreateBudgetFromTemplate, 
        user_id: str,
        created_by: str
    ) -> Budget:
        """Create budget from template."""
        # Get template
        template = await self.template_repo.get_by_id_for_user(
            request.template_id, 
            user_id,
            load_relationships=["template_categories"]
        )
        if not template:
            raise NotFoundError("Template not found")
        
        # Calculate end date based on period type
        end_date = self._calculate_end_date(request.start_date, template.period_type)
        
        # Create budget from template
        budget_data = BudgetCreate(
            name=request.name or template.name,
            description=template.description,
            total_amount=request.total_amount or template.total_amount,
            period_type=template.period_type,
            start_date=request.start_date,
            end_date=end_date,
            warning_threshold=template.warning_threshold,
            critical_threshold=template.critical_threshold,
            categories=[]
        )
        
        # Add categories from template
        if template.template_categories:
            total_amount = budget_data.total_amount
            for template_cat in template.template_categories:
                # Calculate allocated amount based on percentage
                allocated_amount = (template_cat.percentage_of_total / 100) * total_amount
                
                category_data = BudgetCategoryCreate(
                    category_name=template_cat.category_name,
                    category_id=template_cat.category_id,
                    allocated_amount=allocated_amount,
                    is_essential=template_cat.is_essential,
                    priority=template_cat.priority
                )
                budget_data.categories.append(category_data)
        
        # Create budget
        budget = await self.create_budget(budget_data, user_id, created_by)
        
        # Increment template use count
        await self.template_repo.increment_use_count(request.template_id)
        
        logger.info("Created budget from template", 
                   budget_id=budget.id, 
                   template_id=request.template_id,
                   user_id=user_id)
        
        return budget
    
    # Alert management
    async def get_user_alerts(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get alerts for user's budgets."""
        if unread_only:
            alerts = await self.alert_repo.get_unread_alerts_for_user(user_id)
        else:
            # TODO: Implement get_all_alerts_for_user
            alerts = await self.alert_repo.get_unread_alerts_for_user(user_id)
        
        return [
            {
                "id": alert.id,
                "budget_id": alert.budget_id,
                "alert_type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "is_read": alert.is_read,
                "created_at": alert.created_at
            }
            for alert in alerts
        ]
    
    async def mark_alert_as_read(self, alert_id: str, user_id: str) -> bool:
        """Mark alert as read."""
        # TODO: Verify alert belongs to user's budget
        return await self.alert_repo.mark_as_read(alert_id)
    
    async def dismiss_alert(self, alert_id: str, user_id: str) -> bool:
        """Dismiss alert."""
        # TODO: Verify alert belongs to user's budget
        return await self.alert_repo.dismiss_alert(alert_id)
    
    # Private helper methods
    async def _check_and_create_alerts(self, budget) -> None:
        """Check budget thresholds and create alerts if needed."""
        utilization = budget.utilization_percentage
        
        # Check warning threshold
        if utilization >= budget.warning_threshold and not budget.is_warning_threshold_reached:
            await self._create_alert(
                budget.id,
                AlertType.WARNING,
                "Budget Warning",
                f"Budget '{budget.name}' has reached {utilization:.1f}% utilization",
                budget.warning_threshold,
                budget.spent_amount
            )
        
        # Check critical threshold
        if utilization >= budget.critical_threshold and not budget.is_critical_threshold_reached:
            await self._create_alert(
                budget.id,
                AlertType.CRITICAL,
                "Budget Critical",
                f"Budget '{budget.name}' has reached {utilization:.1f}% utilization",
                budget.critical_threshold,
                budget.spent_amount
            )
        
        # Check if over budget
        if budget.is_over_budget:
            await self._create_alert(
                budget.id,
                AlertType.EXCEEDED,
                "Budget Exceeded",
                f"Budget '{budget.name}' has been exceeded by {budget.spent_amount - budget.total_amount}",
                None,
                budget.spent_amount
            )
    
    async def _create_alert(
        self,
        budget_id: str,
        alert_type: AlertType,
        title: str,
        message: str,
        threshold_percentage: Optional[Decimal],
        amount_at_alert: Decimal
    ) -> None:
        """Create budget alert."""
        alert_data = {
            "id": str(uuid4()),
            "budget_id": budget_id,
            "alert_type": alert_type,
            "title": title,
            "message": message,
            "threshold_percentage": threshold_percentage,
            "amount_at_alert": amount_at_alert
        }
        
        await self.alert_repo.create(alert_data)
    
    def _calculate_end_date(self, start_date: date, period_type: BudgetPeriod) -> date:
        """Calculate end date based on period type."""
        if period_type == BudgetPeriod.WEEKLY:
            return start_date + timedelta(days=6)
        elif period_type == BudgetPeriod.MONTHLY:
            # Add one month and subtract one day
            if start_date.month == 12:
                return date(start_date.year + 1, 1, start_date.day) - timedelta(days=1)
            else:
                return date(start_date.year, start_date.month + 1, start_date.day) - timedelta(days=1)
        elif period_type == BudgetPeriod.QUARTERLY:
            return start_date + timedelta(days=89)  # Approximately 3 months
        elif period_type == BudgetPeriod.YEARLY:
            return date(start_date.year + 1, start_date.month, start_date.day) - timedelta(days=1)
        else:
            return start_date + timedelta(days=30)  # Default to monthly