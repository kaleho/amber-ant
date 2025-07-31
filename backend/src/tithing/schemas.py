"""Tithing domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TithingMethod(str, Enum):
    """Tithing payment method enumeration."""
    CASH = "cash"
    CHECK = "check"
    ONLINE = "online"
    AUTO_TRANSFER = "auto_transfer"
    OTHER = "other"


class TithingFrequency(str, Enum):
    """Tithing frequency enumeration."""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TithingPurpose(str, Enum):
    """Tithing purpose enumeration."""
    REGULAR_TITHE = "regular_tithe"
    SPECIAL_OFFERING = "special_offering"
    THANKSGIVING = "thanksgiving"
    MISSIONS = "missions"
    BUILDING_FUND = "building_fund"
    OTHER = "other"


class TithingPaymentBase(BaseModel):
    """Base tithing payment schema with common fields."""
    amount: Decimal = Field(..., gt=0, description="Tithing payment amount")
    date: date = Field(..., description="Payment date")
    method: TithingMethod = Field(..., description="Payment method")
    recipient: str = Field(..., min_length=1, max_length=100, description="Recipient organization")
    purpose: TithingPurpose = Field(default=TithingPurpose.REGULAR_TITHE, description="Payment purpose")
    currency: str = Field(default="USD", max_length=3, description="Payment currency")


class TithingPaymentCreate(TithingPaymentBase):
    """Schema for creating a new tithing payment."""
    recipient_address: Optional[str] = Field(None, description="Recipient address")
    reference_number: Optional[str] = Field(None, max_length=50, description="Payment reference number")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    notes: Optional[str] = Field(None, description="Payment notes")
    is_tax_deductible: bool = Field(default=True, description="Whether payment is tax deductible")
    receipt_issued: bool = Field(default=False, description="Whether receipt was issued")
    receipt_number: Optional[str] = Field(None, max_length=50, description="Receipt number")
    verification_method: Optional[str] = Field(None, max_length=50, description="Verification method")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": "500.00",
                "date": "2024-01-07",
                "method": "online",
                "recipient": "First Baptist Church",
                "recipient_address": "123 Main St, Anytown, ST 12345",
                "purpose": "regular_tithe",
                "reference_number": "TXN-2024-001",
                "notes": "Weekly tithe payment",
                "currency": "USD",
                "is_tax_deductible": True,
                "receipt_issued": True,
                "receipt_number": "RCP-2024-001"
            }
        }
    )


class TithingPaymentUpdate(BaseModel):
    """Schema for updating tithing payment information."""
    recipient: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated recipient")
    recipient_address: Optional[str] = Field(None, description="Updated recipient address")
    reference_number: Optional[str] = Field(None, max_length=50, description="Updated reference number")
    notes: Optional[str] = Field(None, description="Updated notes")
    is_tax_deductible: Optional[bool] = Field(None, description="Updated tax deductible status")
    receipt_issued: Optional[bool] = Field(None, description="Updated receipt status")
    receipt_number: Optional[str] = Field(None, max_length=50, description="Updated receipt number")
    is_verified: Optional[bool] = Field(None, description="Updated verification status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recipient": "Updated Church Name",
                "notes": "Updated payment notes",
                "receipt_issued": True,
                "receipt_number": "RCP-2024-001-UPDATED"
            }
        }
    )


class TithingPaymentResponse(TithingPaymentBase):
    """Schema for tithing payment responses."""
    id: str = Field(..., description="Payment unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    recipient_address: Optional[str] = Field(None, description="Recipient address")
    reference_number: Optional[str] = Field(None, description="Payment reference number")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    notes: Optional[str] = Field(None, description="Payment notes")
    is_verified: bool = Field(default=True, description="Payment verification status")
    verification_method: Optional[str] = Field(None, description="Verification method")
    is_tax_deductible: bool = Field(default=True, description="Tax deductible status")
    receipt_issued: bool = Field(default=False, description="Receipt issued status")
    receipt_number: Optional[str] = Field(None, description="Receipt number")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Payment creation timestamp")
    updated_at: datetime = Field(..., description="Payment last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174012",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "amount": "500.00",
                "date": "2024-01-07",
                "method": "online",
                "recipient": "First Baptist Church",
                "recipient_address": "123 Main St, Anytown, ST 12345",
                "purpose": "regular_tithe",
                "reference_number": "TXN-2024-001",
                "notes": "Weekly tithe payment",
                "currency": "USD",
                "is_verified": True,
                "is_tax_deductible": True,
                "receipt_issued": True,
                "receipt_number": "RCP-2024-001",
                "created_at": "2024-01-07T10:00:00Z",
                "updated_at": "2024-01-07T10:00:00Z"
            }
        }
    )


class TithingScheduleBase(BaseModel):
    """Base tithing schedule schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    amount: Decimal = Field(..., gt=0, description="Scheduled amount")
    percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentage of income")
    frequency: TithingFrequency = Field(..., description="Payment frequency")
    start_date: date = Field(..., description="Schedule start date")
    end_date: Optional[date] = Field(None, description="Schedule end date")
    method: TithingMethod = Field(..., description="Payment method")
    recipient: str = Field(..., min_length=1, max_length=100, description="Recipient organization")


