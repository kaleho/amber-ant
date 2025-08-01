"""Goal management service with comprehensive business logic."""
import structlog
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.goals.repository import (
    GoalRepository, GoalMilestoneRepository, GoalContributionRepository,
    GoalCategoryRepository, GoalTemplateRepository
)
from src.goals.schemas import (
    SavingsGoalCreate, SavingsGoalUpdate, SavingsGoalResponse, GoalListResponse,
    GoalSummaryResponse, GoalAnalysisResponse, GoalContributionResponse,
    GoalContributionCreate, GoalMilestoneResponse, GoalMilestoneCreate,
    GoalInsightResponse
)
from src.goals.models import GoalStatus, GoalType, MilestoneStatus
from src.exceptions import NotFoundError, ValidationError, DatabaseError, BusinessLogicError

logger = structlog.get_logger(__name__)


class GoalService:
    """Service for managing financial goals with comprehensive features."""
    
    def __init__(self):
        self.goal_repo = GoalRepository()
        self.milestone_repo = GoalMilestoneRepository()
        self.contribution_repo = GoalContributionRepository()
        self.category_repo = GoalCategoryRepository()
        self.template_repo = GoalTemplateRepository()
    
    # Core CRUD operations
    async def get_goals(
        self, 
        user_id: str, 
        page: int = 1, 
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SavingsGoalResponse]:
        """Get goals with pagination and filtering."""
        try:
            # Apply filters
            query_filters = {}
            if filters:
                if "status" in filters:
                    query_filters["status"] = filters["status"]
                if "goal_type" in filters:
                    query_filters["goal_type"] = filters["goal_type"]
                if "name_contains" in filters:
                    query_filters["name_ilike"] = f"%{filters['name_contains']}%"
            
            # Get goals with pagination
            goals = await self.goal_repo.get_multi_for_user(
                user_id=user_id,
                filters=query_filters,
                offset=(page - 1) * per_page,
                limit=per_page,
                order_by="-created_at",
                load_relationships=["milestones", "contributions"]
            )
            
            return [SavingsGoalResponse.model_validate(goal) for goal in goals]
            
        except Exception as e:
            logger.error("Failed to get goals", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to get goals: {str(e)}")
    
    async def get_goal(self, goal_id: str, user_id: str) -> SavingsGoalResponse:
        """Get specific goal by ID."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(
                goal_id,
                user_id,
                load_relationships=["milestones", "contributions"]
            )
            if not goal:
                raise NotFoundError("Goal not found")
            
            return SavingsGoalResponse.model_validate(goal)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to get goal", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to get goal: {str(e)}")
    
    async def create_goal(self, user_id: str, goal_data: SavingsGoalCreate) -> SavingsGoalResponse:
        """Create a new savings goal."""
        try:
            # Validate goal data
            if goal_data.target_amount <= 0:
                raise ValidationError("Target amount must be positive")
            
            if goal_data.target_date and goal_data.target_date <= date.today():
                raise ValidationError("Target date must be in the future")
            
            # Create goal
            goal_dict = goal_data.model_dump(exclude={"milestones", "initial_contribution"})
            goal_dict["user_id"] = user_id
            goal_dict["current_amount"] = Decimal("0")
            goal_dict["remaining_amount"] = goal_data.target_amount
            goal_dict["status"] = GoalStatus.ACTIVE
            goal_dict["created_at"] = datetime.utcnow()
            goal_dict["updated_at"] = datetime.utcnow()
            
            goal = await self.goal_repo.create(goal_dict)
            
            # Add initial contribution if provided
            if goal_data.initial_contribution and goal_data.initial_contribution > 0:
                await self.create_contribution(
                    goal_id=goal.id,
                    user_id=user_id,
                    contribution_data=GoalContributionCreate(
                        amount=goal_data.initial_contribution,
                        description="Initial contribution",
                        source_type="manual"
                    )
                )
            
            # Create milestones if provided
            if goal_data.milestones:
                for milestone_data in goal_data.milestones:
                    await self.milestone_repo.create(
                        milestone_data.model_dump(),
                        goal_id=goal.id
                    )
            
            # Load full goal with relationships
            full_goal = await self.goal_repo.get_by_id(
                goal.id,
                load_relationships=["milestones", "contributions"]
            )
            
            logger.info("Created savings goal", goal_id=goal.id, user_id=user_id)
            return SavingsGoalResponse.model_validate(full_goal)
            
        except (ValidationError, NotFoundError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to create goal", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to create goal: {str(e)}")
    
    async def update_goal(
        self, 
        goal_id: str, 
        user_id: str, 
        goal_data: SavingsGoalUpdate
    ) -> SavingsGoalResponse:
        """Update goal information."""
        try:
            # Verify goal exists and belongs to user
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            # Validate updates
            if goal_data.target_amount and goal_data.target_amount <= 0:
                raise ValidationError("Target amount must be positive")
            
            if goal_data.target_date and goal_data.target_date <= date.today():
                raise ValidationError("Target date must be in the future")
            
            # Update goal
            update_dict = goal_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            # Recalculate remaining amount if target changed
            if goal_data.target_amount:
                update_dict["remaining_amount"] = goal_data.target_amount - goal.current_amount
            
            updated_goal = await self.goal_repo.update(goal_id, update_dict)
            
            # Load full goal with relationships
            full_goal = await self.goal_repo.get_by_id(
                goal_id,
                load_relationships=["milestones", "contributions"]
            )
            
            logger.info("Updated goal", goal_id=goal_id, user_id=user_id)
            return SavingsGoalResponse.model_validate(full_goal)
            
        except (ValidationError, NotFoundError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to update goal", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to update goal: {str(e)}")
    
    async def delete_goal(self, goal_id: str, user_id: str) -> bool:
        """Delete a goal (soft delete)."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            # Soft delete by setting status
            await self.goal_repo.update(goal_id, {
                "status": GoalStatus.CANCELLED,
                "updated_at": datetime.utcnow()
            })
            
            logger.info("Deleted goal", goal_id=goal_id, user_id=user_id)
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to delete goal", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to delete goal: {str(e)}")
    
    # Contribution management
    async def get_goal_contributions(
        self, 
        goal_id: str, 
        user_id: str, 
        limit: int = 50
    ) -> List[GoalContributionResponse]:
        """Get contributions for a specific goal."""
        try:
            # Verify goal belongs to user
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            contributions = await self.contribution_repo.get_contributions_for_goal(goal_id, limit)
            return [GoalContributionResponse.model_validate(c) for c in contributions]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to get contributions", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to get contributions: {str(e)}")
    
    async def create_contribution(
        self, 
        goal_id: str, 
        user_id: str, 
        contribution_data: GoalContributionCreate
    ) -> GoalContributionResponse:
        """Add a contribution to a goal."""
        try:
            # Verify goal exists and belongs to user
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            if contribution_data.amount <= 0:
                raise ValidationError("Contribution amount must be positive")
            
            # Create contribution
            contribution_dict = contribution_data.model_dump()
            contribution_dict["goal_id"] = goal_id
            contribution_dict["contribution_date"] = datetime.utcnow().date()
            contribution_dict["created_at"] = datetime.utcnow()
            
            contribution = await self.contribution_repo.create(contribution_dict)
            
            # Update goal amounts
            new_current = goal.current_amount + contribution_data.amount
            new_remaining = goal.target_amount - new_current
            
            # Check if goal is completed
            status = GoalStatus.COMPLETED if new_remaining <= 0 else goal.status
            completed_at = datetime.utcnow() if status == GoalStatus.COMPLETED else None
            
            await self.goal_repo.update(goal_id, {
                "current_amount": new_current,
                "remaining_amount": max(new_remaining, Decimal("0")),
                "status": status,
                "completed_at": completed_at,
                "updated_at": datetime.utcnow()
            })
            
            # Check and complete milestones
            await self._check_and_complete_milestones(goal_id, new_current)
            
            logger.info("Added contribution to goal", 
                       goal_id=goal_id, 
                       amount=contribution_data.amount,
                       user_id=user_id)
            
            return GoalContributionResponse.model_validate(contribution)
            
        except (ValidationError, NotFoundError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to create contribution", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to create contribution: {str(e)}")
    
    # Milestone management
    async def get_goal_milestones(self, goal_id: str, user_id: str) -> List[GoalMilestoneResponse]:
        """Get milestones for a specific goal."""
        try:
            # Verify goal belongs to user
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            milestones = await self.milestone_repo.get_milestones_for_goal(goal_id)
            return [GoalMilestoneResponse.model_validate(m) for m in milestones]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to get milestones", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to get milestones: {str(e)}")
    
    async def create_milestone(
        self, 
        goal_id: str, 
        user_id: str, 
        milestone_data: GoalMilestoneCreate
    ) -> GoalMilestoneResponse:
        """Add a milestone to a goal."""
        try:
            # Verify goal exists and belongs to user
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            if milestone_data.target_amount <= 0:
                raise ValidationError("Milestone target amount must be positive")
            
            if milestone_data.target_amount > goal.target_amount:
                raise ValidationError("Milestone target cannot exceed goal target")
            
            # Create milestone
            milestone_dict = milestone_data.model_dump()
            milestone_dict["goal_id"] = goal_id
            milestone_dict["status"] = MilestoneStatus.PENDING
            milestone_dict["created_at"] = datetime.utcnow()
            
            milestone = await self.milestone_repo.create(milestone_dict)
            
            logger.info("Added milestone to goal", goal_id=goal_id, milestone_id=milestone.id)
            return GoalMilestoneResponse.model_validate(milestone)
            
        except (ValidationError, NotFoundError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to create milestone", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to create milestone: {str(e)}")
    
    async def update_milestone(
        self, 
        milestone_id: str, 
        user_id: str, 
        milestone_data: Dict[str, Any]
    ) -> GoalMilestoneResponse:
        """Update a goal milestone."""
        try:
            milestone = await self.milestone_repo.get_by_id(milestone_id)
            if not milestone:
                raise NotFoundError("Milestone not found")
            
            # Verify goal belongs to user
            goal = await self.goal_repo.get_by_id_for_user(milestone.goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            # Update milestone
            milestone_data["updated_at"] = datetime.utcnow()
            updated_milestone = await self.milestone_repo.update(milestone_id, milestone_data)
            
            return GoalMilestoneResponse.model_validate(updated_milestone)
            
        except (ValidationError, NotFoundError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to update milestone", milestone_id=milestone_id, error=str(e))
            raise BusinessLogicError(f"Failed to update milestone: {str(e)}")
    
    async def delete_milestone(self, milestone_id: str, user_id: str) -> bool:
        """Delete a goal milestone."""
        try:
            milestone = await self.milestone_repo.get_by_id(milestone_id)
            if not milestone:
                raise NotFoundError("Milestone not found")
            
            # Verify goal belongs to user
            goal = await self.goal_repo.get_by_id_for_user(milestone.goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            success = await self.milestone_repo.delete(milestone_id)
            if success:
                logger.info("Deleted milestone", milestone_id=milestone_id)
            
            return success
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to delete milestone", milestone_id=milestone_id, error=str(e))
            raise BusinessLogicError(f"Failed to delete milestone: {str(e)}")
    
    # Goal management operations
    async def pause_goal(self, goal_id: str, user_id: str) -> SavingsGoalResponse:
        """Pause a goal."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            await self.goal_repo.update(goal_id, {
                "status": GoalStatus.PAUSED,
                "updated_at": datetime.utcnow()
            })
            
            updated_goal = await self.goal_repo.get_by_id(
                goal_id,
                load_relationships=["milestones", "contributions"]
            )
            
            return SavingsGoalResponse.model_validate(updated_goal)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to pause goal", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to pause goal: {str(e)}")
    
    async def resume_goal(self, goal_id: str, user_id: str) -> SavingsGoalResponse:
        """Resume a paused goal."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            await self.goal_repo.update(goal_id, {
                "status": GoalStatus.ACTIVE,
                "updated_at": datetime.utcnow()
            })
            
            updated_goal = await self.goal_repo.get_by_id(
                goal_id,
                load_relationships=["milestones", "contributions"]
            )
            
            return SavingsGoalResponse.model_validate(updated_goal)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to resume goal", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to resume goal: {str(e)}")
    
    async def complete_goal(self, goal_id: str, user_id: str) -> SavingsGoalResponse:
        """Mark a goal as completed."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            await self.goal_repo.update(goal_id, {
                "status": GoalStatus.COMPLETED,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            updated_goal = await self.goal_repo.get_by_id(
                goal_id,
                load_relationships=["milestones", "contributions"]
            )
            
            return SavingsGoalResponse.model_validate(updated_goal)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to complete goal", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to complete goal: {str(e)}")
    
    # Analytics and reporting
    async def get_goals_summary(self, user_id: str) -> GoalSummaryResponse:
        """Get goals summary for user."""
        try:
            analytics = await self.goal_repo.get_goal_analytics(user_id)
            
            # Calculate additional metrics
            completion_rate = 0
            if analytics["total_goals"] > 0:
                completion_rate = (analytics["completed_goals"] / analytics["total_goals"]) * 100
            
            # Get goals due soon
            goals_due_soon = await self.goal_repo.get_goals_due_soon(user_id, days=30)
            
            return GoalSummaryResponse(
                total_goals=analytics["total_goals"],
                active_goals=analytics["active_goals"],
                completed_goals=analytics["completed_goals"],
                paused_goals=0,  # TODO: Add to analytics
                total_target_amount=analytics["total_target_amount"],
                total_current_amount=analytics["total_current_amount"],
                total_progress_percentage=float(analytics["total_progress_percentage"]),
                average_monthly_contribution=analytics["average_monthly_contribution"],
                completion_rate=completion_rate,
                goals_due_soon=len(goals_due_soon),
                on_track_goals=0,  # TODO: Calculate
                behind_schedule_goals=0  # TODO: Calculate
            )
            
        except Exception as e:
            logger.error("Failed to get goals summary", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to get summary: {str(e)}")
    
    async def get_goal_analysis(
        self, 
        goal_id: str, 
        user_id: str, 
        analysis_period: int = 90
    ) -> GoalAnalysisResponse:
        """Get detailed goal analysis."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            # Calculate analysis metrics
            progress_percentage = 0
            if goal.target_amount > 0:
                progress_percentage = (goal.current_amount / goal.target_amount) * 100
            
            # Get contributions for analysis period
            end_date = date.today()
            start_date = end_date - timedelta(days=analysis_period)
            contributions = await self.contribution_repo.get_contributions_by_date_range(
                goal_id, start_date, end_date
            )
            
            # Calculate trends
            total_period_contributions = sum(c.amount for c in contributions)
            avg_monthly_contribution = total_period_contributions / (analysis_period / 30)
            
            # Projection
            remaining_needed = goal.target_amount - goal.current_amount
            months_to_completion = None
            if avg_monthly_contribution > 0:
                months_to_completion = float(remaining_needed / avg_monthly_contribution)
            
            return GoalAnalysisResponse(
                goal_id=goal_id,
                current_progress=float(progress_percentage),
                monthly_average=float(avg_monthly_contribution),
                projected_completion_months=months_to_completion,
                total_contributions_period=float(total_period_contributions),
                contribution_frequency=len(contributions),
                is_on_track=avg_monthly_contribution >= (goal.monthly_contribution or 0),
                recommendations=[
                    "Consider increasing monthly contributions to stay on track"
                    if avg_monthly_contribution < (goal.monthly_contribution or 0)
                    else "Great progress! You're on track to meet your goal"
                ]
            )
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to get goal analysis", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to get analysis: {str(e)}")
    
    # Insights and recommendations
    async def get_goal_insights(
        self, 
        user_id: str, 
        unread_only: bool = False, 
        limit: int = 10
    ) -> List[GoalInsightResponse]:
        """Get goal insights and recommendations for user."""
        try:
            insights = []
            
            # Get user's active goals
            active_goals = await self.goal_repo.get_active_goals_for_user(user_id)
            
            for goal in active_goals[:limit]:
                # Calculate progress
                progress = 0
                if goal.target_amount > 0:
                    progress = (goal.current_amount / goal.target_amount) * 100
                
                # Generate insights based on progress and timeline
                insight_type = "progress"
                title = f"Goal Progress Update: {goal.name}"
                message = f"You're {progress:.1f}% towards your {goal.name} goal"
                
                if progress < 25 and goal.target_date:
                    days_remaining = (goal.target_date - date.today()).days
                    if days_remaining < 30:
                        insight_type = "warning"
                        title = f"Goal Deadline Approaching: {goal.name}"
                        message = f"Your {goal.name} goal is due in {days_remaining} days. Consider increasing contributions."
                
                insights.append(GoalInsightResponse(
                    id=str(uuid4()),
                    goal_id=goal.id,
                    insight_type=insight_type,
                    title=title,
                    message=message,
                    priority="medium",
                    is_read=False,
                    created_at=datetime.utcnow(),
                    action_required=progress < 50,
                    recommended_actions=[
                        "Increase monthly contribution",
                        "Review spending to find extra funds"
                    ] if progress < 50 else []
                ))
            
            return insights[:limit]
            
        except Exception as e:
            logger.error("Failed to get goal insights", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to get insights: {str(e)}")
    
    async def mark_insight_as_read(self, insight_id: str, user_id: str) -> bool:
        """Mark goal insight as read."""
        try:
            # TODO: Implement insight storage and reading
            # For now, return True as a placeholder
            return True
            
        except Exception as e:
            logger.error("Failed to mark insight as read", insight_id=insight_id, error=str(e))
            raise BusinessLogicError(f"Failed to mark insight: {str(e)}")
    
    async def dismiss_insight(self, insight_id: str, user_id: str) -> bool:
        """Dismiss a goal insight."""
        try:
            # TODO: Implement insight dismissal
            # For now, return True as a placeholder
            return True
            
        except Exception as e:
            logger.error("Failed to dismiss insight", insight_id=insight_id, error=str(e))
            raise BusinessLogicError(f"Failed to dismiss insight: {str(e)}")
    
    # Utility methods
    async def get_goal_category_suggestions(self, user_id: str) -> List[str]:
        """Get goal category suggestions."""
        try:
            # Common goal categories
            suggestions = [
                "Emergency Fund",
                "Vacation",
                "Home Down Payment",
                "Car Purchase",
                "Education",
                "Retirement",
                "Wedding",
                "Debt Payoff",
                "Investment",
                "Business Startup"
            ]
            
            return suggestions
            
        except Exception as e:
            logger.error("Failed to get category suggestions", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to get suggestions: {str(e)}")
    
    async def get_goal_templates(
        self, 
        user_id: str, 
        goal_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available goal templates."""
        try:
            templates = await self.template_repo.get_public_templates()
            
            if goal_type:
                templates = [t for t in templates if t.goal_type == goal_type]
            
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "goal_type": t.goal_type,
                    "default_target_amount": float(t.default_target_amount or 0),
                    "default_monthly_contribution": float(t.default_monthly_contribution or 0),
                    "use_count": t.use_count
                }
                for t in templates
            ]
            
        except Exception as e:
            logger.error("Failed to get templates", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to get templates: {str(e)}")
    
    async def apply_goal_template(
        self, 
        template_id: str, 
        user_id: str, 
        template_data: Dict[str, Any]
    ) -> SavingsGoalResponse:
        """Apply a goal template to create a new goal."""
        try:
            template = await self.template_repo.get_by_id(template_id)
            if not template:
                raise NotFoundError("Template not found")
            
            # Create goal from template
            goal_data = SavingsGoalCreate(
                name=template_data.get("name", template.name),
                description=template.description,
                goal_type=template.goal_type,
                target_amount=Decimal(str(template_data.get("target_amount", template.default_target_amount))),
                monthly_contribution=Decimal(str(template_data.get("monthly_contribution", template.default_monthly_contribution or 0))),
                target_date=template_data.get("target_date"),
                initial_contribution=Decimal(str(template_data.get("initial_contribution", 0)))
            )
            
            goal = await self.create_goal(user_id, goal_data)
            
            # Increment template use count
            await self.template_repo.increment_use_count(template_id)
            
            return goal
            
        except (ValidationError, NotFoundError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to apply template", template_id=template_id, error=str(e))
            raise BusinessLogicError(f"Failed to apply template: {str(e)}")
    
    # Auto-save functionality
    async def enable_auto_save(
        self, 
        goal_id: str, 
        user_id: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enable automatic savings for a goal."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            # Validate auto-save config
            if "amount" not in config or config["amount"] <= 0:
                raise ValidationError("Auto-save amount must be positive")
            
            if "frequency" not in config:
                raise ValidationError("Auto-save frequency is required")
            
            # Update goal with auto-save settings
            auto_save_settings = {
                "enabled": True,
                "amount": float(config["amount"]),
                "frequency": config["frequency"],
                "next_date": config.get("start_date", date.today().isoformat())
            }
            
            await self.goal_repo.update(goal_id, {
                "auto_save_settings": auto_save_settings,
                "updated_at": datetime.utcnow()
            })
            
            return {
                "message": "Auto-save enabled successfully",
                "settings": auto_save_settings
            }
            
        except (ValidationError, NotFoundError) as e:
            raise e
        except Exception as e:
            logger.error("Failed to enable auto-save", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to enable auto-save: {str(e)}")
    
    async def disable_auto_save(self, goal_id: str, user_id: str) -> Dict[str, Any]:
        """Disable automatic savings for a goal."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            # Disable auto-save
            auto_save_settings = {
                "enabled": False,
                "amount": 0,
                "frequency": None,
                "next_date": None
            }
            
            await self.goal_repo.update(goal_id, {
                "auto_save_settings": auto_save_settings,
                "updated_at": datetime.utcnow()
            })
            
            return {
                "message": "Auto-save disabled successfully"
            }
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to disable auto-save", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to disable auto-save: {str(e)}")
    
    # Health and maintenance
    async def get_service_health(self) -> Dict[str, Any]:
        """Check goal service health."""
        try:
            # Test database connectivity
            test_query = await self.goal_repo.get_multi(limit=1)
            
            return {
                "database_connected": True,
                "repositories_count": 5,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "database_connected": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def recalculate_goal_progress(self, goal_id: str, user_id: str) -> SavingsGoalResponse:
        """Recalculate goal progress and milestones (maintenance operation)."""
        try:
            goal = await self.goal_repo.get_by_id_for_user(goal_id, user_id)
            if not goal:
                raise NotFoundError("Goal not found")
            
            # Recalculate current amount from contributions
            total_contributions = await self.contribution_repo.get_total_contributions_for_goal(goal_id)
            remaining_amount = goal.target_amount - total_contributions
            
            # Determine status
            status = goal.status
            completed_at = goal.completed_at
            
            if total_contributions >= goal.target_amount and status != GoalStatus.COMPLETED:
                status = GoalStatus.COMPLETED
                completed_at = datetime.utcnow()
            
            # Update goal
            await self.goal_repo.update(goal_id, {
                "current_amount": total_contributions,
                "remaining_amount": max(remaining_amount, Decimal("0")),
                "status": status,
                "completed_at": completed_at,
                "updated_at": datetime.utcnow()
            })
            
            # Recalculate milestones
            await self._check_and_complete_milestones(goal_id, total_contributions)
            
            # Return updated goal
            updated_goal = await self.goal_repo.get_by_id(
                goal_id,
                load_relationships=["milestones", "contributions"]
            )
            
            return SavingsGoalResponse.model_validate(updated_goal)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to recalculate goal progress", goal_id=goal_id, error=str(e))
            raise BusinessLogicError(f"Failed to recalculate: {str(e)}")
    
    # Private helper methods
    async def _check_and_complete_milestones(self, goal_id: str, current_amount: Decimal) -> None:
        """Check if any milestones should be auto-completed."""
        try:
            milestones = await self.milestone_repo.get_milestones_for_goal(goal_id)
            
            for milestone in milestones:
                if (milestone.is_automatic and 
                    milestone.status == MilestoneStatus.PENDING and
                    current_amount >= milestone.target_amount):
                    
                    await self.milestone_repo.complete_milestone(milestone.id, current_amount)
                    logger.info("Auto-completed milestone", 
                              milestone_id=milestone.id, 
                              goal_id=goal_id)
        except Exception as e:
            logger.warning("Failed to check milestones", goal_id=goal_id, error=str(e))