"""Account API router."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from src.accounts.service import AccountService
from src.accounts.schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountListResponse,
    AccountSummaryResponse, AccountBalanceTrendResponse, AccountBalanceUpdate,
    AccountConnectionStatus, AccountBalanceHistoryResponse, AccountType
)
from src.auth.dependencies import get_current_active_user
from src.exceptions import NotFoundError, ValidationError

router = APIRouter()

# Initialize service
account_service = AccountService()


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new account."""
    try:
        return await account_service.create_account(current_user["user_id"], account_data)
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=AccountListResponse)
async def get_user_accounts(
    skip: int = Query(0, ge=0, description="Number of accounts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of accounts to return"),
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    institution_name: Optional[str] = Query(None, description="Filter by institution name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get user's accounts with filtering."""
    return await account_service.get_user_accounts(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit,
        account_type=account_type.value if account_type else None,
        institution_name=institution_name,
        is_active=is_active
    )


@router.get("/summary", response_model=AccountSummaryResponse)
async def get_account_summary(
    current_user: dict = Depends(get_current_active_user)
):
    """Get account summary for current user."""
    return await account_service.get_account_summary(current_user["user_id"])


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get account by ID."""
    account = await account_service.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_data: AccountUpdate,
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Update account."""
    try:
        account = await account_service.update_account(
            account_id, 
            current_user["user_id"], 
            account_data
        )
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return account
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{account_id}")
async def delete_account(
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete account (soft delete)."""
    success = await account_service.delete_account(account_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"message": "Account deleted successfully"}


@router.put("/{account_id}/balance", response_model=AccountResponse)
async def update_account_balance(
    balance_data: AccountBalanceUpdate,
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Update account balance."""
    try:
        account = await account_service.update_account_balance(
            account_id, 
            current_user["user_id"], 
            balance_data
        )
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return account
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{account_id}/balance/history", response_model=List[AccountBalanceHistoryResponse])
async def get_account_balance_history(
    account_id: str = Path(..., description="Account ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history to retrieve"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get account balance history."""
    try:
        return await account_service.get_account_balance_history(
            account_id, 
            current_user["user_id"], 
            days
        )
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Account not found")


@router.get("/{account_id}/balance/trend", response_model=AccountBalanceTrendResponse)
async def get_account_balance_trend(
    account_id: str = Path(..., description="Account ID"),
    period_days: int = Query(30, ge=7, le=365, description="Analysis period in days"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get account balance trend analysis."""
    trend = await account_service.get_account_balance_trend(
        account_id, 
        current_user["user_id"], 
        period_days
    )
    if not trend:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return trend


@router.get("/{account_id}/connection/status", response_model=AccountConnectionStatus)
async def get_account_connection_status(
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get account connection status."""
    status = await account_service.get_account_connection_status(
        account_id, 
        current_user["user_id"]
    )
    if not status:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return status


@router.post("/{account_id}/sync", response_model=AccountResponse)
async def sync_account_balance(
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Sync account balance from external service."""
    try:
        account = await account_service.sync_account_balance(
            account_id, 
            current_user["user_id"]
        )
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return account
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{account_id}/connect/plaid", response_model=AccountResponse)
async def connect_account_to_plaid(
    plaid_account_id: str,
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Connect account to Plaid."""
    account = await account_service.connect_account_to_plaid(
        account_id, 
        current_user["user_id"], 
        plaid_account_id
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


@router.delete("/{account_id}/connect/plaid", response_model=AccountResponse)
async def disconnect_account_from_plaid(
    account_id: str = Path(..., description="Account ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Disconnect account from Plaid."""
    account = await account_service.disconnect_account_from_plaid(
        account_id, 
        current_user["user_id"]
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


# Additional endpoints for specific account types
@router.get("/type/{account_type}", response_model=List[AccountResponse])
async def get_accounts_by_type(
    account_type: AccountType = Path(..., description="Account type"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all accounts of a specific type."""
    return await account_service.get_accounts_by_type(
        current_user["user_id"], 
        account_type.value
    )


@router.get("/institution/{institution_name}", response_model=List[AccountResponse])
async def get_accounts_by_institution(
    institution_name: str = Path(..., description="Institution name"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all accounts at a specific institution."""
    return await account_service.get_accounts_by_institution(
        current_user["user_id"], 
        institution_name
    )