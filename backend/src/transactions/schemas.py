"""Transaction domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    """Transaction type enumeration."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    REFUND = "refund"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    OTHER = "other"


class CategoryType(str, Enum):
    """Category type enumeration for dual categorization."""
    FIXED = "fixed"
    DISCRETIONARY = "discretionary"


class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    PENDING = "pending"
    POSTED = "posted"
    CANCELLED = "cancelled"
    ERROR = "error"


class TransactionBase(BaseModel):
    """Base transaction schema with common fields."""
    amount: Decimal = Field(..., description="Transaction amount (positive for credits, negative for debits)")
    date: date = Field(..., description="Transaction date")
    description: str = Field(..., min_length=1, max_length=500, description="Transaction description")
    merchant_name: Optional[str] = Field(None, max_length=100, description="Merchant name")
    type: TransactionType = Field(..., description="Transaction type")
    status: TransactionStatus = Field(default=TransactionStatus.POSTED, description="Transaction status")


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    account_id: str = Field(..., description="Associated account ID")
    category: Optional[str] = Field(None, max_length=100, description="Transaction category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Transaction subcategory")
    category_type: Optional[CategoryType] = Field(None, description="Category type (fixed/discretionary)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Transaction tags")
    notes: Optional[str] = Field(None, description="Transaction notes")
    reference_id: Optional[str] = Field(None, description="External reference ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": "-45.67",
                "date": "2024-01-15",
                "description": "Grocery Store Purchase",
                "merchant_name": "Super Market",
                "type": "debit",
                "status": "posted",
                "category": "Food & Dining",
                "subcategory": "Groceries",
                "category_type": "discretionary",
                "tags": ["groceries", "essential"],
                "notes": "Weekly grocery shopping"
            }
        }
    )


class TransactionUpdate(BaseModel):
    """Schema for updating transaction information."""
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Updated description")
    merchant_name: Optional[str] = Field(None, max_length=100, description="Updated merchant name")
    category: Optional[str] = Field(None, max_length=100, description="Updated category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Updated subcategory")
    category_type: Optional[CategoryType] = Field(None, description="Updated category type")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    notes: Optional[str] = Field(None, description="Updated notes")
    is_excluded_from_budgets: Optional[bool] = Field(None, description="Exclude from budget calculations")
    is_business_expense: Optional[bool] = Field(None, description="Mark as business expense")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Updated Grocery Store Purchase",
                "category": "Food & Dining",
                "subcategory": "Groceries",
                "category_type": "discretionary",
                "tags": ["groceries", "essential", "organic"],
                "notes": "Weekly grocery shopping - organic items",
                "is_excluded_from_budgets": False,
                "is_business_expense": False
            }
        }
    )


class TransactionResponse(TransactionBase):
    """Schema for transaction responses."""
    id: str = Field(..., description="Transaction unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    account_id: str = Field(..., description="Associated account ID")
    plaid_transaction_id: Optional[str] = Field(None, description="Plaid transaction ID")
    category: Optional[str] = Field(None, description="Transaction category")
    subcategory: Optional[str] = Field(None, description="Transaction subcategory")
    category_type: Optional[CategoryType] = Field(None, description="Category type (fixed/discretionary)")
    tags: List[str] = Field(default_factory=list, description="Transaction tags")
    notes: Optional[str] = Field(None, description="Transaction notes")
    reference_id: Optional[str] = Field(None, description="External reference ID")
    currency: str = Field(default="USD", description="Transaction currency")
    location: Optional[Dict[str, Any]] = Field(None, description="Transaction location data")
    payment_meta: Optional[Dict[str, Any]] = Field(None, description="Payment method metadata")
    is_excluded_from_budgets: bool = Field(default=False, description="Excluded from budget calculations")
    is_business_expense: bool = Field(default=False, description="Marked as business expense")
    is_recurring: bool = Field(default=False, description="Identified as recurring transaction")
    confidence_level: Optional[Decimal] = Field(None, description="AI categorization confidence level")
    created_at: datetime = Field(..., description="Transaction creation timestamp")
    updated_at: datetime = Field(..., description="Transaction last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "plaid_transaction_id": "plaid_txn_123",
                "amount": "-45.67",
                "date": "2024-01-15",
                "description": "Grocery Store Purchase",
                "merchant_name": "Super Market",
                "type": "debit",
                "status": "posted",
                "category": "Food & Dining",
                "subcategory": "Groceries",
                "category_type": "discretionary",
                "tags": ["groceries", "essential"],
                "notes": "Weekly grocery shopping",
                "currency": "USD",
                "is_excluded_from_budgets": False,
                "is_business_expense": False,
                "is_recurring": False,
                "confidence_level": "0.95",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class TransactionBulkUpdate(BaseModel):
    """Schema for bulk updating multiple transactions."""
    transaction_ids: List[str] = Field(..., description="List of transaction IDs to update")
    updates: TransactionUpdate = Field(..., description="Updates to apply to all transactions")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_ids": [
                    "123e4567-e89b-12d3-a456-426614174003",
                    "123e4567-e89b-12d3-a456-426614174004"
                ],
                "updates": {
                    "category": "Food & Dining",
                    "subcategory": "Groceries",
                    "category_type": "discretionary"
                }
            }
        }
    )


