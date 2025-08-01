"""Tithing repository for database operations."""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, desc, asc, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.repository import UserScopedRepository
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
    TithingGoalCreate
)


class TithingPaymentRepository(UserScopedRepository[TithingPayment]):
    """Repository for tithing payment operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TithingPayment)
    
    async def create_payment(
        self,
        payment_data: TithingPaymentCreate,
        user_id: str
    ) -> TithingPayment:
        """Create a new tithing payment."""
        payment = TithingPayment(
            user_id=user_id,
            **payment_data.model_dump()
        )
        
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
    
    async def get_payments_by_date_range(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[TithingPayment]:
        """Get payments within a date range."""
        query = select(TithingPayment).where(
            and_(
                TithingPayment.user_id == user_id,
                TithingPayment.date >= start_date,
                TithingPayment.date <= end_date
            )
        ).order_by(desc(TithingPayment.date))
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_payments_by_recipient(
        self,
        user_id: str,
        recipient: str,
        limit: Optional[int] = None
    ) -> List[TithingPayment]:
        """Get payments by recipient."""
        query = select(TithingPayment).where(
            and_(
                TithingPayment.user_id == user_id,
                TithingPayment.recipient.ilike(f"%{recipient}%")
            )
        ).order_by(desc(TithingPayment.date))
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_total_by_year(
        self,
        user_id: str,
        year: int
    ) -> Decimal:
        """Get total tithing amount for a specific year."""
        query = select(func.sum(TithingPayment.amount)).where(
            and_(
                TithingPayment.user_id == user_id,
                extract('year', TithingPayment.date) == year
            )
        )
        
        result = await self.session.execute(query)
        total = result.scalar()
        return total or Decimal('0')
    
    async def get_monthly_totals(
        self,
        user_id: str,
        year: int
    ) -> List[Dict[str, Any]]:
        """Get monthly totals for a specific year."""
        query = select(
            extract('month', TithingPayment.date).label('month'),
            func.sum(TithingPayment.amount).label('total'),
            func.count(TithingPayment.id).label('count')
        ).where(
            and_(
                TithingPayment.user_id == user_id,
                extract('year', TithingPayment.date) == year
            )
        ).group_by(
            extract('month', TithingPayment.date)
        ).order_by('month')
        
        result = await self.session.execute(query)
        return [
            {
                'month': int(row.month),
                'total': row.total or Decimal('0'),
                'count': row.count or 0
            }
            for row in result
        ]
    
    async def get_recipient_totals(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get totals by recipient for a date range."""
        query = select(
            TithingPayment.recipient,
            func.sum(TithingPayment.amount).label('total'),
            func.count(TithingPayment.id).label('count')
        ).where(
            and_(
                TithingPayment.user_id == user_id,
                TithingPayment.date >= start_date,
                TithingPayment.date <= end_date
            )
        ).group_by(
            TithingPayment.recipient
        ).order_by(desc('total'))
        
        result = await self.session.execute(query)
        return [
            {
                'recipient': row.recipient,
                'total': row.total or Decimal('0'),
                'count': row.count or 0
            }
            for row in result
        ]
    
    async def update_payment(
        self,
        payment_id: str,
        user_id: str,
        update_data: TithingPaymentUpdate
    ) -> Optional[TithingPayment]:
        """Update a tithing payment."""
        payment = await self.get_by_id_and_user(payment_id, user_id)
        if not payment:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(payment, field, value)
        
        payment.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(payment)
        return payment