class TithingScheduleCreate(TithingScheduleBase):
    """Schema for creating tithing schedule."""
    source_account_id: Optional[str] = Field(None, description="Source account for payments")
    auto_process: bool = Field(default=False, description="Enable automatic processing")
    is_active: bool = Field(default=True, description="Schedule active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Monthly Tithe",
                "description": "Regular monthly tithe payment",
                "amount": "500.00",
                "percentage": "10.00",
                "frequency": "monthly",
                "start_date": "2024-01-01",
                "method": "auto_transfer",
                "recipient": "First Baptist Church",
                "source_account_id": "123e4567-e89b-12d3-a456-426614174000",
                "auto_process": True,
                "is_active": True
            }
        }
    )


class TithingScheduleResponse(TithingScheduleBase):
    """Schema for tithing schedule responses."""
    id: str = Field(..., description="Schedule unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    source_account_id: Optional[str] = Field(None, description="Source account ID")
    is_active: bool = Field(default=True, description="Schedule active status")
    auto_process: bool = Field(default=False, description="Automatic processing enabled")
    last_executed_at: Optional[datetime] = Field(None, description="Last execution timestamp")
    next_execution_date: Optional[date] = Field(None, description="Next scheduled execution date")
    execution_count: int = Field(default=0, description="Number of executions")
    created_at: datetime = Field(..., description="Schedule creation timestamp")
    updated_at: datetime = Field(..., description="Schedule last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174013",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Monthly Tithe",
                "description": "Regular monthly tithe payment",
                "amount": "500.00",
                "frequency": "monthly",
                "start_date": "2024-01-01",
                "method": "auto_transfer",
                "recipient": "First Baptist Church",
                "is_active": True,
                "auto_process": True,
                "last_executed_at": "2024-01-01T00:00:00Z",
                "next_execution_date": "2024-02-01",
                "execution_count": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class TithingSummaryResponse(BaseModel):
    """Schema for tithing summary responses."""
    id: str = Field(..., description="Summary unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    year: int = Field(..., description="Summary year")
    period_start: date = Field(..., description="Summary period start")
    period_end: date = Field(..., description="Summary period end")
    total_income: Decimal = Field(..., description="Total income for period")
    tithing_eligible_income: Decimal = Field(..., description="Tithing eligible income")
    total_tithe_due: Decimal = Field(..., description="Total tithe amount due")
    total_tithe_paid: Decimal = Field(..., description="Total tithe amount paid")
    balance: Decimal = Field(..., description="Balance (paid - due)")
    current_percentage: Decimal = Field(..., description="Actual tithing percentage")
    target_percentage: Decimal = Field(..., description="Target tithing percentage")
    payment_count: int = Field(..., description="Number of payments made")
    average_payment: Decimal = Field(..., description="Average payment amount")
    largest_payment: Decimal = Field(..., description="Largest single payment")
    income_sources: Dict[str, Decimal] = Field(..., description="Income breakdown by source")
    payment_methods: Dict[str, Decimal] = Field(..., description="Payment breakdown by method")
    recipients: Dict[str, Decimal] = Field(..., description="Payment breakdown by recipient")
    is_final: bool = Field(default=False, description="Whether summary is finalized")
    last_calculated_at: datetime = Field(..., description="Last calculation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174014",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "year": 2024,
                "period_start": "2024-01-01",
                "period_end": "2024-12-31",
                "total_income": "60000.00",
                "tithing_eligible_income": "60000.00",
                "total_tithe_due": "6000.00",
                "total_tithe_paid": "6000.00",
                "balance": "0.00",
                "current_percentage": "10.00",
                "target_percentage": "10.00",
                "payment_count": 52,
                "average_payment": "115.38",
                "largest_payment": "500.00",
                "income_sources": {
                    "salary": "50000.00",
                    "bonus": "10000.00"
                },
                "payment_methods": {
                    "online": "4000.00",
                    "check": "2000.00"
                },
                "recipients": {
                    "First Baptist Church": "6000.00"
                },
                "is_final": False,
                "last_calculated_at": "2024-01-31T23:59:59Z"
            }
        }
    )


class TithingGoalBase(BaseModel):
    """Base tithing goal schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Goal name")
    description: Optional[str] = Field(None, description="Goal description")
    start_date: date = Field(..., description="Goal start date")
    end_date: date = Field(..., description="Goal end date")
    target_percentage: Decimal = Field(default=Decimal("10.0"), ge=0, le=100, description="Target percentage")
    target_amount: Optional[Decimal] = Field(None, gt=0, description="Target amount")


class TithingGoalCreate(TithingGoalBase):
    """Schema for creating tithing goal."""
    reminder_frequency: Optional[str] = Field(None, description="Reminder frequency")
    is_active: bool = Field(default=True, description="Goal active status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "2024 Tithing Goal",
                "description": "Consistent 10% tithing throughout 2024",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "target_percentage": "10.00",
                "target_amount": "6000.00",
                "reminder_frequency": "weekly",
                "is_active": True
            }
        }
    )


class TithingGoalResponse(TithingGoalBase):
    """Schema for tithing goal responses."""
    id: str = Field(..., description="Goal unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    current_percentage: Decimal = Field(..., description="Current percentage achieved")
    current_amount: Decimal = Field(..., description="Current amount given")
    is_active: bool = Field(default=True, description="Goal active status")
    is_completed: bool = Field(default=False, description="Goal completion status")
    completed_at: Optional[datetime] = Field(None, description="Goal completion timestamp")
    reminder_frequency: Optional[str] = Field(None, description="Reminder frequency")
    last_reminder_sent: Optional[datetime] = Field(None, description="Last reminder timestamp")
    created_at: datetime = Field(..., description="Goal creation timestamp")
    updated_at: datetime = Field(..., description="Goal last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174015",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "2024 Tithing Goal",
                "description": "Consistent 10% tithing throughout 2024",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "target_percentage": "10.00",
                "target_amount": "6000.00",
                "current_percentage": "9.5",
                "current_amount": "1140.00",
                "is_active": True,
                "is_completed": False,
                "reminder_frequency": "weekly",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-02-01T00:00:00Z"
            }
        }
    )


class TithingListResponse(BaseModel):
    """Schema for paginated tithing payment list responses."""
    payments: List[TithingPaymentResponse] = Field(..., description="List of tithing payments")
    total: int = Field(..., description="Total number of payments")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "payments": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174012",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "amount": "500.00",
                        "date": "2024-01-07",
                        "method": "online",
                        "recipient": "First Baptist Church",
                        "purpose": "regular_tithe",
                        "currency": "USD",
                        "is_tax_deductible": True,
                        "created_at": "2024-01-07T10:00:00Z",
                        "updated_at": "2024-01-07T10:00:00Z"
                    }
                ],
                "total": 52,
                "page": 1,
                "per_page": 25,
                "total_pages": 3
            }
        }
    )


class TithingAnalysisResponse(BaseModel):
    """Schema for tithing analysis responses."""
    period: str = Field(..., description="Analysis period")
    consistency_score: Decimal = Field(..., description="Tithing consistency score (0-100)")
    faithfulness_rating: str = Field(..., description="Faithfulness rating")
    average_percentage: Decimal = Field(..., description="Average tithing percentage")
    trend_direction: str = Field(..., description="Trend direction (increasing/decreasing/stable)")
    insights: List[str] = Field(..., description="Tithing insights")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    monthly_breakdown: List[Dict[str, Any]] = Field(..., description="Monthly breakdown data")
    recipient_analysis: Dict[str, Dict[str, Any]] = Field(..., description="Analysis by recipient")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": "2024",
                "consistency_score": "95.0",
                "faithfulness_rating": "excellent",
                "average_percentage": "10.2",
                "trend_direction": "stable",
                "insights": [
                    "You've been very consistent with your tithing",
                    "Your giving exceeds the traditional 10% standard",
                    "Consider setting up automatic transfers for even more consistency"
                ],
                "recommendations": [
                    "Continue your excellent tithing habits",
                    "Consider increasing special offerings during holidays"
                ],
                "monthly_breakdown": [
                    {"month": "January", "amount": "500.00", "percentage": "10.0"},
                    {"month": "February", "amount": "510.00", "percentage": "10.2"}
                ],
                "recipient_analysis": {
                    "First Baptist Church": {
                        "total_amount": "6000.00",
                        "percentage_of_total": "100.0",
                        "frequency": "monthly"
                    }
                }
            }
        }
    )