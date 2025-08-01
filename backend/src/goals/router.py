"""Goals management API endpoints."""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from decimal import Decimal

from src.goals.service import GoalService
from src.goals.schemas import (
    SavingsGoalResponse, SavingsGoalCreate, SavingsGoalUpdate, GoalListResponse,
    GoalSummaryResponse, GoalAnalysisResponse, GoalContributionResponse,
    GoalContributionCreate, GoalMilestoneResponse, GoalMilestoneCreate,
    GoalInsightResponse
)
from src.auth.dependencies import get_current_user
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError

router = APIRouter()


# Goal CRUD operations
@router.get("/", response_model=List[SavingsGoalResponse])
async def get_goals(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by goal status"),
    goal_type: Optional[str] = Query(None, description="Filter by goal type"),
    search: Optional[str] = Query(None, description="Search goals by name"),
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get user's goals with pagination and filtering."""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if goal_type:
            filters["goal_type"] = goal_type
        if search:
            filters["name_contains"] = search
        
        goals_data = await goal_service.get_goals(
            user_id=current_user["sub"],
            page=page,
            per_page=per_page,
            filters=filters
        )
        return goals_data
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get goals: {str(e)}")


@router.get("/{goal_id}", response_model=SavingsGoalResponse)
async def get_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get specific goal by ID."""
    try:
        goal = await goal_service.get_goal(goal_id, current_user["sub"])
        return goal
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get goal: {str(e)}")


@router.post("/", response_model=SavingsGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: SavingsGoalCreate,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Create a new savings goal."""
    try:
        goal = await goal_service.create_goal(
            user_id=current_user["sub"],
            goal_data=goal_data
        )
        return goal
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")


@router.put("/{goal_id}", response_model=SavingsGoalResponse)
async def update_goal(
    goal_id: str,
    goal_data: SavingsGoalUpdate,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Update goal information."""
    try:
        goal = await goal_service.update_goal(
            goal_id=goal_id,
            user_id=current_user["sub"],
            goal_data=goal_data
        )
        return goal
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update goal: {str(e)}")


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Delete a goal."""
    try:
        success = await goal_service.delete_goal(goal_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")
            
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete goal: {str(e)}")


# Goal contributions
@router.get("/{goal_id}/contributions", response_model=List[GoalContributionResponse])
async def get_goal_contributions(
    goal_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of contributions"),
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get contributions for a specific goal."""
    try:
        contributions = await goal_service.get_goal_contributions(
            goal_id, current_user["sub"], limit
        )
        return contributions
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contributions: {str(e)}")


@router.post("/{goal_id}/contributions", response_model=GoalContributionResponse, status_code=status.HTTP_201_CREATED)
async def create_goal_contribution(
    goal_id: str,
    contribution_data: GoalContributionCreate,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Add a contribution to a goal."""
    try:
        contribution = await goal_service.create_contribution(
            goal_id=goal_id,
            user_id=current_user["sub"],
            contribution_data=contribution_data
        )
        return contribution
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create contribution: {str(e)}")


# Goal milestones
@router.get("/{goal_id}/milestones", response_model=List[GoalMilestoneResponse])
async def get_goal_milestones(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get milestones for a specific goal."""
    try:
        milestones = await goal_service.get_goal_milestones(goal_id, current_user["sub"])
        return milestones
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get milestones: {str(e)}")


@router.post("/{goal_id}/milestones", response_model=GoalMilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_goal_milestone(
    goal_id: str,
    milestone_data: GoalMilestoneCreate,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Add a milestone to a goal."""
    try:
        milestone = await goal_service.create_milestone(
            goal_id=goal_id,
            user_id=current_user["sub"],
            milestone_data=milestone_data
        )
        return milestone
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create milestone: {str(e)}")


@router.put("/milestones/{milestone_id}", response_model=GoalMilestoneResponse)
async def update_milestone(
    milestone_id: str,
    milestone_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Update a goal milestone."""
    try:
        milestone = await goal_service.update_milestone(
            milestone_id=milestone_id,
            user_id=current_user["sub"],
            milestone_data=milestone_data
        )
        return milestone
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update milestone: {str(e)}")


@router.delete("/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    milestone_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Delete a goal milestone."""
    try:
        success = await goal_service.delete_milestone(milestone_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Milestone not found")
            
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete milestone: {str(e)}")


# Goal management operations
@router.post("/{goal_id}/pause")
async def pause_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Pause a goal."""
    try:
        goal = await goal_service.pause_goal(goal_id, current_user["sub"])
        return {"message": "Goal paused successfully", "goal": goal}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause goal: {str(e)}")


@router.post("/{goal_id}/resume")
async def resume_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Resume a paused goal."""
    try:
        goal = await goal_service.resume_goal(goal_id, current_user["sub"])
        return {"message": "Goal resumed successfully", "goal": goal}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume goal: {str(e)}")


@router.post("/{goal_id}/complete")
async def complete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Mark a goal as completed."""
    try:
        goal = await goal_service.complete_goal(goal_id, current_user["sub"])
        return {"message": "Goal completed successfully", "goal": goal}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete goal: {str(e)}")


# Analytics and reporting
@router.get("/summary", response_model=GoalSummaryResponse)
async def get_goals_summary(
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get goals summary for user."""
    try:
        summary = await goal_service.get_goals_summary(current_user["sub"])
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/{goal_id}/analysis", response_model=GoalAnalysisResponse)
async def get_goal_analysis(
    goal_id: str,
    analysis_period: int = Query(90, ge=30, le=365, description="Analysis period in days"),
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get detailed goal analysis."""
    try:
        analysis = await goal_service.get_goal_analysis(
            goal_id=goal_id,
            user_id=current_user["sub"],
            analysis_period=analysis_period
        )
        return analysis
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


# Insights and recommendations
@router.get("/insights", response_model=List[GoalInsightResponse])
async def get_goal_insights(
    unread_only: bool = Query(False, description="Get only unread insights"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of insights"),
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get goal insights and recommendations for user."""
    try:
        insights = await goal_service.get_goal_insights(
            user_id=current_user["sub"],
            unread_only=unread_only,
            limit=limit
        )
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.put("/insights/{insight_id}/read")
async def mark_insight_as_read(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Mark goal insight as read."""
    try:
        success = await goal_service.mark_insight_as_read(insight_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Insight not found")
        return {"message": "Insight marked as read"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark insight: {str(e)}")


@router.delete("/insights/{insight_id}")
async def dismiss_insight(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Dismiss a goal insight."""
    try:
        success = await goal_service.dismiss_insight(insight_id, current_user["sub"])
        if not success:
            raise HTTPException(status_code=404, detail="Insight not found")
        return {"message": "Insight dismissed"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dismiss insight: {str(e)}")


# Utility endpoints
@router.get("/categories/suggestions")
async def get_goal_category_suggestions(
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get goal category suggestions."""
    try:
        suggestions = await goal_service.get_goal_category_suggestions(current_user["sub"])
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/templates")
async def get_goal_templates(
    goal_type: Optional[str] = Query(None, description="Filter by goal type"),
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Get available goal templates."""
    try:
        templates = await goal_service.get_goal_templates(
            user_id=current_user["sub"],
            goal_type=goal_type
        )
        return {"templates": templates}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.post("/templates/{template_id}/apply", response_model=SavingsGoalResponse)
async def apply_goal_template(
    template_id: str,
    template_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Apply a goal template to create a new goal."""
    try:
        goal = await goal_service.apply_goal_template(
            template_id=template_id,
            user_id=current_user["sub"],
            template_data=template_data
        )
        return goal
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply template: {str(e)}")


# Automated savings
@router.post("/{goal_id}/auto-save/enable")
async def enable_auto_save(
    goal_id: str,
    auto_save_config: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Enable automatic savings for a goal."""
    try:
        result = await goal_service.enable_auto_save(
            goal_id=goal_id,
            user_id=current_user["sub"],
            config=auto_save_config
        )
        return result
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable auto-save: {str(e)}")


@router.post("/{goal_id}/auto-save/disable")
async def disable_auto_save(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Disable automatic savings for a goal."""
    try:
        result = await goal_service.disable_auto_save(goal_id, current_user["sub"])
        return result
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable auto-save: {str(e)}")


# Health and maintenance
@router.get("/health")
async def goal_service_health():
    """Check goal service health."""
    try:
        service = GoalService()
        health_data = await service.get_service_health()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "goals",
            "version": "1.0.0",
            **health_data
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/maintenance/recalculate/{goal_id}")
async def recalculate_goal_progress(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends()
):
    """Recalculate goal progress and milestones (maintenance operation)."""
    try:
        result = await goal_service.recalculate_goal_progress(goal_id, current_user["sub"])
        return {
            "message": "Goal progress recalculated successfully",
            "updated_goal": result
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recalculate: {str(e)}")