class TransactionCategorizationRequest(BaseModel):
    """Schema for transaction categorization requests."""
    transaction_ids: List[str] = Field(..., description="List of transaction IDs to categorize")
    force_recategorize: bool = Field(default=False, description="Force recategorization of already categorized transactions")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_ids": [
                    "123e4567-e89b-12d3-a456-426614174003",
                    "123e4567-e89b-12d3-a456-426614174004"
                ],
                "force_recategorize": False
            }
        }
    )


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list responses."""
    transactions: List[TransactionResponse] = Field(..., description="List of transactions")
    total: int = Field(..., description="Total number of transactions")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transactions": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174003",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "account_id": "123e4567-e89b-12d3-a456-426614174000",
                        "amount": "-45.67",
                        "date": "2024-01-15",
                        "description": "Grocery Store Purchase",
                        "merchant_name": "Super Market",
                        "type": "debit",
                        "status": "posted",
                        "category": "Food & Dining",
                        "subcategory": "Groceries",
                        "category_type": "discretionary",
                        "currency": "USD",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 150,
                "page": 1,
                "per_page": 25,
                "total_pages": 6
            }
        }
    )


class TransactionSummaryResponse(BaseModel):
    """Schema for transaction summary responses."""
    total_transactions: int = Field(..., description="Total number of transactions")
    total_income: Decimal = Field(..., description="Total income amount")
    total_expenses: Decimal = Field(..., description="Total expense amount")
    net_flow: Decimal = Field(..., description="Net cash flow (income - expenses)")
    fixed_expenses: Decimal = Field(..., description="Total fixed expenses")
    discretionary_expenses: Decimal = Field(..., description="Total discretionary expenses")
    average_transaction: Decimal = Field(..., description="Average transaction amount")
    largest_expense: Decimal = Field(..., description="Largest single expense")
    largest_income: Decimal = Field(..., description="Largest single income")
    transactions_by_category: Dict[str, Decimal] = Field(..., description="Spending by category")
    transactions_by_type: Dict[str, int] = Field(..., description="Transaction counts by type")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_transactions": 150,
                "total_income": "5000.00",
                "total_expenses": "-3500.00",
                "net_flow": "1500.00",
                "fixed_expenses": "-2000.00",
                "discretionary_expenses": "-1500.00",
                "average_transaction": "-23.33",
                "largest_expense": "-850.00",
                "largest_income": "5000.00",
                "transactions_by_category": {
                    "Food & Dining": "-450.00",
                    "Transportation": "-300.00",
                    "Shopping": "-250.00"
                },
                "transactions_by_type": {
                    "debit": 125,
                    "credit": 20,
                    "transfer": 5
                }
            }
        }
    )


class TransactionTrendResponse(BaseModel):
    """Schema for transaction trend analysis."""
    period: str = Field(..., description="Analysis period (e.g., '30d', '90d', '1y')")
    trend_direction: str = Field(..., description="Overall trend direction (up/down/stable)")
    total_change: Decimal = Field(..., description="Total change in spending")
    percentage_change: Decimal = Field(..., description="Percentage change in spending")
    data_points: List[Dict[str, Any]] = Field(..., description="Historical data points")
    category_trends: Dict[str, Dict[str, Any]] = Field(..., description="Trends by category")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": "90d",
                "trend_direction": "up",
                "total_change": "150.00",
                "percentage_change": "4.5",
                "data_points": [
                    {"date": "2024-01-01", "amount": "-3000.00"},
                    {"date": "2024-02-01", "amount": "-3100.00"},
                    {"date": "2024-03-01", "amount": "-3150.00"}
                ],
                "category_trends": {
                    "Food & Dining": {
                        "change": "25.00",
                        "percentage_change": "5.6",
                        "direction": "up"
                    }
                }
            }
        }
    )


class TransactionRecurringPattern(BaseModel):
    """Schema for recurring transaction pattern analysis."""
    pattern_id: str = Field(..., description="Pattern unique identifier")
    merchant_name: str = Field(..., description="Merchant name")
    amount_range: Dict[str, Decimal] = Field(..., description="Amount range (min/max)")
    frequency: str = Field(..., description="Frequency pattern (weekly/monthly/etc.)")
    confidence: Decimal = Field(..., description="Pattern confidence score")
    next_expected_date: Optional[date] = Field(None, description="Next expected transaction date")
    transaction_count: int = Field(..., description="Number of transactions in pattern")
    category: Optional[str] = Field(None, description="Predicted category")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pattern_id": "pattern_123",
                "merchant_name": "Netflix",
                "amount_range": {"min": "-15.99", "max": "-15.99"},
                "frequency": "monthly",
                "confidence": "0.95",
                "next_expected_date": "2024-02-15",
                "transaction_count": 12,
                "category": "Entertainment"
            }
        }
    )


class TransactionSplitRequest(BaseModel):
    """Schema for transaction splitting requests."""
    transaction_id: str = Field(..., description="Transaction ID to split")
    splits: List[Dict[str, Any]] = Field(..., description="Split details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174003",
                "splits": [
                    {
                        "amount": "-25.00",
                        "category": "Food & Dining",
                        "subcategory": "Groceries",
                        "category_type": "discretionary",
                        "description": "Groceries portion"
                    },
                    {
                        "amount": "-20.67",
                        "category": "Personal Care",
                        "subcategory": "Health & Beauty",
                        "category_type": "discretionary",
                        "description": "Personal care items"
                    }
                ]
            }
        }
    )