"""Account service for business logic."""
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime

from src.accounts.repository import AccountRepository, AccountBalanceHistoryRepository
from src.accounts.schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountListResponse,
    AccountSummaryResponse, AccountBalanceTrendResponse, AccountBalanceUpdate,
    AccountConnectionStatus, AccountBalanceHistoryResponse
)
from src.exceptions import NotFoundError, ValidationError
from src.tenant.context import get_tenant_context


class AccountService:
    """Service for account business logic."""
    
    def __init__(self):
        self.account_repo = AccountRepository()
        self.balance_history_repo = AccountBalanceHistoryRepository()
    
    async def create_account(self, user_id: str, account_data: AccountCreate) -> AccountResponse:
        """Create a new account."""
        # Validate account data
        if account_data.type == "credit" and not account_data.credit_limit:
            raise ValidationError("Credit limit is required for credit accounts")
        
        # Create account
        account = await self.account_repo.create_for_user(user_id, account_data)
        
        return AccountResponse.model_validate(account)
    
    async def get_account(self, account_id: str, user_id: str) -> Optional[AccountResponse]:
        """Get account by ID for specific user."""
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        return AccountResponse.model_validate(account)
    
    async def get_user_accounts(
        self, 
        user_id: str,
        skip: int = 0, 
        limit: int = 100,
        account_type: Optional[str] = None,
        institution_name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> AccountListResponse:
        """Get user's accounts with filtering."""
        filters = {}
        
        if account_type:
            filters["type"] = account_type
        
        if institution_name:
            filters["institution_name"] = institution_name
        
        if is_active is not None:
            filters["is_active"] = is_active
        
        accounts = await self.account_repo.get_multi_for_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="-updated_at"
        )
        
        total = await self.account_repo.count_for_user(user_id, filters)
        
        account_responses = [AccountResponse.model_validate(account) for account in accounts]
        
        return AccountListResponse(
            accounts=account_responses,
            total=total,
            page=(skip // limit) + 1,
            per_page=limit,
            total_pages=(total + limit - 1) // limit
        )
    
    async def update_account(
        self, 
        account_id: str, 
        user_id: str, 
        account_data: AccountUpdate
    ) -> Optional[AccountResponse]:
        """Update account."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        updated_account = await self.account_repo.update(account_id, account_data)
        if not updated_account:
            return None
        
        return AccountResponse.model_validate(updated_account)
    
    async def delete_account(self, account_id: str, user_id: str) -> bool:
        """Delete account (soft delete)."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return False
        
        # Soft delete by setting is_active to False
        update_data = AccountUpdate(is_active=False)
        updated_account = await self.account_repo.update(account_id, update_data)
        
        return updated_account is not None
    
    async def update_account_balance(
        self, 
        account_id: str, 
        user_id: str, 
        balance_data: AccountBalanceUpdate
    ) -> Optional[AccountResponse]:
        """Update account balance."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        updated_account = await self.account_repo.update_balance(
            account_id=account_id,
            new_balance=balance_data.current_balance,
            available_balance=balance_data.available_balance,
            balance_date=balance_data.balance_date
        )
        
        if not updated_account:
            return None
        
        return AccountResponse.model_validate(updated_account)
    
    async def get_account_summary(self, user_id: str) -> AccountSummaryResponse:
        """Get account summary for user."""
        summary = await self.account_repo.get_user_account_summary(user_id)
        
        return AccountSummaryResponse(**summary)
    
    async def get_account_balance_history(
        self, 
        account_id: str, 
        user_id: str,
        days: int = 30
    ) -> List[AccountBalanceHistoryResponse]:
        """Get account balance history."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            raise NotFoundError("Account not found")
        
        history = await self.balance_history_repo.get_account_history(account_id, days)
        
        return [AccountBalanceHistoryResponse.model_validate(h) for h in history]
    
    async def get_account_balance_trend(
        self, 
        account_id: str, 
        user_id: str,
        period_days: int = 30
    ) -> Optional[AccountBalanceTrendResponse]:
        """Get account balance trend analysis."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        trend = await self.balance_history_repo.get_balance_trend(account_id, period_days)
        
        return AccountBalanceTrendResponse(**trend)
    
    async def get_accounts_by_institution(
        self, 
        user_id: str, 
        institution_name: str
    ) -> List[AccountResponse]:
        """Get all accounts at a specific institution."""
        accounts = await self.account_repo.get_accounts_by_institution(user_id, institution_name)
        
        return [AccountResponse.model_validate(account) for account in accounts]
    
    async def get_accounts_by_type(
        self, 
        user_id: str, 
        account_type: str
    ) -> List[AccountResponse]:
        """Get all accounts of a specific type."""
        accounts = await self.account_repo.get_accounts_by_type(user_id, account_type)
        
        return [AccountResponse.model_validate(account) for account in accounts]
    
    async def get_account_connection_status(
        self, 
        account_id: str, 
        user_id: str
    ) -> Optional[AccountConnectionStatus]:
        """Get account connection status."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        # Determine connection status based on account data
        is_connected = account.plaid_account_id is not None
        connection_type = "plaid" if is_connected else None
        
        # Check sync status
        sync_status = "success"  # Default
        error_message = None
        requires_reauth = False
        
        # TODO: Implement proper sync status checking
        # This would involve checking Plaid item status, error logs, etc.
        
        return AccountConnectionStatus(
            account_id=account_id,
            is_connected=is_connected,
            connection_type=connection_type,
            last_sync_at=account.last_sync_at,
            sync_status=sync_status,
            error_message=error_message,
            requires_reauth=requires_reauth
        )
    
    async def sync_account_balance(self, account_id: str, user_id: str) -> Optional[AccountResponse]:
        """Sync account balance from external service (Plaid)."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        if not account.plaid_account_id:
            raise ValidationError("Account is not connected to Plaid")
        
        # TODO: Implement Plaid balance sync
        # This would involve calling Plaid API to get latest balance
        # and updating the account with new balance data
        
        # For now, just return the account as-is
        return AccountResponse.model_validate(account)
    
    async def connect_account_to_plaid(
        self, 
        account_id: str, 
        user_id: str, 
        plaid_account_id: str
    ) -> Optional[AccountResponse]:
        """Connect account to Plaid."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        # Update account with Plaid connection
        update_data = AccountUpdate(
            plaid_account_id=plaid_account_id,
            is_manual=False,
            last_sync_at=datetime.utcnow()
        )
        
        updated_account = await self.account_repo.update(account_id, update_data)
        if not updated_account:
            return None
        
        return AccountResponse.model_validate(updated_account)
    
    async def disconnect_account_from_plaid(
        self, 
        account_id: str, 
        user_id: str
    ) -> Optional[AccountResponse]:
        """Disconnect account from Plaid."""
        # Verify account belongs to user
        account = await self.account_repo.get_by_id_for_user(account_id, user_id)
        if not account:
            return None
        
        # Remove Plaid connection
        update_data = AccountUpdate(
            plaid_account_id=None,
            is_manual=True,
            last_sync_at=None
        )
        
        updated_account = await self.account_repo.update(account_id, update_data)
        if not updated_account:
            return None
        
        return AccountResponse.model_validate(updated_account)