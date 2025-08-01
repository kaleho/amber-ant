"""Transaction API router."""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from src.transactions.service import TransactionService
from src.transactions.schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse, TransactionListResponse,
    TransactionSummaryResponse, TransactionTrendResponse, TransactionBulkUpdate,
    TransactionCategorizationRequest, TransactionSplitRequest, TransactionType
)
from src.auth.dependencies import get_current_active_user
from src.exceptions import NotFoundError, ValidationError

router = APIRouter()

# Initialize service
transaction_service = TransactionService()


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new transaction."""
    try:
        return await transaction_service.create_transaction(
            current_user["user_id"], 
            transaction_data
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=TransactionListResponse)
async def get_user_transactions(
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of transactions to return"),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    search: Optional[str] = Query(None, description="Search in description and merchant name"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get user's transactions with filtering."""
    return await transaction_service.get_user_transactions(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit,
        account_id=account_id,
        category=category,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type.value if transaction_type else None,
        search=search
    )


@router.get("/summary", response_model=TransactionSummaryResponse)
async def get_transaction_summary(
    start_date: Optional[date] = Query(None, description="Summary start date"),
    end_date: Optional[date] = Query(None, description="Summary end date"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get transaction summary for current user."""
    return await transaction_service.get_transaction_summary(
        current_user["user_id"],
        start_date,
        end_date
    )


@router.get("/trends", response_model=TransactionTrendResponse)
async def get_transaction_trends(
    period_days: int = Query(90, ge=7, le=365, description="Analysis period in days"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get transaction trend analysis."""
    return await transaction_service.get_transaction_trend(
        current_user["user_id"],
        period_days
    )


@router.get("/spending/by-category")
async def get_spending_by_category(
    start_date: Optional[date] = Query(None, description="Filter start date"),
    end_date: Optional[date] = Query(None, description="Filter end date"),
    category_type: Optional[str] = Query(None, description="Filter by category type (fixed/discretionary)"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get spending breakdown by category."""
    spending = await transaction_service.get_spending_by_category(
        current_user["user_id"],
        start_date,
        end_date,
        category_type
    )
    
    return {"spending_by_category": spending}


@router.get("/uncategorized", response_model=List[TransactionResponse])
async def get_uncategorized_transactions(
    limit: int = Query(100, ge=1, le=1000, description="Number of transactions to return"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get uncategorized transactions."""
    return await transaction_service.get_uncategorized_transactions(
        current_user["user_id"],
        limit
    )


@router.get("/duplicates")
async def get_duplicate_transactions(
    current_user: dict = Depends(get_current_active_user)
):
    """Find potential duplicate transactions."""
    duplicates = await transaction_service.get_duplicate_transactions(current_user["user_id"])
    
    return {
        "duplicate_groups": duplicates,
        "total_groups": len(duplicates),
        "total_duplicates": sum(len(group) for group in duplicates)
    }


@router.post("/categorize")
async def categorize_transactions(
    request: TransactionCategorizationRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Auto-categorize transactions."""
    return await transaction_service.categorize_transactions(
        current_user["user_id"],
        request
    )


@router.put("/bulk-update")
async def bulk_update_transactions(
    request: TransactionBulkUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Bulk update multiple transactions."""
    try:
        return await transaction_service.bulk_update_transactions(
            current_user["user_id"],
            request
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{transaction_id}/split", response_model=List[TransactionResponse])
async def split_transaction(
    request: TransactionSplitRequest,
    transaction_id: str = Path(..., description="Transaction ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Split a transaction into multiple transactions."""
    try:
        # Override transaction_id from path
        request.transaction_id = transaction_id
        
        return await transaction_service.split_transaction(
            current_user["user_id"],
            request
        )
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Transaction not found")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str = Path(..., description="Transaction ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get transaction by ID."""
    transaction = await transaction_service.get_transaction(
        transaction_id, 
        current_user["user_id"]
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_data: TransactionUpdate,
    transaction_id: str = Path(..., description="Transaction ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Update transaction."""
    try:
        transaction = await transaction_service.update_transaction(
            transaction_id,
            current_user["user_id"],
            transaction_data
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return transaction
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str = Path(..., description="Transaction ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete transaction."""
    success = await transaction_service.delete_transaction(
        transaction_id, 
        current_user["user_id"]
    )
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"message": "Transaction deleted successfully"}


# Account-specific transaction endpoints
@router.get("/account/{account_id}", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: str = Path(..., description="Account ID"),
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of transactions to return"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    current_user: dict = Depends(get_current_active_user)
):
    """Get transactions for a specific account."""
    return await transaction_service.get_transactions_for_account(
        current_user["user_id"],
        account_id,
        skip,
        limit,
        start_date,
        end_date
    )