class TithingScheduleRepository(UserScopedRepository[TithingSchedule]):
    """Repository for tithing schedule operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TithingSchedule)
    
    async def create_schedule(
        self,
        schedule_data: TithingScheduleCreate,
        user_id: str
    ) -> TithingSchedule:
        """Create a new tithing schedule."""
        schedule = TithingSchedule(
            user_id=user_id,
            **schedule_data.model_dump()
        )
        
        self.session.add(schedule)
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule
    
    async def get_active_schedules(
        self,
        user_id: str
    ) -> List[TithingSchedule]:
        """Get all active schedules for user."""
        query = select(TithingSchedule).where(
            and_(
                TithingSchedule.user_id == user_id,
                TithingSchedule.is_active == True
            )
        ).order_by(TithingSchedule.next_execution_date)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_schedules_due(
        self,
        user_id: str,
        due_date: date
    ) -> List[TithingSchedule]:
        """Get schedules due on or before a specific date."""
        query = select(TithingSchedule).where(
            and_(
                TithingSchedule.user_id == user_id,
                TithingSchedule.is_active == True,
                TithingSchedule.auto_process == True,
                TithingSchedule.next_execution_date <= due_date
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_schedule_execution(
        self,
        schedule_id: str,
        user_id: str,
        execution_date: datetime,
        next_execution_date: Optional[date] = None
    ) -> Optional[TithingSchedule]:
        """Update schedule after execution."""
        schedule = await self.get_by_id_and_user(schedule_id, user_id)
        if not schedule:
            return None
        
        schedule.last_executed_at = execution_date
        schedule.execution_count += 1
        if next_execution_date:
            schedule.next_execution_date = next_execution_date
        
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule


class TithingSummaryRepository(UserScopedRepository[TithingSummary]):
    """Repository for tithing summary operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TithingSummary)
    
    async def get_or_create_year_summary(
        self,
        user_id: str,
        year: int
    ) -> TithingSummary:
        """Get or create summary for a specific year."""
        query = select(TithingSummary).where(
            and_(
                TithingSummary.user_id == user_id,
                TithingSummary.year == year
            )
        )
        
        result = await self.session.execute(query)
        summary = result.scalar_one_or_none()
        
        if not summary:
            summary = TithingSummary(
                user_id=user_id,
                year=year,
                period_start=date(year, 1, 1),
                period_end=date(year, 12, 31)
            )
            self.session.add(summary)
            await self.session.commit()
            await self.session.refresh(summary)
        
        return summary
    
    async def update_summary_calculations(
        self,
        user_id: str,
        year: int,
        totals: Dict[str, Any]
    ) -> Optional[TithingSummary]:
        """Update summary with calculated totals."""
        summary = await self.get_or_create_year_summary(user_id, year)
        
        # Update calculated fields
        for field, value in totals.items():
            if hasattr(summary, field):
                setattr(summary, field, value)
        
        summary.last_calculated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(summary)
        return summary


class TithingGoalRepository(UserScopedRepository[TithingGoal]):
    """Repository for tithing goal operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TithingGoal)
    
    async def create_goal(
        self,
        goal_data: TithingGoalCreate,
        user_id: str
    ) -> TithingGoal:
        """Create a new tithing goal."""
        goal = TithingGoal(
            user_id=user_id,
            **goal_data.model_dump()
        )
        
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal
    
    async def get_active_goals(
        self,
        user_id: str
    ) -> List[TithingGoal]:
        """Get all active goals for user."""
        query = select(TithingGoal).where(
            and_(
                TithingGoal.user_id == user_id,
                TithingGoal.is_active == True,
                TithingGoal.is_completed == False
            )
        ).order_by(TithingGoal.end_date)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_goals_by_year(
        self,
        user_id: str,
        year: int
    ) -> List[TithingGoal]:
        """Get goals for a specific year."""
        query = select(TithingGoal).where(
            and_(
                TithingGoal.user_id == user_id,
                or_(
                    extract('year', TithingGoal.start_date) == year,
                    extract('year', TithingGoal.end_date) == year,
                    and_(
                        TithingGoal.start_date <= date(year, 12, 31),
                        TithingGoal.end_date >= date(year, 1, 1)
                    )
                )
            )
        ).order_by(TithingGoal.start_date)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_goal_progress(
        self,
        goal_id: str,
        user_id: str,
        current_amount: Decimal,
        current_percentage: Decimal
    ) -> Optional[TithingGoal]:
        """Update goal progress."""
        goal = await self.get_by_id_and_user(goal_id, user_id)
        if not goal:
            return None
        
        goal.current_amount = current_amount
        goal.current_percentage = current_percentage
        
        # Check if goal is completed
        if (goal.target_amount and current_amount >= goal.target_amount) or \
           (current_percentage >= goal.target_percentage):
            goal.is_completed = True
            goal.completed_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(goal)
        return goal