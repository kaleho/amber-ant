"""Transaction service for business logic."""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from src.transactions.repository import TransactionRepository
from src.transactions.schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse, TransactionListResponse,
    TransactionSummaryResponse, TransactionTrendResponse, TransactionBulkUpdate,
    TransactionCategorizationRequest, TransactionSplitRequest
)
from src.exceptions import NotFoundError, ValidationError
from src.tenant.context import get_tenant_context


class TransactionService:
    """Service for transaction business logic."""
    
    def __init__(self):
        self.transaction_repo = TransactionRepository()
    
    async def create_transaction(
        self, 
        user_id: str, 
        transaction_data: TransactionCreate
    ) -> TransactionResponse:
        """Create a new transaction."""
        # Validate transaction data
        if transaction_data.amount == 0:
            raise ValidationError("Transaction amount cannot be zero")
        
        # Auto-categorize if possible
        if not transaction_data.category and transaction_data.merchant_name:
            transaction_data.category = await self._auto_categorize_transaction(
                transaction_data.merchant_name,
                transaction_data.description,
                transaction_data.amount
            )
        
        # Create transaction
        transaction = await self.transaction_repo.create_for_user(user_id, transaction_data)
        
        return TransactionResponse.model_validate(transaction)
    
    async def get_transaction(
        self, 
        transaction_id: str, 
        user_id: str
    ) -> Optional[TransactionResponse]:
        """Get transaction by ID for specific user."""
        transaction = await self.transaction_repo.get_by_id_for_user(transaction_id, user_id)
        if not transaction:
            return None
        
        return TransactionResponse.model_validate(transaction)
    
    async def get_user_transactions(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        account_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> TransactionListResponse:
        """Get user's transactions with filtering."""
        if search:
            transactions = await self.transaction_repo.search_transactions(
                user_id, search, skip, limit
            )
            total = len(transactions)  # Simplified count
        else:
            filters = {}
            
            if account_id:
                filters["account_id"] = account_id
            if category:
                filters["category"] = category
            if transaction_type:
                filters["type"] = transaction_type
            if start_date:
                filters["date"] = {"gte": start_date}
            if end_date:
                if "date" in filters:
                    filters["date"]["lte"] = end_date
                else:
                    filters["date"] = {"lte": end_date}
            
            transactions = await self.transaction_repo.get_multi_for_user(
                user_id=user_id,
                skip=skip,
                limit=limit,
                filters=filters,
                order_by="-date"
            )
            
            total = await self.transaction_repo.count_for_user(user_id, filters)
        
        transaction_responses = [
            TransactionResponse.model_validate(transaction) 
            for transaction in transactions
        ]
        
        return TransactionListResponse(
            transactions=transaction_responses,
            total=total,
            page=(skip // limit) + 1,
            per_page=limit,
            total_pages=(total + limit - 1) // limit
        )
    
    async def update_transaction(
        self,
        transaction_id: str,
        user_id: str,
        transaction_data: TransactionUpdate
    ) -> Optional[TransactionResponse]:
        """Update transaction."""
        # Verify transaction belongs to user
        transaction = await self.transaction_repo.get_by_id_for_user(transaction_id, user_id)
        if not transaction:
            return None
        
        updated_transaction = await self.transaction_repo.update(transaction_id, transaction_data)
        if not updated_transaction:
            return None
        
        return TransactionResponse.model_validate(updated_transaction)
    
    async def delete_transaction(self, transaction_id: str, user_id: str) -> bool:
        """Delete transaction."""
        # Verify transaction belongs to user
        transaction = await self.transaction_repo.get_by_id_for_user(transaction_id, user_id)
        if not transaction:
            return False
        
        return await self.transaction_repo.delete(transaction_id)
    
    async def get_transaction_summary(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TransactionSummaryResponse:
        """Get transaction summary for user."""
        summary = await self.transaction_repo.get_transaction_summary(
            user_id, start_date, end_date
        )
        
        return TransactionSummaryResponse(**summary)
    
    async def get_spending_by_category(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_type: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """Get spending breakdown by category."""
        return await self.transaction_repo.get_spending_by_category(
            user_id, start_date, end_date, category_type
        )
    
    async def get_transaction_trend(
        self,
        user_id: str,
        period_days: int = 90
    ) -> TransactionTrendResponse:
        """Get transaction trend analysis."""
        months = max(1, period_days // 30)
        trend_data = await self.transaction_repo.get_monthly_spending_trend(user_id, months)
        
        if not trend_data:
            return TransactionTrendResponse(
                period=f"{period_days}d",
                trend_direction="stable",
                total_change=Decimal('0'),
                percentage_change=Decimal('0'),
                data_points=[],
                category_trends={}
            )
        
        # Calculate overall trend
        first_month = trend_data[0]
        last_month = trend_data[-1]
        
        total_change = last_month['expenses'] - first_month['expenses']
        percentage_change = Decimal('0')
        if first_month['expenses'] > 0:
            percentage_change = (total_change / first_month['expenses']) * 100
        
        trend_direction = "stable"
        if total_change > 0:
            trend_direction = "up"
        elif total_change < 0:
            trend_direction = "down"
        
        # Convert to data points
        data_points = [
            {
                "date": point["month"],
                "amount": float(point["expenses"])
            }
            for point in trend_data
        ]
        
        # Calculate category trends
        category_trends = {}
        if len(trend_data) >= 2:
            # Get category spending for first and last periods
            first_categories = await self.transaction_repo.get_spending_by_category(
                user_id, 
                date.today() - timedelta(days=period_days),
                date.today() - timedelta(days=period_days - 30)
            )
            last_categories = await self.transaction_repo.get_spending_by_category(
                user_id,
                date.today() - timedelta(days=30),
                date.today()
            )
            
            # Compare category spending
            all_categories = set(first_categories.keys()) | set(last_categories.keys())
            for category in all_categories:
                first_amount = first_categories.get(category, Decimal('0'))
                last_amount = last_categories.get(category, Decimal('0'))
                
                if first_amount > 0:
                    change = ((last_amount - first_amount) / first_amount) * 100
                    category_trends[category] = {
                        "change_percentage": float(change),
                        "direction": "up" if change > 5 else "down" if change < -5 else "stable"
                    }
        
        return TransactionTrendResponse(
            period=f"{period_days}d",
            trend_direction=trend_direction,
            total_change=total_change,
            percentage_change=percentage_change,
            data_points=data_points,
            category_trends=category_trends
        )
    
    async def categorize_transactions(
        self,
        user_id: str,
        request: TransactionCategorizationRequest
    ) -> Dict[str, Any]:
        """Categorize transactions using AI/rules."""
        categorized_count = 0
        
        for transaction_id in request.transaction_ids:
            transaction = await self.transaction_repo.get_by_id_for_user(transaction_id, user_id)
            if not transaction:
                continue
            
            # Skip if already categorized and not forcing
            if transaction.category and not request.force_recategorize:
                continue
            
            # Auto-categorize
            category = await self._auto_categorize_transaction(
                transaction.merchant_name,
                transaction.description,
                transaction.amount
            )
            
            if category:
                update_data = TransactionUpdate(category=category)
                await self.transaction_repo.update(transaction_id, update_data)
                categorized_count += 1
        
        return {
            "message": f"Categorized {categorized_count} transactions",
            "categorized_count": categorized_count,
            "total_requested": len(request.transaction_ids)
        }
    
    async def bulk_update_transactions(
        self,
        user_id: str,
        request: TransactionBulkUpdate
    ) -> Dict[str, Any]:
        """Bulk update multiple transactions."""
        # Verify all transactions belong to user
        valid_transaction_ids = []
        for transaction_id in request.transaction_ids:
            transaction = await self.transaction_repo.get_by_id_for_user(transaction_id, user_id)
            if transaction:
                valid_transaction_ids.append(transaction_id)
        
        if not valid_transaction_ids:
            raise ValidationError("No valid transactions found")
        
        # Perform bulk update
        updated_count = 0
        for transaction_id in valid_transaction_ids:
            updated_transaction = await self.transaction_repo.update(transaction_id, request.updates)
            if updated_transaction:
                updated_count += 1
        
        return {
            "message": f"Updated {updated_count} transactions",
            "updated_count": updated_count,
            "total_requested": len(request.transaction_ids)
        }
    
    async def get_uncategorized_transactions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[TransactionResponse]:
        """Get uncategorized transactions."""
        transactions = await self.transaction_repo.get_uncategorized_transactions(user_id, limit)
        
        return [TransactionResponse.model_validate(t) for t in transactions]
    
    async def get_transactions_for_account(
        self,
        user_id: str,
        account_id: str,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TransactionResponse]:
        """Get transactions for a specific account."""
        transactions = await self.transaction_repo.get_transactions_for_account(
            user_id, account_id, skip, limit, start_date, end_date
        )
        
        return [TransactionResponse.model_validate(t) for t in transactions]
    
    async def get_duplicate_transactions(self, user_id: str) -> List[List[TransactionResponse]]:
        """Find potential duplicate transactions."""
        duplicate_groups = await self.transaction_repo.get_duplicate_transactions(user_id)
        
        return [
            [TransactionResponse.model_validate(t) for t in group]
            for group in duplicate_groups
        ]
    
    async def split_transaction(
        self,
        user_id: str,
        request: TransactionSplitRequest
    ) -> List[TransactionResponse]:
        """Split a transaction into multiple transactions."""
        # Get original transaction
        original_transaction = await self.transaction_repo.get_by_id_for_user(
            request.transaction_id, user_id
        )
        if not original_transaction:
            raise NotFoundError("Transaction not found")
        
        # Validate split amounts
        total_split_amount = sum(Decimal(str(split["amount"])) for split in request.splits)
        if abs(total_split_amount - abs(original_transaction.amount)) > Decimal('0.01'):
            raise ValidationError("Split amounts must equal original transaction amount")
        
        # Create split transactions
        split_transactions = []
        
        for i, split in enumerate(request.splits):
            split_data = TransactionCreate(
                account_id=original_transaction.account_id,
                amount=Decimal(str(split["amount"])),
                date=original_transaction.date,
                description=split.get("description", f"{original_transaction.description} (split {i+1})"),
                merchant_name=original_transaction.merchant_name,
                type=original_transaction.type,
                status=original_transaction.status,
                category=split.get("category", original_transaction.category),
                subcategory=split.get("subcategory", original_transaction.subcategory),
                category_type=split.get("category_type", original_transaction.category_type),
                notes=split.get("notes")
            )
            
            split_transaction = await self.transaction_repo.create_for_user(user_id, split_data)
            split_transactions.append(TransactionResponse.model_validate(split_transaction))
        
        # Mark original transaction as split (could add a flag or delete it)
        update_data = TransactionUpdate(
            notes=f"Split into {len(request.splits)} transactions",
            is_excluded_from_budgets=True
        )
        await self.transaction_repo.update(request.transaction_id, update_data)
        
        return split_transactions
    
    async def _auto_categorize_transaction(
        self,
        merchant_name: Optional[str],
        description: str,
        amount: Decimal
    ) -> Optional[str]:
        """Auto-categorize transaction based on merchant and description."""
        # TODO: Implement proper auto-categorization logic
        # This could use ML models, rules engine, or merchant databases
        
        if not merchant_name:
            return None
        
        merchant_lower = merchant_name.lower()
        
        # Simple rule-based categorization
        if any(keyword in merchant_lower for keyword in ['grocery', 'supermarket', 'food']):
            return "Food & Dining"
        elif any(keyword in merchant_lower for keyword in ['gas', 'fuel', 'shell', 'exxon']):
            return "Transportation"
        elif any(keyword in merchant_lower for keyword in ['amazon', 'walmart', 'target']):
            return "Shopping"
        elif any(keyword in merchant_lower for keyword in ['restaurant', 'cafe', 'mcdonald']):
            return "Food & Dining"
        elif any(keyword in merchant_lower for keyword in ['netflix', 'spotify', 'hulu']):
            return "Entertainment"
        elif any(keyword in merchant_lower for keyword in ['church', 'tithe', 'offering']):
            return "Charitable Giving"
        
        return None