"""Account domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AccountType(str, Enum):
    """Account type enumeration."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    MORTGAGE = "mortgage"
    OTHER = "other"


class AccountSubtype(str, Enum):
    """Account subtype enumeration."""
    # Checking subtypes
    CHECKING = "checking"
    # Savings subtypes
    SAVINGS = "savings"
    MONEY_MARKET = "money_market"
    CD = "cd"
    # Credit subtypes
    CREDIT_CARD = "credit_card"
    # Loan subtypes
    STUDENT = "student"
    MORTGAGE = "mortgage"
    AUTO = "auto"
    PERSONAL = "personal"
    # Investment subtypes
    BROKERAGE = "brokerage"
    IRA = "ira"
    RETIREMENT_401K = "401k"
    # Other
    OTHER = "other"


class AccountBase(BaseModel):
    """Base account schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    type: AccountType = Field(..., description="Account type")
    subtype: Optional[AccountSubtype] = Field(None, description="Account subtype")
    institution_name: Optional[str] = Field(None, max_length=100, description="Financial institution name")
    is_active: bool = Field(default=True, description="Whether account is active")


class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    current_balance: Decimal = Field(..., description="Current account balance")
    available_balance: Optional[Decimal] = Field(None, description="Available balance (for credit accounts)")
    credit_limit: Optional[Decimal] = Field(None, description="Credit limit (for credit accounts)")
    currency: str = Field(default="USD", max_length=3, description="Account currency")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Main Checking Account",
                "type": "checking",
                "subtype": "checking",
                "institution_name": "First National Bank",
                "current_balance": "2500.00",
                "available_balance": "2500.00",
                "currency": "USD",
                "is_active": True
            }
        }
    )


class AccountUpdate(BaseModel):
    """Schema for updating account information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated account name")
    institution_name: Optional[str] = Field(None, max_length=100, description="Updated institution name")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    notes: Optional[str] = Field(None, description="Updated account notes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Checking Account",
                "institution_name": "Updated Bank Name",
                "is_active": True
            }
        }
    )


class AccountResponse(AccountBase):
    """Schema for account responses."""
    id: str = Field(..., description="Account unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    account_number: Optional[str] = Field(None, description="Masked account number")
    routing_number: Optional[str] = Field(None, description="Bank routing number")
    current_balance: Decimal = Field(..., description="Current account balance")
    available_balance: Optional[Decimal] = Field(None, description="Available balance")
    credit_limit: Optional[Decimal] = Field(None, description="Credit limit")
    currency: str = Field(default="USD", description="Account currency")
    last_sync_at: Optional[datetime] = Field(None, description="Last synchronization timestamp")
    plaid_account_id: Optional[str] = Field(None, description="Associated Plaid account ID")
    is_manual: bool = Field(default=True, description="Whether account is manually managed")
    notes: Optional[str] = Field(None, description="Account notes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional account metadata")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Account last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Main Checking Account",
                "type": "checking",
                "subtype": "checking",
                "institution_name": "First National Bank",
                "account_number": "****1234",
                "routing_number": "021000021",
                "current_balance": "2500.00",
                "available_balance": "2500.00",
                "currency": "USD",
                "is_active": True,
                "is_manual": False,
                "plaid_account_id": "plaid_account_123",
                "last_sync_at": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class AccountBalanceUpdate(BaseModel):
    """Schema for updating account balance."""
    current_balance: Decimal = Field(..., description="New current balance")
    available_balance: Optional[Decimal] = Field(None, description="New available balance")
    balance_date: Optional[datetime] = Field(None, description="Balance effective date")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_balance": "2750.00",
                "available_balance": "2750.00",
                "balance_date": "2024-01-15T00:00:00Z"
            }
        }
    )


