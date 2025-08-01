"""Transaction repository for database operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, desc, asc, text, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.repository import UserScopedRepository
from src.transactions.models import Transaction, TransactionSplit
from src.transactions.schemas import TransactionCreate, TransactionUpdate
from src.exceptions import DatabaseError


class TransactionRepository(UserScopedRepository[Transaction, TransactionCreate, TransactionUpdate]):
    """Repository for Transaction operations."""
    
    def __init__(self):
        super().__init__(Transaction)
    
    async def get_by_plaid_transaction_id(self, plaid_transaction_id: str) -> Optional[Transaction]:
        """Get transaction by Plaid transaction ID."""
        return await self.get_by_field("plaid_transaction_id", plaid_transaction_id)
    
    async def get_transactions_for_account(
        self,
        user_id: str,
        account_id: str,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """Get transactions for a specific account."""
        filters = {"account_id": account_id}
        
        if start_date:
            filters["date"] = {"gte": start_date}
        if end_date:
            if "date" in filters:
                filters["date"]["lte"] = end_date
            else:
                filters["date"] = {"lte": end_date}
        
        return await self.get_multi_for_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="-date"
        )
    
    async def get_transactions_by_category(
        self,
        user_id: str,
        category: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """Get transactions by category."""
        filters = {"category": category}
        
        if start_date:
            filters["date"] = {"gte": start_date}
        if end_date:
            if "date" in filters:
                filters["date"]["lte"] = end_date
            else:
                filters["date"] = {"lte": end_date}
        
        return await self.get_multi_for_user(
            user_id=user_id,
            filters=filters,
            order_by="-date"
        )
    
    async def get_transaction_summary(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get transaction summary for user."""
        async with await self.get_session() as session:
            try:
                query = select(Transaction).where(Transaction.user_id == user_id)
                
                if start_date:
                    query = query.where(Transaction.date >= start_date)
                if end_date:
                    query = query.where(Transaction.date <= end_date)
                
                result = await session.execute(query)
                transactions = list(result.scalars().all())
                
                if not transactions:
                    return {
                        "total_transactions": 0,
                        "total_income": Decimal('0'),
                        "total_expenses": Decimal('0'),
                        "net_flow": Decimal('0'),
                        "fixed_expenses": Decimal('0'),
                        "discretionary_expenses": Decimal('0'),
                        "average_transaction": Decimal('0'),
                        "largest_expense": Decimal('0'),
                        "largest_income": Decimal('0'),
                        "transactions_by_category": {},
                        "transactions_by_type": {}
                    }
                
                total_transactions = len(transactions)
                total_income = Decimal('0')
                total_expenses = Decimal('0')
                fixed_expenses = Decimal('0')
                discretionary_expenses = Decimal('0')
                largest_expense = Decimal('0')
                largest_income = Decimal('0')
                
                transactions_by_category = {}
                transactions_by_type = {}
                
                for transaction in transactions:
                    amount = transaction.amount
                    
                    # Track by type
                    tx_type = transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type)
                    transactions_by_type[tx_type] = transactions_by_type.get(tx_type, 0) + 1
                    
                    # Track by category
                    category = transaction.category or "Uncategorized"
                    if category not in transactions_by_category:
                        transactions_by_category[category] = Decimal('0')
                    transactions_by_category[category] += amount
                    
                    # Income vs expenses
                    if amount > 0:
                        total_income += amount
                        if amount > largest_income:
                            largest_income = amount
                    else:
                        total_expenses += amount
                        if abs(amount) > largest_expense:
                            largest_expense = abs(amount)
                        
                        # Fixed vs discretionary
                        if transaction.category_type == "fixed":
                            fixed_expenses += amount
                        else:
                            discretionary_expenses += amount
                
                net_flow = total_income + total_expenses  # expenses are negative
                average_transaction = sum(t.amount for t in transactions) / len(transactions)
                
                return {
                    "total_transactions": total_transactions,
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "net_flow": net_flow,
                    "fixed_expenses": fixed_expenses,
                    "discretionary_expenses": discretionary_expenses,
                    "average_transaction": average_transaction,
                    "largest_expense": largest_expense,
                    "largest_income": largest_income,
                    "transactions_by_category": transactions_by_category,
                    "transactions_by_type": transactions_by_type
                }
                
            except Exception as e:
                raise DatabaseError(f"Failed to get transaction summary: {str(e)}")
    
    async def get_spending_by_category(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_type: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """Get spending breakdown by category."""
        async with await self.get_session() as session:
            try:
                query = select(Transaction).where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.amount < 0  # Only expenses
                    )
                )
                
                if start_date:
                    query = query.where(Transaction.date >= start_date)
                if end_date:
                    query = query.where(Transaction.date <= end_date)
                if category_type:
                    query = query.where(Transaction.category_type == category_type)
                
                result = await session.execute(query)
                transactions = list(result.scalars().all())
                
                category_totals = {}
                for transaction in transactions:
                    category = transaction.category or "Uncategorized"
                    if category not in category_totals:
                        category_totals[category] = Decimal('0')
                    category_totals[category] += abs(transaction.amount)
                
                return category_totals
                
            except Exception as e:
                raise DatabaseError(f"Failed to get spending by category: {str(e)}")
    
    async def get_monthly_spending_trend(
        self,
        user_id: str,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """Get monthly spending trend."""
        async with await self.get_session() as session:
            try:
                # Calculate date range
                end_date = date.today()
                start_date = end_date - timedelta(days=months * 30)  # Approximate
                
                query = select(Transaction).where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.date >= start_date,
                        Transaction.date <= end_date
                    )
                ).order_by(Transaction.date)
                
                result = await session.execute(query)
                transactions = list(result.scalars().all())
                
                # Group by month
                monthly_data = {}
                for transaction in transactions:
                    month_key = transaction.date.strftime('%Y-%m')
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            'month': month_key,
                            'income': Decimal('0'),
                            'expenses': Decimal('0'),
                            'net': Decimal('0'),
                            'transaction_count': 0
                        }
                    
                    monthly_data[month_key]['transaction_count'] += 1
                    
                    if transaction.amount > 0:
                        monthly_data[month_key]['income'] += transaction.amount
                    else:
                        monthly_data[month_key]['expenses'] += abs(transaction.amount)
                    
                    monthly_data[month_key]['net'] = (
                        monthly_data[month_key]['income'] - 
                        monthly_data[month_key]['expenses']
                    )
                
                return list(monthly_data.values())
                
            except Exception as e:
                raise DatabaseError(f"Failed to get monthly spending trend: {str(e)}")
    
    async def search_transactions(
        self,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Search transactions by description or merchant."""
        async with await self.get_session() as session:
            try:
                search_query = select(Transaction).where(
                    and_(
                        Transaction.user_id == user_id,
                        or_(
                            Transaction.description.ilike(f"%{query}%"),
                            Transaction.merchant_name.ilike(f"%{query}%")
                        )
                    )
                ).order_by(desc(Transaction.date)).offset(skip).limit(limit)
                
                result = await session.execute(search_query)
                return list(result.scalars().all())
                
            except Exception as e:
                raise DatabaseError(f"Failed to search transactions: {str(e)}")
    
    async def get_uncategorized_transactions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Transaction]:
        """Get uncategorized transactions."""
        return await self.get_multi_for_user(
            user_id=user_id,
            filters={
                "category": None,
                "is_excluded_from_budgets": False
            },
            limit=limit,
            order_by="-date"
        )
    
    async def bulk_update_category(
        self,
        transaction_ids: List[str],
        category: str,
        subcategory: Optional[str] = None,
        category_type: Optional[str] = None
    ) -> int:
        """Bulk update transaction categories."""
        async with await self.get_session() as session:
            try:
                update_data = {"category": category}
                if subcategory:
                    update_data["subcategory"] = subcategory
                if category_type:
                    update_data["category_type"] = category_type
                
                query = (
                    update(Transaction)
                    .where(Transaction.id.in_(transaction_ids))
                    .values(**update_data)
                )
                
                result = await session.execute(query)
                await session.commit()
                
                return result.rowcount
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(f"Failed to bulk update categories: {str(e)}")
    
    async def get_duplicate_transactions(
        self,
        user_id: str,
        days: int = 7
    ) -> List[List[Transaction]]:
        """Find potential duplicate transactions."""
        async with await self.get_session() as session:
            try:
                cutoff_date = date.today() - timedelta(days=days)
                
                query = select(Transaction).where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.date >= cutoff_date
                    )
                ).order_by(Transaction.date, Transaction.amount)
                
                result = await session.execute(query)
                transactions = list(result.scalars().all())
                
                # Group potential duplicates
                duplicates = []
                seen = set()
                
                for i, transaction in enumerate(transactions):
                    if transaction.id in seen:
                        continue
                    
                    potential_duplicates = [transaction]
                    seen.add(transaction.id)
                    
                    # Look for similar transactions
                    for j, other_transaction in enumerate(transactions[i+1:], i+1):
                        if other_transaction.id in seen:
                            continue
                        
                        # Check if transactions are similar
                        if (
                            abs(transaction.amount - other_transaction.amount) < Decimal('0.01') and
                            abs((transaction.date - other_transaction.date).days) <= 1 and
                            transaction.merchant_name == other_transaction.merchant_name
                        ):
                            potential_duplicates.append(other_transaction)
                            seen.add(other_transaction.id)
                    
                    if len(potential_duplicates) > 1:
                        duplicates.append(potential_duplicates)
                
                return duplicates
                
            except Exception as e:
                raise DatabaseError(f"Failed to find duplicate transactions: {str(e)}")