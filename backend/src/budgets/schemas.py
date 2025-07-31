"""Budget domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class BudgetPeriod(str, Enum):
    """Budget period enumeration."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetStatus(str, Enum):
    """Budget status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class BudgetBase(BaseModel):
    """Base budget schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Budget name")
    description: Optional[str] = Field(None, description="Budget description")
    period: BudgetPeriod = Field(..., description="Budget period")
    start_date: date = Field(..., description="Budget start date")
    end_date: Optional[date] = Field(None, description="Budget end date")
    is_active: bool = Field(default=True, description="Whether budget is active")


class BudgetCreate(BudgetBase):
    """Schema for creating a new budget."""
    total_amount: Decimal = Field(..., gt=0, description="Total budget amount")
    categories: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, 
        description="Budget category allocations"
    )
    auto_adjust: bool = Field(default=False, description="Enable automatic adjustments")
    rollover_unused: bool = Field(default=True, description="Rollover unused amounts to next period")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Monthly Household Budget",
                "description": "Family monthly budget for essential expenses",
                "period": "monthly",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "total_amount": "3500.00",
                "categories": [
                    {
                        "category": "Food & Dining",
                        "subcategory": "Groceries",
                        "budgeted_amount": "600.00",
                        "category_type": "discretionary"
                    },
                    {
                        "category": "Transportation",
                        "subcategory": "Gas",
                        "budgeted_amount": "200.00",
                        "category_type": "fixed"
                    }
                ],
                "auto_adjust": False,
                "rollover_unused": True,
                "is_active": True
            }
        }
    )