class AccountBalanceHistoryResponse(BaseModel):
    """Schema for account balance history responses."""
    id: str = Field(..., description="Balance history record ID")
    account_id: str = Field(..., description="Associated account ID")
    balance: Decimal = Field(..., description="Balance amount")
    available_balance: Optional[Decimal] = Field(None, description="Available balance")
    credit_used: Optional[Decimal] = Field(None, description="Credit used (for credit accounts)")
    balance_date: datetime = Field(..., description="Balance effective date")
    change_amount: Optional[Decimal] = Field(None, description="Change from previous balance")
    change_percentage: Optional[Decimal] = Field(None, description="Percentage change from previous balance")
    source: str = Field(..., description="Source of balance update")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "balance": "2500.00",
                "available_balance": "2500.00",
                "balance_date": "2024-01-01T00:00:00Z",
                "change_amount": "250.00",
                "change_percentage": "11.11",
                "source": "plaid_sync",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class AccountListResponse(BaseModel):
    """Schema for paginated account list responses."""
    accounts: List[AccountResponse] = Field(..., description="List of accounts")
    total: int = Field(..., description="Total number of accounts")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "accounts": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "Main Checking Account",
                        "type": "checking",
                        "subtype": "checking",
                        "institution_name": "First National Bank",
                        "current_balance": "2500.00",
                        "currency": "USD",
                        "is_active": True,
                        "is_manual": False,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 5,
                "page": 1,
                "per_page": 10,
                "total_pages": 1
            }
        }
    )


class AccountSummaryResponse(BaseModel):
    """Schema for account summary responses."""
    total_accounts: int = Field(..., description="Total number of accounts")
    active_accounts: int = Field(..., description="Number of active accounts")
    total_assets: Decimal = Field(..., description="Total asset value")
    total_liabilities: Decimal = Field(..., description="Total liability value")
    net_worth: Decimal = Field(..., description="Net worth (assets - liabilities)")
    checking_balance: Decimal = Field(..., description="Total checking account balance")
    savings_balance: Decimal = Field(..., description="Total savings account balance")
    credit_available: Decimal = Field(..., description="Total available credit")
    credit_used: Decimal = Field(..., description="Total credit used")
    investment_value: Decimal = Field(..., description="Total investment value")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_accounts": 5,
                "active_accounts": 5,
                "total_assets": "15000.00",
                "total_liabilities": "2500.00",
                "net_worth": "12500.00",
                "checking_balance": "2500.00",
                "savings_balance": "5000.00",
                "credit_available": "5000.00",
                "credit_used": "2500.00",
                "investment_value": "7500.00"
            }
        }
    )


class AccountBalanceTrendResponse(BaseModel):
    """Schema for account balance trend analysis."""
    account_id: str = Field(..., description="Account ID")
    period: str = Field(..., description="Analysis period (e.g., '30d', '90d', '1y')")
    start_balance: Decimal = Field(..., description="Starting balance for period")
    end_balance: Decimal = Field(..., description="Ending balance for period")
    change_amount: Decimal = Field(..., description="Total change amount")
    change_percentage: Decimal = Field(..., description="Total change percentage")
    average_balance: Decimal = Field(..., description="Average balance during period")
    highest_balance: Decimal = Field(..., description="Highest balance during period")
    lowest_balance: Decimal = Field(..., description="Lowest balance during period")
    data_points: List[Dict[str, Any]] = Field(..., description="Historical balance data points")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "period": "30d",
                "start_balance": "2000.00",
                "end_balance": "2500.00",
                "change_amount": "500.00",
                "change_percentage": "25.00",
                "average_balance": "2250.00",
                "highest_balance": "2750.00",
                "lowest_balance": "1800.00",
                "data_points": [
                    {"date": "2024-01-01", "balance": "2000.00"},
                    {"date": "2024-01-15", "balance": "2250.00"},
                    {"date": "2024-01-30", "balance": "2500.00"}
                ]
            }
        }
    )


class AccountConnectionStatus(BaseModel):
    """Schema for account connection status."""
    account_id: str = Field(..., description="Account ID")
    is_connected: bool = Field(..., description="Whether account is connected to external service")
    connection_type: Optional[str] = Field(None, description="Type of connection (e.g., 'plaid')")
    last_sync_at: Optional[datetime] = Field(None, description="Last successful sync timestamp")
    sync_status: str = Field(..., description="Current sync status")
    error_message: Optional[str] = Field(None, description="Last sync error message")
    requires_reauth: bool = Field(default=False, description="Whether reauthorization is required")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_connected": True,
                "connection_type": "plaid",
                "last_sync_at": "2024-01-01T12:00:00Z",
                "sync_status": "success",
                "requires_reauth": False
            }
        }
    )