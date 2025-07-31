"""Goals domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class GoalType(str, Enum):
    """Goal type enumeration."""
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    HOME_PURCHASE = "home_purchase"
    CAR_PURCHASE = "car_purchase"
    EDUCATION = "education"
    RETIREMENT = "retirement"
    DEBT_PAYOFF = "debt_payoff"
    GENERAL_SAVINGS = "general_savings"
    OTHER = "other"


class GoalStatus(str, Enum):
    """Goal status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalPriority(int, Enum):
    """Goal priority enumeration (1=highest)."""
    HIGHEST = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    LOWEST = 5


class SavingsGoalBase(BaseModel):
    """Base savings goal schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Goal name")
    description: Optional[str] = Field(None, description="Goal description")
    target_amount: Decimal = Field(..., gt=0, description="Target amount to save")
    target_date: Optional[date] = Field(None, description="Target completion date")
    goal_type: GoalType = Field(default=GoalType.GENERAL_SAVINGS, description="Type of goal")
    priority: GoalPriority = Field(default=GoalPriority.MEDIUM, description="Goal priority")
    is_active: bool = Field(default=True, description="Whether goal is active")


class SavingsGoalCreate(SavingsGoalBase):
    """Schema for creating a new savings goal."""
    category: Optional[str] = Field(None, max_length=50, description="Goal category")
    color: Optional[str] = Field(None, max_length=7, description="Goal color (hex)")
    icon: Optional[str] = Field(None, max_length=50, description="Goal icon")
    auto_save_enabled: bool = Field(default=False, description="Enable automatic savings")
    auto_save_amount: Optional[Decimal] = Field(None, description="Automatic savings amount")
    auto_save_frequency: Optional[str] = Field(None, description="Automatic savings frequency")
    linked_account_id: Optional[str] = Field(None, description="Linked account for automatic savings")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Emergency Fund",
                "description": "6 months of expenses for financial security",
                "target_amount": "15000.00",
                "target_date": "2024-12-31",
                "goal_type": "emergency_fund",
                "priority": 1,
                "category": "Security",
                "color": "#28a745",
                "icon": "shield",
                "auto_save_enabled": True,
                "auto_save_amount": "500.00",
                "auto_save_frequency": "monthly",
                "linked_account_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_active": True
            }
        }
    )


class SavingsGoalUpdate(BaseModel):
    """Schema for updating savings goal information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated goal name")
    description: Optional[str] = Field(None, description="Updated goal description")
    target_amount: Optional[Decimal] = Field(None, gt=0, description="Updated target amount")
    target_date: Optional[date] = Field(None, description="Updated target date")
    priority: Optional[GoalPriority] = Field(None, description="Updated priority")
    category: Optional[str] = Field(None, max_length=50, description="Updated category")
    color: Optional[str] = Field(None, max_length=7, description="Updated color")
    icon: Optional[str] = Field(None, max_length=50, description="Updated icon")
    auto_save_enabled: Optional[bool] = Field(None, description="Updated auto-save setting")
    auto_save_amount: Optional[Decimal] = Field(None, description="Updated auto-save amount")
    auto_save_frequency: Optional[str] = Field(None, description="Updated auto-save frequency")
    linked_account_id: Optional[str] = Field(None, description="Updated linked account")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Emergency Fund",
                "target_amount": "18000.00",
                "target_date": "2024-10-31",
                "auto_save_amount": "600.00",
                "is_active": True
            }
        }
    )