class BudgetUpdate(BaseModel):
    """Schema for updating budget information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated budget name")
    description: Optional[str] = Field(None, description="Updated budget description")
    total_amount: Optional[Decimal] = Field(None, gt=0, description="Updated total budget amount")
    end_date: Optional[date] = Field(None, description="Updated end date")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    auto_adjust: Optional[bool] = Field(None, description="Updated auto-adjustment setting")
    rollover_unused: Optional[bool] = Field(None, description="Updated rollover setting")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Monthly Budget",
                "total_amount": "3750.00",
                "auto_adjust": True,
                "is_active": True
            }
        }
    )


class BudgetResponse(BudgetBase):
    """Schema for budget responses."""
    id: str = Field(..., description="Budget unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    total_amount: Decimal = Field(..., description="Total budget amount")
    spent_amount: Decimal = Field(..., description="Amount spent so far")
    remaining_amount: Decimal = Field(..., description="Amount remaining")
    progress_percentage: Decimal = Field(..., description="Budget progress percentage")
    status: BudgetStatus = Field(..., description="Current budget status")
    auto_adjust: bool = Field(default=False, description="Auto-adjustment enabled")
    rollover_unused: bool = Field(default=True, description="Rollover unused amounts")
    last_updated_at: Optional[datetime] = Field(None, description="Last budget update timestamp")
    created_at: datetime = Field(..., description="Budget creation timestamp")
    updated_at: datetime = Field(..., description="Budget last modification timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174005",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Monthly Household Budget",
                "description": "Family monthly budget for essential expenses",
                "period": "monthly",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "total_amount": "3500.00",
                "spent_amount": "1250.00",
                "remaining_amount": "2250.00",
                "progress_percentage": "35.71",
                "status": "active",
                "auto_adjust": False,
                "rollover_unused": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class BudgetCategoryBase(BaseModel):
    """Base budget category schema."""
    category: str = Field(..., max_length=100, description="Category name")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategory name")
    budgeted_amount: Decimal = Field(..., gt=0, description="Budgeted amount for category")
    category_type: Optional[str] = Field(None, description="Category type (fixed/discretionary)")


class BudgetCategoryCreate(BudgetCategoryBase):
    """Schema for creating budget category."""
    notes: Optional[str] = Field(None, description="Category notes")
    alert_threshold: Optional[Decimal] = Field(None, description="Alert threshold percentage")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "Food & Dining",
                "subcategory": "Groceries",
                "budgeted_amount": "600.00",
                "category_type": "discretionary",
                "notes": "Weekly grocery shopping budget",
                "alert_threshold": "80.0"
            }
        }
    )


class BudgetCategoryUpdate(BaseModel):
    """Schema for updating budget category."""
    budgeted_amount: Optional[Decimal] = Field(None, gt=0, description="Updated budgeted amount")
    notes: Optional[str] = Field(None, description="Updated notes")
    alert_threshold: Optional[Decimal] = Field(None, description="Updated alert threshold")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "budgeted_amount": "650.00",
                "alert_threshold": "85.0",
                "is_active": True
            }
        }
    )


class BudgetCategoryResponse(BudgetCategoryBase):
    """Schema for budget category responses."""
    id: str = Field(..., description="Category unique identifier")
    budget_id: str = Field(..., description="Associated budget ID")
    spent_amount: Decimal = Field(..., description="Amount spent in this category")
    remaining_amount: Decimal = Field(..., description="Amount remaining in this category")
    progress_percentage: Decimal = Field(..., description="Category progress percentage")
    over_budget: bool = Field(..., description="Whether category is over budget")
    variance: Decimal = Field(..., description="Variance from budgeted amount")
    alert_threshold: Optional[Decimal] = Field(None, description="Alert threshold percentage")
    is_active: bool = Field(default=True, description="Whether category is active")
    notes: Optional[str] = Field(None, description="Category notes")
    created_at: datetime = Field(..., description="Category creation timestamp")
    updated_at: datetime = Field(..., description="Category last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174006",
                "budget_id": "123e4567-e89b-12d3-a456-426614174005",
                "category": "Food & Dining",
                "subcategory": "Groceries",
                "budgeted_amount": "600.00",
                "spent_amount": "450.00",
                "remaining_amount": "150.00",
                "progress_percentage": "75.00",
                "over_budget": False,
                "variance": "-150.00",
                "category_type": "discretionary",
                "alert_threshold": "80.0",
                "is_active": True,
                "notes": "Weekly grocery shopping budget",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class BudgetListResponse(BaseModel):
    """Schema for paginated budget list responses."""
    budgets: List[BudgetResponse] = Field(..., description="List of budgets")
    total: int = Field(..., description="Total number of budgets")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "budgets": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174005",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "Monthly Household Budget",
                        "period": "monthly",
                        "total_amount": "3500.00",
                        "spent_amount": "1250.00",
                        "remaining_amount": "2250.00",
                        "progress_percentage": "35.71",
                        "status": "active",
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


class BudgetSummaryResponse(BaseModel):
    """Schema for budget summary responses."""
    total_budgets: int = Field(..., description="Total number of budgets")
    active_budgets: int = Field(..., description="Number of active budgets")
    total_budgeted: Decimal = Field(..., description="Total budgeted amount across all budgets")
    total_spent: Decimal = Field(..., description="Total spent across all budgets")
    total_remaining: Decimal = Field(..., description="Total remaining across all budgets")
    overall_progress: Decimal = Field(..., description="Overall budget progress percentage")
    over_budget_count: int = Field(..., description="Number of categories over budget")
    categories_summary: Dict[str, Dict[str, Any]] = Field(..., description="Summary by category")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_budgets": 2,
                "active_budgets": 2,
                "total_budgeted": "5000.00",
                "total_spent": "1800.00",
                "total_remaining": "3200.00",
                "overall_progress": "36.00",
                "over_budget_count": 1,
                "categories_summary": {
                    "Food & Dining": {
                        "budgeted": "600.00",
                        "spent": "450.00",
                        "remaining": "150.00",
                        "percentage": "75.00"
                    }
                }
            }
        }
    )


class BudgetAnalysisResponse(BaseModel):
    """Schema for budget analysis responses."""
    budget_id: str = Field(..., description="Budget ID")
    period: str = Field(..., description="Analysis period")
    performance_score: Decimal = Field(..., description="Budget performance score (0-100)")
    insights: List[str] = Field(..., description="Budget insights and recommendations")
    trends: Dict[str, Any] = Field(..., description="Spending trends analysis")
    category_performance: Dict[str, Dict[str, Any]] = Field(..., description="Performance by category")
    recommendations: List[Dict[str, Any]] = Field(..., description="Improvement recommendations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "budget_id": "123e4567-e89b-12d3-a456-426614174005",
                "period": "monthly",
                "performance_score": "85.5",
                "insights": [
                    "You're on track to stay within budget this month",
                    "Grocery spending is 15% higher than last month",
                    "Transportation costs are well controlled"
                ],
                "trends": {
                    "overall_trend": "stable",
                    "variance_from_last_period": "-2.5"
                },
                "category_performance": {
                    "Food & Dining": {
                        "score": "75.0",
                        "trend": "increasing",
                        "recommendation": "Consider meal planning to reduce costs"
                    }
                },
                "recommendations": [
                    {
                        "type": "optimization",
                        "category": "Food & Dining",
                        "suggestion": "Set up automatic savings for unused budget amounts",
                        "potential_savings": "50.00"
                    }
                ]
            }
        }
    )


class BudgetForecastResponse(BaseModel):
    """Schema for budget forecast responses."""
    budget_id: str = Field(..., description="Budget ID")
    forecast_period: str = Field(..., description="Forecast period")
    projected_spending: Decimal = Field(..., description="Projected total spending")
    projected_variance: Decimal = Field(..., description="Projected variance from budget")
    confidence_level: Decimal = Field(..., description="Forecast confidence level")
    category_forecasts: Dict[str, Dict[str, Any]] = Field(..., description="Forecasts by category")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "budget_id": "123e4567-e89b-12d3-a456-426614174005",
                "forecast_period": "end_of_month",
                "projected_spending": "3400.00",
                "projected_variance": "-100.00",
                "confidence_level": "0.85",
                "category_forecasts": {
                    "Food & Dining": {
                        "projected": "580.00",
                        "variance": "-20.00",
                        "confidence": "0.90"
                    }
                },
                "risk_factors": [
                    "Upcoming holiday may increase dining expenses",
                    "Gas prices trending upward"
                ]
            }
        }
    )


class BudgetAlertResponse(BaseModel):
    """Schema for budget alert responses."""
    id: str = Field(..., description="Alert unique identifier")
    budget_id: str = Field(..., description="Associated budget ID")
    category_id: Optional[str] = Field(None, description="Associated category ID if category-specific")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message")
    threshold_percentage: Optional[Decimal] = Field(None, description="Threshold that triggered alert")
    current_percentage: Decimal = Field(..., description="Current spending percentage")
    is_read: bool = Field(default=False, description="Whether alert has been read")
    created_at: datetime = Field(..., description="Alert creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174007",
                "budget_id": "123e4567-e89b-12d3-a456-426614174005",
                "category_id": "123e4567-e89b-12d3-a456-426614174006",
                "alert_type": "threshold_exceeded",
                "severity": "warning",
                "message": "Groceries spending has reached 85% of budget",
                "threshold_percentage": "80.0",
                "current_percentage": "85.0",
                "is_read": False,
                "created_at": "2024-01-20T14:30:00Z"
            }
        }
    )