"""Tithing service for business logic."""
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db_session
from src.tithing.repository import (
    TithingPaymentRepository,
    TithingScheduleRepository,
    TithingSummaryRepository,
    TithingGoalRepository
)
from src.tithing.models import (
    TithingPayment,
    TithingSchedule,
    TithingSummary,
    TithingGoal
)
from src.tithing.schemas import (
    TithingPaymentCreate,
    TithingPaymentUpdate,
    TithingScheduleCreate,
    TithingGoalCreate,
    TithingAnalysisResponse,
    TithingFrequency
)
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError


class TithingService:
    """Service for tithing operations."""
    
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session
        self.payment_repo = TithingPaymentRepository(session)
        self.schedule_repo = TithingScheduleRepository(session)
        self.summary_repo = TithingSummaryRepository(session)
        self.goal_repo = TithingGoalRepository(session)
    
    # Payment operations
    async def create_payment(
        self,
        payment_data: TithingPaymentCreate,
        user_id: str
    ) -> TithingPayment:
        """Create a new tithing payment."""
        # Validate payment data
        if payment_data.amount <= 0:
            raise ValidationError("Payment amount must be greater than zero")
        
        if payment_data.date > date.today():
            raise ValidationError("Payment date cannot be in the future")
        
        # Create payment
        payment = await self.payment_repo.create_payment(payment_data, user_id)
        
        # Update related summaries and goals
        await self._update_summaries_after_payment(payment)
        await self._update_goals_after_payment(payment)
        
        return payment
    
    async def get_payments(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        recipient: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[TithingPayment]:
        """Get payments with optional filters."""
        if start_date and end_date:
            return await self.payment_repo.get_payments_by_date_range(
                user_id, start_date, end_date, limit, offset
            )
        elif recipient:
            return await self.payment_repo.get_payments_by_recipient(
                user_id, recipient, limit
            )
        else:
            return await self.payment_repo.get_by_user_id(user_id, limit, offset)
    
    async def get_payment(
        self,
        payment_id: str,
        user_id: str
    ) -> Optional[TithingPayment]:
        """Get payment by ID."""
        return await self.payment_repo.get_by_id_and_user(payment_id, user_id)
    
    async def update_payment(
        self,
        payment_id: str,
        payment_data: TithingPaymentUpdate,
        user_id: str
    ) -> Optional[TithingPayment]:
        """Update payment."""
        payment = await self.payment_repo.update_payment(payment_id, user_id, payment_data)
        
        if payment:
            # Recalculate summaries and goals
            await self._update_summaries_after_payment(payment)
            await self._update_goals_after_payment(payment)
        
        return payment
    
    async def delete_payment(
        self,
        payment_id: str,
        user_id: str
    ) -> bool:
        """Delete payment."""
        payment = await self.payment_repo.get_by_id_and_user(payment_id, user_id)
        if not payment:
            return False
        
        await self.payment_repo.delete(payment_id)
        
        # Recalculate summaries and goals
        await self._recalculate_year_summary(user_id, payment.date.year)
        await self._recalculate_goals_for_year(user_id, payment.date.year)
        
        return True
    
    # Schedule operations
    async def create_schedule(
        self,
        schedule_data: TithingScheduleCreate,
        user_id: str
    ) -> TithingSchedule:
        """Create a new tithing schedule."""
        # Validate schedule data
        if schedule_data.amount <= 0:
            raise ValidationError("Schedule amount must be greater than zero")
        
        if schedule_data.start_date < date.today():
            raise ValidationError("Schedule start date cannot be in the past")
        
        if schedule_data.end_date and schedule_data.end_date <= schedule_data.start_date:
            raise ValidationError("Schedule end date must be after start date")
        
        # Calculate next execution date
        next_execution = self._calculate_next_execution_date(
            schedule_data.start_date, schedule_data.frequency
        )
        
        schedule = await self.schedule_repo.create_schedule(schedule_data, user_id)
        schedule.next_execution_date = next_execution
        
        await self.session.commit()
        await self.session.refresh(schedule)
        
        return schedule
    
    async def get_schedules(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[TithingSchedule]:
        """Get schedules for user."""
        if active_only:
            return await self.schedule_repo.get_active_schedules(user_id)
        else:
            return await self.schedule_repo.get_by_user_id(user_id)
    
    async def get_schedule(
        self,
        schedule_id: str,
        user_id: str
    ) -> Optional[TithingSchedule]:
        """Get schedule by ID."""
        return await self.schedule_repo.get_by_id_and_user(schedule_id, user_id)
    
    async def process_due_schedules(
        self,
        user_id: str,
        process_date: Optional[date] = None
    ) -> List[TithingPayment]:
        """Process schedules that are due."""
        if not process_date:
            process_date = date.today()
        
        due_schedules = await self.schedule_repo.get_schedules_due(user_id, process_date)
        created_payments = []
        
        for schedule in due_schedules:
            # Create payment from schedule
            payment_data = TithingPaymentCreate(
                amount=schedule.amount,
                date=process_date,
                method=schedule.method,
                recipient=schedule.recipient,
                purpose="regular_tithe",
                notes=f"Automatic payment from schedule: {schedule.name}"
            )
            
            payment = await self.create_payment(payment_data, user_id)
            created_payments.append(payment)
            
            # Update schedule execution
            next_execution = self._calculate_next_execution_date(
                process_date, schedule.frequency
            )
            
            await self.schedule_repo.update_schedule_execution(
                schedule.id, user_id, datetime.utcnow(), next_execution
            )
        
        return created_payments
    
    # Summary operations
    async def get_year_summary(
        self,
        user_id: str,
        year: int
    ) -> TithingSummary:
        """Get or create summary for a specific year."""
        summary = await self.summary_repo.get_or_create_year_summary(user_id, year)
        
        # Recalculate if not recent
        if not summary.last_calculated_at or \
           (datetime.utcnow() - summary.last_calculated_at).days > 1:
            await self._recalculate_year_summary(user_id, year)
            await self.session.refresh(summary)
        
        return summary
    
    async def get_monthly_breakdown(
        self,
        user_id: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """Get monthly breakdown for a year."""
        return await self.payment_repo.get_monthly_totals(user_id, year)
    
    # Goal operations
    async def create_goal(
        self,
        goal_data: TithingGoalCreate,
        user_id: str
    ) -> TithingGoal:
        """Create a new tithing goal."""
        # Validate goal data
        if goal_data.start_date >= goal_data.end_date:
            raise ValidationError("Goal end date must be after start date")
        
        if goal_data.target_percentage <= 0:
            raise ValidationError("Target percentage must be greater than zero")
        
        if goal_data.target_amount and goal_data.target_amount <= 0:
            raise ValidationError("Target amount must be greater than zero")
        
        goal = await self.goal_repo.create_goal(goal_data, user_id)
        
        # Calculate initial progress
        await self._update_goal_progress(goal)
        
        return goal
    
    async def get_goals(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[TithingGoal]:
        """Get goals for user."""
        if active_only:
            return await self.goal_repo.get_active_goals(user_id)
        else:
            return await self.goal_repo.get_by_user_id(user_id)
    
    async def get_goal(
        self,
        goal_id: str,
        user_id: str
    ) -> Optional[TithingGoal]:
        """Get goal by ID."""
        return await self.goal_repo.get_by_id_and_user(goal_id, user_id)
    
    # Analysis operations
    async def get_tithing_analysis(
        self,
        user_id: str,
        year: int
    ) -> TithingAnalysisResponse:
        """Get comprehensive tithing analysis."""
        # Get year summary
        summary = await self.get_year_summary(user_id, year)
        
        # Get monthly breakdown
        monthly_data = await self.get_monthly_breakdown(user_id, year)
        
        # Get recipient breakdown
        recipient_data = await self.payment_repo.get_recipient_totals(
            user_id, date(year, 1, 1), date(year, 12, 31)
        )
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(monthly_data)
        
        # Generate insights and recommendations
        insights = self._generate_insights(summary, monthly_data, consistency_score)
        recommendations = self._generate_recommendations(summary, consistency_score)
        
        # Determine faithfulness rating
        faithfulness_rating = self._get_faithfulness_rating(
            summary.current_percentage, consistency_score
        )
        
        return TithingAnalysisResponse(
            period=str(year),
            consistency_score=consistency_score,
            faithfulness_rating=faithfulness_rating,
            average_percentage=summary.current_percentage,
            trend_direction="stable",  # TODO: Calculate trend
            insights=insights,
            recommendations=recommendations,
            monthly_breakdown=[
                {
                    "month": self._get_month_name(item["month"]),
                    "amount": str(item["total"]),
                    "percentage": str(item["total"] / summary.tithing_eligible_income * 100)
                    if summary.tithing_eligible_income > 0 else "0"
                }
                for item in monthly_data
            ],
            recipient_analysis={
                item["recipient"]: {
                    "total_amount": str(item["total"]),
                    "percentage_of_total": str(
                        item["total"] / summary.total_tithe_paid * 100
                    ) if summary.total_tithe_paid > 0 else "0",
                    "frequency": "regular"  # TODO: Calculate frequency
                }
                for item in recipient_data
            }
        )
    
    # Private helper methods
    async def _update_summaries_after_payment(self, payment: TithingPayment):
        """Update summaries after a payment."""
        await self._recalculate_year_summary(payment.user_id, payment.date.year)
    
    async def _update_goals_after_payment(self, payment: TithingPayment):
        """Update goals after a payment."""
        goals = await self.goal_repo.get_goals_by_year(payment.user_id, payment.date.year)
        
        for goal in goals:
            if goal.start_date <= payment.date <= goal.end_date:
                await self._update_goal_progress(goal)
    
    async def _recalculate_year_summary(self, user_id: str, year: int):
        """Recalculate year summary."""
        # Get all payments for the year
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        payments = await self.payment_repo.get_payments_by_date_range(
            user_id, start_date, end_date
        )
        
        # Calculate totals
        total_paid = sum(p.amount for p in payments)
        payment_count = len(payments)
        
        # Get recipient breakdown
        recipient_totals = await self.payment_repo.get_recipient_totals(
            user_id, start_date, end_date
        )
        
        # Get method breakdown
        method_breakdown = {}
        for payment in payments:
            method = payment.method
            method_breakdown[method] = method_breakdown.get(method, Decimal('0')) + payment.amount
        
        # Update summary
        summary_data = {
            'total_tithe_paid': total_paid,
            'payment_count': payment_count,
            'average_payment': total_paid / payment_count if payment_count > 0 else Decimal('0'),
            'largest_payment': max((p.amount for p in payments), default=Decimal('0')),
            'current_percentage': Decimal('10.0'),  # TODO: Calculate from income
            'payment_methods': method_breakdown,
            'recipients': {r['recipient']: r['total'] for r in recipient_totals}
        }
        
        await self.summary_repo.update_summary_calculations(user_id, year, summary_data)
    
    async def _recalculate_goals_for_year(self, user_id: str, year: int):
        """Recalculate all goals for a year."""
        goals = await self.goal_repo.get_goals_by_year(user_id, year)
        
        for goal in goals:
            await self._update_goal_progress(goal)
    
    async def _update_goal_progress(self, goal: TithingGoal):
        """Update progress for a specific goal."""
        # Get payments within goal period
        payments = await self.payment_repo.get_payments_by_date_range(
            goal.user_id, goal.start_date, goal.end_date
        )
        
        current_amount = sum(p.amount for p in payments)
        
        # TODO: Calculate current percentage based on income
        current_percentage = Decimal('10.0')  # Placeholder
        
        await self.goal_repo.update_goal_progress(
            goal.id, goal.user_id, current_amount, current_percentage
        )
    
    def _calculate_next_execution_date(
        self,
        start_date: date,
        frequency: TithingFrequency
    ) -> date:
        """Calculate next execution date based on frequency."""
        if frequency == TithingFrequency.WEEKLY:
            return start_date + timedelta(weeks=1)
        elif frequency == TithingFrequency.BIWEEKLY:
            return start_date + timedelta(weeks=2)
        elif frequency == TithingFrequency.MONTHLY:
            return start_date + relativedelta(months=1)
        elif frequency == TithingFrequency.QUARTERLY:
            return start_date + relativedelta(months=3)
        elif frequency == TithingFrequency.YEARLY:
            return start_date + relativedelta(years=1)
        else:
            return start_date
    
    def _calculate_consistency_score(self, monthly_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate consistency score based on monthly data."""
        if not monthly_data:
            return Decimal('0')
        
        # Simple consistency calculation based on payment frequency
        months_with_payments = len([m for m in monthly_data if m['count'] > 0])
        return Decimal(str(months_with_payments / 12 * 100))
    
    def _generate_insights(
        self,
        summary: TithingSummary,
        monthly_data: List[Dict[str, Any]],
        consistency_score: Decimal
    ) -> List[str]:
        """Generate tithing insights."""
        insights = []
        
        if consistency_score >= 90:
            insights.append("You've been very consistent with your tithing")
        elif consistency_score >= 70:
            insights.append("You have good tithing consistency with room for improvement")
        else:
            insights.append("Consider establishing a more regular tithing pattern")
        
        if summary.current_percentage >= Decimal('10'):
            insights.append("Your giving meets or exceeds the traditional 10% standard")
        else:
            insights.append("Consider working toward the traditional 10% tithing goal")
        
        return insights
    
    def _generate_recommendations(
        self,
        summary: TithingSummary,
        consistency_score: Decimal
    ) -> List[str]:
        """Generate tithing recommendations."""
        recommendations = []
        
        if consistency_score < 80:
            recommendations.append("Consider setting up automatic transfers for more consistency")
        
        if summary.current_percentage < Decimal('10'):
            recommendations.append("Gradually increase your tithing percentage toward 10%")
        
        recommendations.append("Continue your faithful giving and track your progress")
        
        return recommendations
    
    def _get_faithfulness_rating(
        self,
        percentage: Decimal,
        consistency: Decimal
    ) -> str:
        """Get faithfulness rating based on percentage and consistency."""
        if percentage >= Decimal('10') and consistency >= 90:
            return "excellent"
        elif percentage >= Decimal('8') and consistency >= 75:
            return "good"
        elif percentage >= Decimal('5') and consistency >= 50:
            return "fair"
        else:
            return "needs_improvement"
    
    def _get_month_name(self, month_number: int) -> str:
        """Get month name from number."""
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return months[month_number - 1] if 1 <= month_number <= 12 else "Unknown"