class SavingsGoalResponse(SavingsGoalBase):
    """Schema for savings goal responses."""
    id: str = Field(..., description="Goal unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    current_amount: Decimal = Field(..., description="Current saved amount")
    progress_percentage: Decimal = Field(..., description="Progress percentage (0-100)")
    category: Optional[str] = Field(None, description="Goal category")
    color: Optional[str] = Field(None, description="Goal color")
    icon: Optional[str] = Field(None, description="Goal icon")
    auto_save_enabled: bool = Field(default=False, description="Auto-save enabled")
    auto_save_amount: Optional[Decimal] = Field(None, description="Auto-save amount")
    auto_save_frequency: Optional[str] = Field(None, description="Auto-save frequency")
    linked_account_id: Optional[str] = Field(None, description="Linked account ID")
    is_completed: bool = Field(default=False, description="Whether goal is completed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    days_remaining: Optional[int] = Field(None, description="Days remaining to target date")
    projected_completion_date: Optional[date] = Field(None, description="Projected completion date")
    monthly_contribution_needed: Optional[Decimal] = Field(None, description="Monthly contribution needed")
    created_at: datetime = Field(..., description="Goal creation timestamp")
    updated_at: datetime = Field(..., description="Goal last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174008",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Emergency Fund",
                "description": "6 months of expenses for financial security",
                "target_amount": "15000.00",
                "current_amount": "7500.00",
                "progress_percentage": "50.00",
                "target_date": "2024-12-31",
                "goal_type": "emergency_fund",
                "priority": 1,
                "category": "Security",
                "color": "#28a745",
                "icon": "shield",
                "auto_save_enabled": True,
                "auto_save_amount": "500.00",
                "auto_save_frequency": "monthly",
                "linked_account_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_completed": False,
                "days_remaining": 180,
                "projected_completion_date": "2024-11-15",
                "monthly_contribution_needed": "1250.00",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class GoalContributionBase(BaseModel):
    """Base goal contribution schema."""
    amount: Decimal = Field(..., gt=0, description="Contribution amount")
    contribution_date: date = Field(default_factory=date.today, description="Contribution date")
    source_type: str = Field(default="manual", description="Contribution source type")
    notes: Optional[str] = Field(None, description="Contribution notes")


class GoalContributionCreate(GoalContributionBase):
    """Schema for creating goal contribution."""
    source_account_id: Optional[str] = Field(None, description="Source account ID")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    reference_id: Optional[str] = Field(None, description="External reference ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": "500.00",
                "contribution_date": "2024-01-15",
                "source_type": "automatic",
                "source_account_id": "123e4567-e89b-12d3-a456-426614174000",
                "notes": "Monthly automatic contribution"
            }
        }
    )


class GoalContributionResponse(GoalContributionBase):
    """Schema for goal contribution responses."""
    id: str = Field(..., description="Contribution unique identifier")
    goal_id: str = Field(..., description="Associated goal ID")
    user_id: str = Field(..., description="Associated user ID")
    source_account_id: Optional[str] = Field(None, description="Source account ID")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    reference_id: Optional[str] = Field(None, description="External reference ID")
    status: str = Field(default="completed", description="Contribution status")
    created_at: datetime = Field(..., description="Contribution creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174009",
                "goal_id": "123e4567-e89b-12d3-a456-426614174008",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "amount": "500.00",
                "contribution_date": "2024-01-15",
                "source_type": "automatic",
                "source_account_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "notes": "Monthly automatic contribution",
                "created_at": "2024-01-15T10:00:00Z"
            }
        }
    )


