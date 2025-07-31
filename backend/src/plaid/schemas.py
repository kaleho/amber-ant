"""Plaid domain Pydantic schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class PlaidEnvironment(str, Enum):
    """Plaid environment enumeration."""
    SANDBOX = "sandbox"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class PlaidProduct(str, Enum):
    """Plaid product enumeration."""
    TRANSACTIONS = "transactions"
    AUTH = "auth"
    IDENTITY = "identity"
    ASSETS = "assets"
    INVESTMENTS = "investments"
    LIABILITIES = "liabilities"
    PAYMENT_INITIATION = "payment_initiation"


class PlaidAccountType(str, Enum):
    """Plaid account type enumeration."""
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER = "other"


class PlaidAccountSubtype(str, Enum):
    """Plaid account subtype enumeration."""
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money_market"
    CD = "cd"
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    STUDENT = "student"
    MORTGAGE = "mortgage"
    AUTO = "auto"
    BUSINESS = "business"
    COMMERCIAL = "commercial"
    CONSTRUCTION = "construction"
    CONSUMER = "consumer"
    HOME_EQUITY = "home_equity"
    LINE_OF_CREDIT = "line_of_credit"
    LOAN = "loan"
    OTHER = "other"


class PlaidItemStatus(str, Enum):
    """Plaid item status enumeration."""
    GOOD = "good"
    BAD = "bad"
    REQUIRES_UPDATE = "requires_update"


class PlaidLinkTokenRequest(BaseModel):
    """Schema for creating Plaid Link token."""
    products: List[PlaidProduct] = Field(..., description="Plaid products to enable")
    country_codes: List[str] = Field(default=["US"], description="Country codes")
    client_name: str = Field(default="Faithful Finances", description="Client name")
    language: str = Field(default="en", description="Language code")
    account_filters: Optional[Dict[str, Any]] = Field(None, description="Account filters")
    webhook: Optional[str] = Field(None, description="Webhook URL")
    update_mode: Optional[str] = Field(None, description="Update mode for existing item")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "products": ["transactions", "auth"],
                "country_codes": ["US"],
                "client_name": "Faithful Finances",
                "language": "en",
                "account_filters": {
                    "depository": {
                        "account_subtypes": ["checking", "savings"]
                    }
                },
                "webhook": "https://api.faithfulfinances.com/webhooks/plaid"
            }
        }
    )


class PlaidLinkTokenResponse(BaseModel):
    """Schema for Plaid Link token response."""
    link_token: str = Field(..., description="Plaid Link token")
    request_id: str = Field(..., description="Plaid request ID")
    expiration: datetime = Field(..., description="Token expiration time")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "link_token": "link-sandbox-12345678-abcd-1234-abcd-123456789012",
                "request_id": "12345678-abcd-1234-abcd-123456789012",
                "expiration": "2024-01-01T04:00:00Z"
            }
        }
    )


class PlaidPublicTokenExchangeRequest(BaseModel):
    """Schema for exchanging public token for access token."""
    public_token: str = Field(..., description="Public token from Link")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata from Link")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "public_token": "public-sandbox-12345678-abcd-1234-abcd-123456789012",
                "metadata": {
                    "institution": {
                        "name": "Chase",
                        "institution_id": "ins_3"
                    },
                    "accounts": [
                        {
                            "id": "account_123",
                            "name": "Plaid Checking",
                            "mask": "0000",
                            "type": "depository",
                            "subtype": "checking"
                        }
                    ]
                }
            }
        }
    )


class PlaidItemResponse(BaseModel):
    """Schema for Plaid item responses."""
    id: str = Field(..., description="Item unique identifier")
    user_id: str = Field(..., description="Associated user ID")
    plaid_item_id: str = Field(..., description="Plaid item ID")
    plaid_access_token: str = Field(..., description="Encrypted Plaid access token")
    institution_id: str = Field(..., description="Institution ID")
    institution_name: str = Field(..., description="Institution name")
    institution_color: Optional[str] = Field(None, description="Institution brand color")
    institution_logo: Optional[str] = Field(None, description="Institution logo URL")
    institution_website: Optional[str] = Field(None, description="Institution website")
    status: PlaidItemStatus = Field(..., description="Item status")
    error_code: Optional[str] = Field(None, description="Current error code")
    error_message: Optional[str] = Field(None, description="Current error message")
    products: List[str] = Field(..., description="Enabled Plaid products")
    available_products: List[str] = Field(..., description="Available Plaid products")
    billed_products: List[str] = Field(..., description="Billed Plaid products")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    consent_expiration_time: Optional[datetime] = Field(None, description="Consent expiration")
    update_type: Optional[str] = Field(None, description="Update type")
    last_successful_sync: Optional[datetime] = Field(None, description="Last successful sync")
    last_sync_attempt: Optional[datetime] = Field(None, description="Last sync attempt")
    consecutive_failed_syncs: int = Field(..., description="Consecutive failed sync count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Item creation timestamp")
    updated_at: datetime = Field(..., description="Item last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174026",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "plaid_item_id": "plaid_item_123abc456def",
                "plaid_access_token": "encrypted_access_token",
                "institution_id": "ins_3",
                "institution_name": "Chase",
                "institution_color": "#0066b2",
                "institution_logo": "https://logos.plaid.com/chase.png",
                "institution_website": "https://www.chase.com",
                "status": "good",
                "products": ["transactions", "auth"],
                "available_products": ["transactions", "auth", "identity"],
                "billed_products": ["transactions"],
                "webhook_url": "https://api.faithfulfinances.com/webhooks/plaid",
                "last_successful_sync": "2024-01-15T12:00:00Z",
                "consecutive_failed_syncs": 0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class PlaidAccountResponse(BaseModel):
    """Schema for Plaid account responses."""
    id: str = Field(..., description="Account unique identifier")
    item_id: str = Field(..., description="Associated item ID")
    account_id: str = Field(..., description="Associated local account ID")
    plaid_account_id: str = Field(..., description="Plaid account ID")
    name: str = Field(..., description="Account name")
    official_name: Optional[str] = Field(None, description="Official account name")
    type: PlaidAccountType = Field(..., description="Account type")
    subtype: PlaidAccountSubtype = Field(..., description="Account subtype")
    verification_status: Optional[str] = Field(None, description="Verification status")
    balance_data: Dict[str, Any] = Field(..., description="Balance information")
    plaid_metadata: Dict[str, Any] = Field(default_factory=dict, description="Plaid metadata")
    sync_transactions: bool = Field(..., description="Whether to sync transactions")
    sync_balance: bool = Field(..., description="Whether to sync balance")
    is_active: bool = Field(..., description="Whether account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Account last update timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174027",
                "item_id": "123e4567-e89b-12d3-a456-426614174026",
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "plaid_account_id": "plaid_account_123abc456def",
                "name": "Plaid Checking",
                "official_name": "Plaid Gold Standard 0% Interest Checking",
                "type": "depository",
                "subtype": "checking",
                "verification_status": "verified",
                "balance_data": {
                    "available": "100.00",
                    "current": "110.00",
                    "limit": None,
                    "iso_currency_code": "USD"
                },
                "sync_transactions": True,
                "sync_balance": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class PlaidTransactionSyncRequest(BaseModel):
    """Schema for transaction sync requests."""
    item_id: str = Field(..., description="Item ID to sync")
    cursor: Optional[str] = Field(None, description="Sync cursor for pagination")
    count: Optional[int] = Field(None, description="Number of transactions to fetch")
    force_full_sync: bool = Field(default=False, description="Force full sync")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": "123e4567-e89b-12d3-a456-426614174026",
                "cursor": "cursor_abc123def456",
                "count": 500,
                "force_full_sync": False
            }
        }
    )


class PlaidTransactionSyncResponse(BaseModel):
    """Schema for transaction sync responses."""
    added: List[Dict[str, Any]] = Field(..., description="Added transactions")
    modified: List[Dict[str, Any]] = Field(..., description="Modified transactions")
    removed: List[Dict[str, Any]] = Field(..., description="Removed transactions")
    next_cursor: Optional[str] = Field(None, description="Next sync cursor")
    has_more: bool = Field(..., description="Whether more transactions are available")
    sync_log_id: str = Field(..., description="Sync log ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "added": [
                    {
                        "transaction_id": "txn_123abc456def",
                        "account_id": "account_123",
                        "amount": "12.34",
                        "date": "2024-01-15",
                        "merchant_name": "Coffee Shop",
                        "category": ["Food and Drink", "Restaurants", "Coffee"]
                    }
                ],
                "modified": [],
                "removed": [],
                "next_cursor": "cursor_next_abc123def456",
                "has_more": False,
                "sync_log_id": "123e4567-e89b-12d3-a456-426614174028"
            }
        }
    )


class PlaidWebhookRequest(BaseModel):
    """Schema for Plaid webhook requests."""
    webhook_type: str = Field(..., description="Webhook type")
    webhook_code: str = Field(..., description="Webhook code")
    item_id: Optional[str] = Field(None, description="Plaid item ID")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information")
    new_transactions: Optional[int] = Field(None, description="Number of new transactions")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "webhook_type": "TRANSACTIONS",
                "webhook_code": "DEFAULT_UPDATE",
                "item_id": "plaid_item_123abc456def",
                "new_transactions": 5
            }
        }
    )


class PlaidWebhookResponse(BaseModel):
    """Schema for Plaid webhook responses."""
    id: str = Field(..., description="Webhook unique identifier")
    item_id: Optional[str] = Field(None, description="Associated item ID")
    webhook_type: str = Field(..., description="Webhook type")
    webhook_code: str = Field(..., description="Webhook code")
    plaid_item_id: Optional[str] = Field(None, description="Plaid item ID")
    payload: Dict[str, Any] = Field(..., description="Webhook payload")
    headers: Dict[str, str] = Field(..., description="Webhook headers")
    processed: bool = Field(..., description="Whether webhook has been processed")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    processing_error: Optional[str] = Field(None, description="Processing error message")
    retry_count: int = Field(..., description="Number of retry attempts")
    is_verified: bool = Field(..., description="Whether webhook signature is verified")
    verification_error: Optional[str] = Field(None, description="Verification error message")
    received_at: datetime = Field(..., description="Webhook received timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174029",
                "item_id": "123e4567-e89b-12d3-a456-426614174026",
                "webhook_type": "TRANSACTIONS",
                "webhook_code": "DEFAULT_UPDATE",
                "plaid_item_id": "plaid_item_123abc456def",
                "payload": {
                    "webhook_type": "TRANSACTIONS",
                    "webhook_code": "DEFAULT_UPDATE",
                    "item_id": "plaid_item_123abc456def",
                    "new_transactions": 5
                },
                "headers": {
                    "content-type": "application/json",
                    "plaid-verification": "signature"
                },
                "processed": True,
                "processed_at": "2024-01-15T12:01:00Z",
                "retry_count": 0,
                "is_verified": True,
                "received_at": "2024-01-15T12:00:00Z"
            }
        }
    )


class PlaidSyncLogResponse(BaseModel):
    """Schema for Plaid sync log responses."""
    id: str = Field(..., description="Sync log unique identifier")
    item_id: str = Field(..., description="Associated item ID")
    sync_type: str = Field(..., description="Type of sync")
    sync_status: str = Field(..., description="Sync status")
    records_processed: int = Field(..., description="Number of records processed")
    records_added: int = Field(..., description="Number of records added")
    records_updated: int = Field(..., description="Number of records updated")
    records_removed: int = Field(..., description="Number of records removed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_type: Optional[str] = Field(None, description="Error type if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: datetime = Field(..., description="Sync start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Sync completion timestamp")
    duration_ms: Optional[int] = Field(None, description="Sync duration in milliseconds")
    cursor: Optional[str] = Field(None, description="Sync cursor")
    has_more: bool = Field(..., description="Whether more data is available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    plaid_request_id: Optional[str] = Field(None, description="Plaid request ID")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174030",
                "item_id": "123e4567-e89b-12d3-a456-426614174026",
                "sync_type": "transactions",
                "sync_status": "success",
                "records_processed": 50,
                "records_added": 5,
                "records_updated": 2,
                "records_removed": 0,
                "started_at": "2024-01-15T12:00:00Z",
                "completed_at": "2024-01-15T12:00:30Z",
                "duration_ms": 30000,
                "cursor": "cursor_abc123def456",
                "has_more": False,
                "plaid_request_id": "plaid_req_123abc456def"
            }
        }
    )


class PlaidErrorResponse(BaseModel):
    """Schema for Plaid error responses."""
    id: str = Field(..., description="Error unique identifier")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    item_id: Optional[str] = Field(None, description="Associated item ID")
    error_type: str = Field(..., description="Error type")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    endpoint: str = Field(..., description="API endpoint where error occurred")
    request_id: Optional[str] = Field(None, description="Plaid request ID")
    suggested_action: Optional[str] = Field(None, description="Suggested action")
    requires_user_action: bool = Field(..., description="Whether user action is required")
    is_resolved: bool = Field(..., description="Whether error has been resolved")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    occurrence_count: int = Field(..., description="Number of occurrences")
    first_occurred_at: datetime = Field(..., description="First occurrence timestamp")
    last_occurred_at: datetime = Field(..., description="Last occurrence timestamp")
    error_data: Dict[str, Any] = Field(default_factory=dict, description="Additional error data")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174031",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "item_id": "123e4567-e89b-12d3-a456-426614174026",
                "error_type": "ITEM_ERROR",
                "error_code": "ITEM_LOGIN_REQUIRED",
                "error_message": "Item requires user login to continue accessing financial data",
                "endpoint": "/transactions/get",
                "request_id": "plaid_req_123abc456def",
                "suggested_action": "RECONNECT_ACCOUNT",
                "requires_user_action": True,
                "is_resolved": False,
                "occurrence_count": 3,
                "first_occurred_at": "2024-01-10T10:00:00Z",
                "last_occurred_at": "2024-01-15T12:00:00Z",
                "error_data": {
                    "display_message": "Please reconnect your account"
                }
            }
        }
    )


class PlaidInstitutionSearchRequest(BaseModel):
    """Schema for institution search requests."""
    query: str = Field(..., min_length=1, description="Search query")
    products: List[PlaidProduct] = Field(..., description="Required products")
    country_codes: List[str] = Field(default=["US"], description="Country codes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Chase",
                "products": ["transactions", "auth"],
                "country_codes": ["US"]
            }
        }
    )


class PlaidInstitutionResponse(BaseModel):
    """Schema for institution responses."""
    institution_id: str = Field(..., description="Institution ID")
    name: str = Field(..., description="Institution name")
    products: List[str] = Field(..., description="Supported products")
    country_codes: List[str] = Field(..., description="Supported country codes")
    url: Optional[str] = Field(None, description="Institution website")
    primary_color: Optional[str] = Field(None, description="Primary brand color")
    logo: Optional[str] = Field(None, description="Institution logo URL")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institution_id": "ins_3",
                "name": "Chase",
                "products": ["transactions", "auth", "identity"],
                "country_codes": ["US"],
                "url": "https://www.chase.com",
                "primary_color": "#0066b2",
                "logo": "https://logos.plaid.com/chase.png"
            }
        }
    )


class PlaidItemHealthResponse(BaseModel):
    """Schema for item health responses."""
    item_id: str = Field(..., description="Item ID")
    status: PlaidItemStatus = Field(..., description="Item status")
    last_sync_success: Optional[datetime] = Field(None, description="Last successful sync")
    consecutive_failures: int = Field(..., description="Consecutive failure count")
    current_errors: List[PlaidErrorResponse] = Field(..., description="Current active errors")
    sync_frequency: str = Field(..., description="Sync frequency")
    next_sync_scheduled: Optional[datetime] = Field(None, description="Next scheduled sync")
    accounts_count: int = Field(..., description="Number of accounts")
    transactions_count: int = Field(..., description="Total transactions synced")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": "123e4567-e89b-12d3-a456-426614174026",
                "status": "good",
                "last_sync_success": "2024-01-15T12:00:00Z",
                "consecutive_failures": 0,
                "current_errors": [],
                "sync_frequency": "daily",
                "next_sync_scheduled": "2024-01-16T12:00:00Z",
                "accounts_count": 3,
                "transactions_count": 150
            }
        }
    )