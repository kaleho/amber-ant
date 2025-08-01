"""Budget management API endpoints."""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from decimal import Decimal

from src.budgets.service import BudgetService
from src.budgets.schemas import (
    BudgetResponse, BudgetCreate, BudgetUpdate, BudgetListResponse,
    BudgetSummaryResponse, BudgetAnalysisResponse, BudgetForecastResponse,
    BudgetCategoryResponse, BudgetCategoryCreate, BudgetCategoryUpdate,
    BudgetAlertResponse, Budget, BudgetSummary, BudgetCategory,
    BudgetTemplateCreate, BudgetTemplateUpdate, BudgetTemplate,
    CreateBudgetFromTemplate, BudgetAnalytics
)
from src.budgets.models import BudgetStatus
from src.auth.dependencies import get_current_user
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError

router = APIRouter()


# Budget CRUD operations
@router.get("/", response_model=List[Budget])
async def get_budgets(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[BudgetStatus] = Query(None, description="Filter by budget status"),
    period: Optional[str] = Query(None, description="Filter by budget period"),
    search: Optional[str] = Query(None, description="Search budgets by name"),
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Get user's budgets with pagination and filtering."""
    try:
        # Use existing service method with filters
        budgets = await budget_service.get_user_budgets(
            user_id=current_user["sub"],
            status=status
        )
        
        # Apply search filter if provided
        if search:
            budgets = [b for b in budgets if search.lower() in b.name.lower()]
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_budgets = budgets[start:end]
        
        return paginated_budgets
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get budgets: {str(e)}")


@router.get("/current", response_model=Budget)
async def get_current_budget(
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Get current active budget for user."""
    budget = await budget_service.get_current_budget(current_user["sub"])
    if not budget:
        raise HTTPException(status_code=404, detail="No current budget found")
    return budget


@router.get("/{budget_id}", response_model=Budget)
async def get_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Get specific budget by ID."""
    try:
        budget = await budget_service.get_budget(budget_id, current_user["sub"])
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        return budget
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get budget: {str(e)}")


@router.post("/", response_model=Budget, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Create a new budget."""
    try:
        budget = await budget_service.create_budget(
            budget_data=budget_data,
            user_id=current_user["sub"],
            created_by=current_user["sub"]
        )
        return budget
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create budget: {str(e)}")


@router.put("/{budget_id}", response_model=Budget)
async def update_budget(
    budget_id: str,
    budget_data: BudgetUpdate,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Update budget information."""
    try:
        budget = await budget_service.update_budget(
            budget_id=budget_id,
            budget_data=budget_data,
            user_id=current_user["sub"]
        )
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        return budget
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update budget: {str(e)}")


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Delete a budget."""
    try:
        success = await budget_service.delete_budget(budget_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Budget not found")
            
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete budget: {str(e)}")


# Budget categories
@router.get("/{budget_id}/categories", response_model=List[BudgetCategory])
async def get_budget_categories(
    budget_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Get categories for a specific budget."""
    try:
        # Verify budget ownership first
        budget = await budget_service.get_budget(budget_id, current_user["sub"])
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        # Return categories from the budget
        return budget.categories or []
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.post("/{budget_id}/categories", response_model=BudgetCategory, status_code=status.HTTP_201_CREATED)
async def create_budget_category(
    budget_id: str,
    category_data: BudgetCategoryCreate,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Add a category to a budget."""
    try:
        category = await budget_service.add_category_to_budget(
            budget_id=budget_id,
            category_data=category_data,
            user_id=current_user["sub"]
        )
        return category
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")


@router.put("/{budget_id}/categories/{category_id}", response_model=BudgetCategory)
async def update_budget_category(
    budget_id: str,
    category_id: str,
    category_data: BudgetCategoryUpdate,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Update a budget category."""
    try:
        # Verify budget ownership
        budget = await budget_service.get_budget(budget_id, current_user["sub"])
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        category = await budget_service.update_category(
            category_id=category_id,
            category_data=category_data,
            user_id=current_user["sub"]
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")


@router.delete("/{budget_id}/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_category(
    budget_id: str,
    category_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Delete a budget category."""
    try:
        # Verify budget ownership
        budget = await budget_service.get_budget(budget_id, current_user["sub"])
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        success = await budget_service.delete_category(category_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
            
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete category: {str(e)}")


# Budget management operations
@router.post("/{budget_id}/sync", response_model=Budget)
async def sync_budget_spending(
    budget_id: str,
    force_sync: bool = Query(False, description="Force sync even if recently synced"),
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Sync budget spending with actual transactions."""
    try:
        # Get budget and sync spending amounts
        budget = await budget_service.get_budget(budget_id, current_user["sub"])
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        
        # TODO: Implement actual transaction sync logic
        # For now, return the existing budget
        return budget
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync budget: {str(e)}")


@router.post("/{budget_id}/pause")
async def pause_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Pause a budget."""
    try:
        budget = await budget_service.update_budget(
            budget_id=budget_id,
            budget_data=BudgetUpdate(status=BudgetStatus.PAUSED),
            user_id=current_user["sub"]
        )
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        return {"message": "Budget paused successfully", "budget": budget}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause budget: {str(e)}")


@router.post("/{budget_id}/resume")
async def resume_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Resume a paused budget."""
    try:
        budget = await budget_service.update_budget(
            budget_id=budget_id,
            budget_data=BudgetUpdate(status=BudgetStatus.ACTIVE),
            user_id=current_user["sub"]
        )
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        return {"message": "Budget resumed successfully", "budget": budget}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume budget: {str(e)}")


# Analytics and reporting
@router.get("/analytics", response_model=BudgetAnalytics)
async def get_budget_analytics(
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Get budget analytics for the current user."""
    try:
        analytics = await budget_service.get_budget_analytics(current_user["sub"])
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# Alerts and notifications
@router.get("/alerts", response_model=List[dict])
async def get_budget_alerts(
    unread_only: bool = Query(False, description="Get only unread alerts"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of alerts"),
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Get budget alerts for user."""
    try:
        alerts = await budget_service.get_user_alerts(
            user_id=current_user["sub"],
            unread_only=unread_only
        )
        
        # Apply limit
        return alerts[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts/{alert_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_alert_as_read(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Mark budget alert as read."""
    try:
        success = await budget_service.mark_alert_as_read(alert_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark alert: {str(e)}")


@router.post("/alerts/{alert_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Dismiss a budget alert."""
    try:
        success = await budget_service.dismiss_alert(alert_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dismiss alert: {str(e)}")


# Template endpoints
@router.post("/templates", response_model=BudgetTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: BudgetTemplateCreate,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Create budget template."""
    try:
        template = await budget_service.create_template(
            template_data=template_data,
            user_id=current_user["sub"],
            created_by=current_user["sub"]
        )
        return template
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates")
async def get_budget_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Get available budget templates."""
    try:
        # For now, return empty list - would be implemented with template repository
        return {"templates": []}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.post("/templates/{template_id}/create-budget", response_model=Budget, status_code=status.HTTP_201_CREATED)
async def create_budget_from_template(
    template_id: str,
    request: CreateBudgetFromTemplate,
    current_user: dict = Depends(get_current_user),
    budget_service: BudgetService = Depends()
):
    """Create budget from template."""
    try:
        # Override template_id from path
        request.template_id = template_id
        
        budget = await budget_service.create_budget_from_template(
            request=request,
            user_id=current_user["sub"],
            created_by=current_user["sub"]
        )
        return budget
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health and maintenance
@router.get("/health")
async def budget_service_health():
    """Check budget service health."""
    try:
        service = BudgetService()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "budgets",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }