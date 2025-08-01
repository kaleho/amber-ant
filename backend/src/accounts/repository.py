"""Account repository for database operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, desc, update, delete

from src.shared.repository import UserScopedRepository
from src.accounts.models import Account, AccountBalanceHistory
from src.accounts.schemas import AccountCreate, AccountUpdate
from src.exceptions import DatabaseError


class AccountRepository(UserScopedRepository[Account, AccountCreate, AccountUpdate]):
    """Repository for Account operations."""
    
    def __init__(self):
        super().__init__(Account)
    
    async def get_by_plaid_account_id(self, plaid_account_id: str) -> Optional[Account]:
        """Get account by Plaid account ID."""
        return await self.get_by_field("plaid_account_id", plaid_account_id)
    
    async def get_accounts_by_institution(
        self, 
        user_id: str, 
        institution_name: str
    ) -> List[Account]:
        """Get all accounts for a user at a specific institution."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"institution_name": institution_name, "is_active": True},
            order_by="name"
        )
    
    async def get_accounts_by_type(
        self, 
        user_id: str, 
        account_type: str
    ) -> List[Account]:
        """Get all accounts of a specific type for a user."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={"type": account_type, "is_active": True},
            order_by="name"
        )
    
    async def get_user_account_summary(self, user_id: str) -> Dict[str, Any]:
        """Get account summary for a user."""
        async with await self.get_session() as session:
            try:
                # Get all active accounts for user
                accounts = await self.get_multi_for_user(
                    user_id=user_id,
                    filters={"is_active": True}
                )
                
                total_accounts = len(accounts)
                active_accounts = len([a for a in accounts if a.is_active])
                
                # Calculate balances by type
                total_assets = Decimal('0')
                total_liabilities = Decimal('0')
                checking_balance = Decimal('0')
                savings_balance = Decimal('0')
                credit_available = Decimal('0')
                credit_used = Decimal('0')
                investment_value = Decimal('0')
                
                for account in accounts:
                    if account.type in ['checking', 'savings', 'investment']:
                        total_assets += account.current_balance or Decimal('0')
                        
                        if account.type == 'checking':
                            checking_balance += account.current_balance or Decimal('0')
                        elif account.type == 'savings':
                            savings_balance += account.current_balance or Decimal('0')
                        elif account.type == 'investment':
                            investment_value += account.current_balance or Decimal('0')
                    
                    elif account.type == 'credit':
                        # For credit accounts, current_balance is typically negative (amount owed)
                        credit_used += abs(account.current_balance or Decimal('0'))
                        credit_available += (account.credit_limit or Decimal('0')) - abs(account.current_balance or Decimal('0'))
                        total_liabilities += abs(account.current_balance or Decimal('0'))
                    
                    elif account.type == 'loan':
                        # For loans, current_balance is typically positive (amount owed)
                        total_liabilities += account.current_balance or Decimal('0')
                
                net_worth = total_assets - total_liabilities
                
                return {
                    "total_accounts": total_accounts,
                    "active_accounts": active_accounts,
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "net_worth": net_worth,
                    "checking_balance": checking_balance,
                    "savings_balance": savings_balance,
                    "credit_available": credit_available,
                    "credit_used": credit_used,
                    "investment_value": investment_value
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get account summary: {str(e)}")
    
    async def update_balance(
        self, 
        account_id: str, 
        new_balance: Decimal,
        available_balance: Optional[Decimal] = None,
        balance_date: Optional[datetime] = None
    ) -> Optional[Account]:
        """Update account balance and create history record."""
        async with await self.get_session() as session:
            try:
                account = await self.get_by_id(account_id)
                if not account:
                    return None
                
                old_balance = account.current_balance
                balance_date = balance_date or datetime.utcnow()
                
                # Update account balance
                account.current_balance = new_balance
                if available_balance is not None:
                    account.available_balance = available_balance
                account.updated_at = datetime.utcnow()
                
                # Create balance history record
                change_amount = new_balance - (old_balance or Decimal('0'))
                change_percentage = None
                if old_balance and old_balance != 0:
                    change_percentage = (change_amount / abs(old_balance)) * 100
                
                balance_history = AccountBalanceHistory(
                    account_id=account_id,
                    balance=new_balance,
                    available_balance=available_balance,
                    credit_used=(account.credit_limit - available_balance) if account.credit_limit and available_balance else None,
                    balance_date=balance_date,
                    change_amount=change_amount,
                    change_percentage=change_percentage,
                    source="manual_update"  # Could be "plaid_sync", "manual_update", etc.
                )
                
                session.add(balance_history)
                await session.commit()
                await session.refresh(account)
                
                return account
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to update account balance: {str(e)}")


class AccountBalanceHistoryRepository(UserScopedRepository[AccountBalanceHistory, None, None]):
    """Repository for AccountBalanceHistory operations."""
    
    def __init__(self):
        super().__init__(AccountBalanceHistory, user_field="account.user_id")
    
    async def get_account_history(
        self, 
        account_id: str, 
        days: int = 30,
        limit: int = 100
    ) -> List[AccountBalanceHistory]:
        """Get balance history for an account."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return await self.get_multi(
            filters={
                "account_id": account_id,
                "balance_date": {"gte": cutoff_date}
            },
            order_by="-balance_date",
            limit=limit
        )
    
    async def get_balance_trend(
        self, 
        account_id: str, 
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get balance trend analysis for an account."""
        async with await self.get_session() as session:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=period_days)
                
                # Get balance history for the period
                history = await self.get_account_history(account_id, period_days)
                
                if not history:
                    return {
                        "account_id": account_id,
                        "period": f"{period_days}d",
                        "start_balance": Decimal('0'),
                        "end_balance": Decimal('0'),
                        "change_amount": Decimal('0'),
                        "change_percentage": Decimal('0'),
                        "average_balance": Decimal('0'),
                        "highest_balance": Decimal('0'),
                        "lowest_balance": Decimal('0'),
                        "data_points": []
                    }
                
                # Sort by date (oldest first)
                history.sort(key=lambda x: x.balance_date)
                
                start_balance = history[0].balance
                end_balance = history[-1].balance
                change_amount = end_balance - start_balance
                change_percentage = Decimal('0')
                
                if start_balance != 0:
                    change_percentage = (change_amount / abs(start_balance)) * 100
                
                # Calculate statistics
                balances = [h.balance for h in history]
                average_balance = sum(balances) / len(balances)
                highest_balance = max(balances)
                lowest_balance = min(balances)
                
                # Create data points for charting
                data_points = [
                    {
                        "date": h.balance_date.date().isoformat(),
                        "balance": float(h.balance)
                    }
                    for h in history
                ]
                
                return {
                    "account_id": account_id,
                    "period": f"{period_days}d",
                    "start_balance": start_balance,
                    "end_balance": end_balance,
                    "change_amount": change_amount,
                    "change_percentage": change_percentage,
                    "average_balance": average_balance,
                    "highest_balance": highest_balance,
                    "lowest_balance": lowest_balance,
                    "data_points": data_points
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get balance trend: {str(e)}")