class GoalMilestoneBase(BaseModel):
    """Base goal milestone schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    target_amount: Decimal = Field(..., gt=0, description="Milestone target amount")
    target_percentage: Decimal = Field(..., ge=0, le=100, description="Milestone target percentage")
    target_date: Optional[date] = Field(None, description="Milestone target date")


class GoalMilestoneCreate(GoalMilestoneBase):
    """Schema for creating goal milestone."""
    reward_message: Optional[str] = Field(None, description="Reward message for achievement")
    notify_on_achievement: bool = Field(default=True, description="Send notification on achievement")
    sort_order: int = Field(default=0, description="Milestone sort order")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "First Quarter",
                "description": "25% of emergency fund goal",
                "target_amount": "3750.00",
                "target_percentage": "25.00",
                "target_date": "2024-03-31",
                "reward_message": "Great job! You're 25% of the way to your emergency fund goal!",
                "notify_on_achievement": True,
                "sort_order": 1
            }
        }
    )


class GoalMilestoneResponse(GoalMilestoneBase):
    """Schema for goal milestone responses."""
    id: str = Field(..., description="Milestone unique identifier")
    goal_id: str = Field(..., description="Associated goal ID")
    is_achieved: bool = Field(default=False, description="Whether milestone is achieved")
    achieved_at: Optional[datetime] = Field(None, description="Achievement timestamp")
    achieved_amount: Optional[Decimal] = Field(None, description="Amount when achieved")
    reward_message: Optional[str] = Field(None, description="Reward message")
    notify_on_achievement: bool = Field(default=True, description="Notification setting")
    sort_order: int = Field(default=0, description="Sort order")
    created_at: datetime = Field(..., description="Milestone creation timestamp")
    updated_at: datetime = Field(..., description="Milestone last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174010",
                "goal_id": "123e4567-e89b-12d3-a456-426614174008",
                "name": "First Quarter",
                "description": "25% of emergency fund goal",
                "target_amount": "3750.00",
                "target_percentage": "25.00",
                "target_date": "2024-03-31",
                "is_achieved": True,
                "achieved_at": "2024-03-25T14:30:00Z",
                "achieved_amount": "3750.00",
                "reward_message": "Great job! You're 25% of the way to your emergency fund goal!",
                "sort_order": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-03-25T14:30:00Z"
            }
        }
    )


class GoalListResponse(BaseModel):
    """Schema for paginated goal list responses."""
    goals: List[SavingsGoalResponse] = Field(..., description="List of goals")
    total: int = Field(..., description="Total number of goals")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goals": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174008",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "Emergency Fund",
                        "target_amount": "15000.00",
                        "current_amount": "7500.00",
                        "progress_percentage": "50.00",
                        "goal_type": "emergency_fund",
                        "priority": 1,
                        "is_completed": False,
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-15T12:00:00Z"
                    }
                ],
                "total": 3,
                "page": 1,
                "per_page": 10,
                "total_pages": 1
            }
        }
    )


class GoalSummaryResponse(BaseModel):
    """Schema for goal summary responses."""
    total_goals: int = Field(..., description="Total number of goals")
    active_goals: int = Field(..., description="Number of active goals")
    completed_goals: int = Field(..., description="Number of completed goals")
    total_target_amount: Decimal = Field(..., description="Total target amount across all goals")
    total_saved_amount: Decimal = Field(..., description="Total saved amount across all goals")
    overall_progress: Decimal = Field(..., description="Overall progress percentage")
    goals_on_track: int = Field(..., description="Number of goals on track")
    goals_behind_schedule: int = Field(..., description="Number of goals behind schedule")
    next_milestone: Optional[Dict[str, Any]] = Field(None, description="Next upcoming milestone")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_goals": 3,
                "active_goals": 2,
                "completed_goals": 1,
                "total_target_amount": "25000.00",
                "total_saved_amount": "12500.00",
                "overall_progress": "50.00",
                "goals_on_track": 2,
                "goals_behind_schedule": 0,
                "next_milestone": {
                    "goal_name": "Emergency Fund",
                    "milestone_name": "Half Way There",
                    "target_amount": "7500.00",
                    "progress": "95.00"
                }
            }
        }
    )


class GoalAnalysisResponse(BaseModel):
    """Schema for goal analysis responses."""
    goal_id: str = Field(..., description="Goal ID")
    performance_score: Decimal = Field(..., description="Goal performance score (0-100)")
    velocity: Decimal = Field(..., description="Savings velocity (amount per month)")
    projected_completion: Optional[date] = Field(None, description="Projected completion date")
    completion_probability: Decimal = Field(..., description="Probability of completion on time")
    insights: List[str] = Field(..., description="Goal insights and recommendations")
    contribution_patterns: Dict[str, Any] = Field(..., description="Contribution pattern analysis")
    recommendations: List[Dict[str, Any]] = Field(..., description="Improvement recommendations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goal_id": "123e4567-e89b-12d3-a456-426614174008",
                "performance_score": "85.5",
                "velocity": "625.00",
                "projected_completion": "2024-11-15",
                "completion_probability": "0.85",
                "insights": [
                    "You're ahead of schedule on this goal",
                    "Your contribution rate has been consistent",
                    "Consider increasing automatic contributions"
                ],
                "contribution_patterns": {
                    "average_monthly": "625.00",
                    "consistency_score": "0.90",
                    "largest_contribution": "1000.00"
                },
                "recommendations": [
                    {
                        "type": "optimization",
                        "suggestion": "Increase monthly contribution to $750 to complete 2 months early",
                        "impact": "early_completion"
                    }
                ]
            }
        }
    )


class GoalInsightResponse(BaseModel):
    """Schema for goal insight responses."""
    id: str = Field(..., description="Insight unique identifier")
    goal_id: str = Field(..., description="Associated goal ID")
    user_id: str = Field(..., description="Associated user ID")
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    message: str = Field(..., description="Insight message")
    priority: str = Field(..., description="Insight priority")
    confidence_score: Optional[Decimal] = Field(None, description="AI confidence score")
    suggested_actions: List[str] = Field(..., description="Suggested actions")
    is_read: bool = Field(default=False, description="Whether insight has been read")
    is_dismissed: bool = Field(default=False, description="Whether insight has been dismissed")
    is_actionable: bool = Field(default=True, description="Whether insight is actionable")
    created_at: datetime = Field(..., description="Insight creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Insight expiration timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174011",
                "goal_id": "123e4567-e89b-12d3-a456-426614174008",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "insight_type": "recommendation",
                "title": "Increase Your Emergency Fund Goal",
                "message": "Based on your current expenses, consider increasing your emergency fund target to $18,000 for better financial security.",
                "priority": "medium",
                "confidence_score": "0.85",
                "suggested_actions": [
                    "Review your monthly expenses",
                    "Adjust goal target amount",
                    "Update automatic contribution"
                ],
                "is_read": False,
                "is_dismissed": False,
                "is_actionable": True,
                "created_at": "2024-01-20T10:00:00Z"
            }
        }
    )