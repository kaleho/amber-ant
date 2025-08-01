"""Tithing management API endpoints."""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.tithing.service import TithingService
from src.tithing.schemas import (
    TithingPaymentCreate, TithingPaymentUpdate, TithingPaymentResponse,
    TithingScheduleCreate, TithingScheduleResponse,
    TithingGoalCreate, TithingGoalResponse,
    TithingSummaryResponse, TithingAnalysisResponse,
    TithingListResponse
)
from src.auth.dependencies import get_current_user
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError

router = APIRouter()


# Payment endpoints
@router.post("/payments", response_model=TithingPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: TithingPaymentCreate,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Create a new tithing payment."""
    try:
        payment = await tithing_service.create_payment(
            payment_data=payment_data,
            user_id=current_user["sub"]
        )
        return payment
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/payments", response_model=List[TithingPaymentResponse])
async def get_payments(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    recipient: Optional[str] = Query(None, description="Recipient filter"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of payments to return"),
    offset: int = Query(0, ge=0, description="Number of payments to skip"),
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get tithing payments for the current user."""
    payments = await tithing_service.get_payments(
        user_id=current_user["sub"],
        start_date=start_date,
        end_date=end_date,
        recipient=recipient,
        limit=limit,
        offset=offset
    )
    return payments


@router.get("/payments/{payment_id}", response_model=TithingPaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get tithing payment by ID."""
    payment = await tithing_service.get_payment(payment_id, current_user["sub"])
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.put("/payments/{payment_id}", response_model=TithingPaymentResponse)
async def update_payment(
    payment_id: str,
    payment_data: TithingPaymentUpdate,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Update tithing payment."""
    try:
        payment = await tithing_service.update_payment(
            payment_id=payment_id,
            payment_data=payment_data,
            user_id=current_user["sub"]
        )
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Delete tithing payment."""
    success = await tithing_service.delete_payment(payment_id, current_user["sub"])
    if not success:
        raise HTTPException(status_code=404, detail="Payment not found")


# Schedule endpoints
@router.post("/schedules", response_model=TithingScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: TithingScheduleCreate,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Create a new tithing schedule."""
    try:
        schedule = await tithing_service.create_schedule(
            schedule_data=schedule_data,
            user_id=current_user["sub"]
        )
        return schedule
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules", response_model=List[TithingScheduleResponse])
async def get_schedules(
    active_only: bool = Query(True, description="Only return active schedules"),
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get tithing schedules for the current user."""
    schedules = await tithing_service.get_schedules(
        user_id=current_user["sub"],
        active_only=active_only
    )
    return schedules


@router.get("/schedules/{schedule_id}", response_model=TithingScheduleResponse)
async def get_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get tithing schedule by ID."""
    schedule = await tithing_service.get_schedule(schedule_id, current_user["sub"])
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.post("/schedules/process", response_model=List[TithingPaymentResponse])
async def process_due_schedules(
    process_date: Optional[date] = Query(None, description="Date to process schedules for"),
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Process schedules that are due."""
    payments = await tithing_service.process_due_schedules(
        user_id=current_user["sub"],
        process_date=process_date
    )
    return payments


# Summary endpoints
@router.get("/summary/{year}", response_model=TithingSummaryResponse)
async def get_year_summary(
    year: int,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get tithing summary for a specific year."""
    summary = await tithing_service.get_year_summary(
        user_id=current_user["sub"],
        year=year
    )
    return summary


@router.get("/analysis/{year}", response_model=TithingAnalysisResponse)
async def get_tithing_analysis(
    year: int,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get comprehensive tithing analysis for a year."""
    analysis = await tithing_service.get_tithing_analysis(
        user_id=current_user["sub"],
        year=year
    )
    return analysis


# Goal endpoints
@router.post("/goals", response_model=TithingGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: TithingGoalCreate,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Create a new tithing goal."""
    try:
        goal = await tithing_service.create_goal(
            goal_data=goal_data,
            user_id=current_user["sub"]
        )
        return goal
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/goals", response_model=List[TithingGoalResponse])
async def get_goals(
    active_only: bool = Query(True, description="Only return active goals"),
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get tithing goals for the current user."""
    goals = await tithing_service.get_goals(
        user_id=current_user["sub"],
        active_only=active_only
    )
    return goals


@router.get("/goals/{goal_id}", response_model=TithingGoalResponse)
async def get_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    tithing_service: TithingService = Depends()
):
    """Get tithing goal by ID."""
    goal = await tithing_service.get_goal(goal_id, current_user["sub"])
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal