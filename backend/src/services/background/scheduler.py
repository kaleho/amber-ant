"""Task scheduler for background operations."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

import structlog
from celery import current_app
from celery.schedules import crontab

from .celery_app import celery_app
from . import tasks

logger = structlog.get_logger(__name__)


class ScheduleType(Enum):
    """Schedule types for tasks."""
    INTERVAL = "interval"
    CRON = "cron"
    ONCE = "once"


class TaskScheduler:
    """Service for scheduling and managing background tasks."""
    
    def __init__(self):
        self.celery_app = celery_app
    
    async def schedule_account_sync(
        self,
        tenant_id: str,
        access_token: str,
        account_id: str = None,
        delay_seconds: int = 0
    ) -> str:
        """Schedule account data synchronization."""
        if delay_seconds > 0:
            task = tasks.sync_account_data.apply_async(
                args=[tenant_id, access_token, account_id],
                countdown=delay_seconds
            )
        else:
            task = tasks.sync_account_data.delay(tenant_id, access_token, account_id)
        
        logger.info("Account sync task scheduled",
                   tenant_id=tenant_id,
                   account_id=account_id,
                   task_id=task.id,
                   delay_seconds=delay_seconds)
        
        return task.id
    
    async def schedule_transaction_processing(
        self,
        tenant_id: str,
        access_token: str,
        start_date: str = None,
        end_date: str = None,
        account_ids: List[str] = None,
        delay_seconds: int = 0
    ) -> str:
        """Schedule transaction processing."""
        if delay_seconds > 0:
            task = tasks.process_transactions.apply_async(
                args=[tenant_id, access_token, start_date, end_date, account_ids],
                countdown=delay_seconds
            )
        else:
            task = tasks.process_transactions.delay(
                tenant_id, access_token, start_date, end_date, account_ids
            )
        
        logger.info("Transaction processing task scheduled",
                   tenant_id=tenant_id,
                   task_id=task.id,
                   delay_seconds=delay_seconds)
        
        return task.id
    
    async def schedule_notification_email(
        self,
        tenant_id: str,
        user_email: str,
        template: str,
        subject: str,
        data: Dict[str, Any] = None,
        delay_seconds: int = 0
    ) -> str:
        """Schedule notification email."""
        if delay_seconds > 0:
            task = tasks.send_notification_email.apply_async(
                args=[tenant_id, user_email, template, subject, data],
                countdown=delay_seconds
            )
        else:
            task = tasks.send_notification_email.delay(
                tenant_id, user_email, template, subject, data
            )
        
        logger.info("Notification email task scheduled",
                   tenant_id=tenant_id,
                   user_email=user_email,
                   template=template,
                   task_id=task.id,
                   delay_seconds=delay_seconds)
        
        return task.id
    
    async def schedule_monthly_report(
        self,
        tenant_id: str,
        month: str = None,
        year: int = None,
        delay_seconds: int = 0
    ) -> str:
        """Schedule monthly report generation."""
        if delay_seconds > 0:
            task = tasks.generate_monthly_report.apply_async(
                args=[tenant_id, month, year],
                countdown=delay_seconds
            )
        else:
            task = tasks.generate_monthly_report.delay(tenant_id, month, year)
        
        logger.info("Monthly report task scheduled",
                   tenant_id=tenant_id,
                   month=month,
                   year=year,
                   task_id=task.id,
                   delay_seconds=delay_seconds)
        
        return task.id
    
    async def schedule_recurring_task(
        self,
        task_name: str,
        schedule_type: ScheduleType,
        schedule_config: Dict[str, Any],
        task_args: List[Any] = None,
        task_kwargs: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Schedule recurring task."""
        task_args = task_args or []
        task_kwargs = task_kwargs or {}
        
        # Get task function
        task_func = getattr(tasks, task_name, None)
        if not task_func:
            raise ValueError(f"Task {task_name} not found")
        
        # Create schedule based on type
        if schedule_type == ScheduleType.INTERVAL:
            # Interval-based schedule (every N seconds/minutes/hours)
            interval_seconds = schedule_config.get("seconds", 0)
            schedule = interval_seconds
        
        elif schedule_type == ScheduleType.CRON:
            # Cron-based schedule
            schedule = crontab(
                minute=schedule_config.get("minute", "*"),
                hour=schedule_config.get("hour", "*"),
                day_of_week=schedule_config.get("day_of_week", "*"),
                day_of_month=schedule_config.get("day_of_month", "*"),
                month_of_year=schedule_config.get("month_of_year", "*")
            )
        
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
        
        # Add to beat schedule
        schedule_entry = {
            "task": f"src.services.background.tasks.{task_name}",
            "schedule": schedule,
            "args": task_args,
            "kwargs": task_kwargs,
            "options": schedule_config.get("options", {})
        }
        
        # Update Celery beat schedule
        self.celery_app.conf.beat_schedule[f"custom_{task_name}"] = schedule_entry
        
        logger.info("Recurring task scheduled",
                   task_name=task_name,
                   schedule_type=schedule_type.value,
                   schedule_config=schedule_config)
        
        return {
            "task_name": task_name,
            "schedule_type": schedule_type.value,
            "schedule_entry": schedule_entry,
            "scheduled": True
        }
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a scheduled task."""
        try:
            # Use the cancel_task utility function
            result = await tasks.cancel_task(task_id)
            
            logger.info("Task canceled", task_id=task_id)
            return result
            
        except Exception as e:
            logger.error("Failed to cancel task", task_id=task_id, error=str(e))
            return {
                "task_id": task_id,
                "canceled": False,
                "error": str(e)
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a scheduled task."""
        try:
            # Use the check_task_status utility function
            result = await tasks.check_task_status(task_id)
            
            return result
            
        except Exception as e:
            logger.error("Failed to get task status", task_id=task_id, error=str(e))
            return {
                "task_id": task_id,
                "status": "ERROR",
                "error": str(e)
            }
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of active tasks."""
        try:
            inspect = self.celery_app.control.inspect()
            
            # Get active tasks from all workers
            active_tasks = inspect.active()
            
            if not active_tasks:
                return []
            
            # Flatten results from all workers
            all_tasks = []
            for worker, tasks_list in active_tasks.items():
                for task in tasks_list:
                    task_info = {
                        "task_id": task["id"],
                        "task_name": task["name"],
                        "worker": worker,
                        "args": task.get("args", []),
                        "kwargs": task.get("kwargs", {}),
                        "time_start": task.get("time_start"),
                        "acknowledged": task.get("acknowledged", False)
                    }
                    all_tasks.append(task_info)
            
            return all_tasks
            
        except Exception as e:
            logger.error("Failed to get active tasks", error=str(e))
            return []
    
    async def get_scheduled_tasks(self) -> Dict[str, Any]:
        """Get list of scheduled recurring tasks."""
        try:
            # Get beat schedule
            beat_schedule = self.celery_app.conf.beat_schedule
            
            scheduled_tasks = {}
            for task_name, schedule_entry in beat_schedule.items():
                scheduled_tasks[task_name] = {
                    "task": schedule_entry["task"],
                    "schedule": str(schedule_entry["schedule"]),
                    "args": schedule_entry.get("args", []),
                    "kwargs": schedule_entry.get("kwargs", {}),
                    "options": schedule_entry.get("options", {})
                }
            
            return scheduled_tasks
            
        except Exception as e:
            logger.error("Failed to get scheduled tasks", error=str(e))
            return {}
    
    async def get_worker_stats(self) -> Dict[str, Any]:
        """Get Celery worker statistics."""
        try:
            inspect = self.celery_app.control.inspect()
            
            stats = inspect.stats()
            reserved = inspect.reserved()
            active = inspect.active()
            
            worker_stats = {}
            if stats:
                for worker, worker_stats_data in stats.items():
                    worker_stats[worker] = {
                        "stats": worker_stats_data,
                        "reserved_tasks": len(reserved.get(worker, [])) if reserved else 0,
                        "active_tasks": len(active.get(worker, [])) if active else 0
                    }
            
            return worker_stats
            
        except Exception as e:
            logger.error("Failed to get worker stats", error=str(e))
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on task scheduler."""
        health_status = {
            "service": "task_scheduler",
            "status": "healthy",
            "details": {}
        }
        
        try:
            # Check Celery connectivity
            inspect = self.celery_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                active_workers = len(stats)
                health_status["details"]["active_workers"] = active_workers
                health_status["details"]["worker_names"] = list(stats.keys())
            else:
                health_status["status"] = "unhealthy"
                health_status["details"]["error"] = "No active workers found"
            
            # Get active and scheduled task counts
            active_tasks = await self.get_active_tasks()
            scheduled_tasks = await self.get_scheduled_tasks()
            
            health_status["details"]["active_tasks"] = len(active_tasks)
            health_status["details"]["scheduled_tasks"] = len(scheduled_tasks)
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["details"]["error"] = str(e)
            logger.error("Task scheduler health check failed", error=str(e))
        
        return health_status


# Pre-configured scheduling patterns
SCHEDULE_PATTERNS = {
    "every_minute": {"seconds": 60},
    "every_5_minutes": {"seconds": 300},
    "every_15_minutes": {"seconds": 900},
    "every_30_minutes": {"seconds": 1800},
    "every_hour": {"seconds": 3600},
    "every_6_hours": {"seconds": 21600},
    "every_12_hours": {"seconds": 43200},
    "daily_at_midnight": {"hour": 0, "minute": 0},
    "daily_at_6am": {"hour": 6, "minute": 0},
    "daily_at_noon": {"hour": 12, "minute": 0},
    "weekly_sunday": {"hour": 0, "minute": 0, "day_of_week": 0},
    "monthly_first": {"hour": 0, "minute": 0, "day_of_month": 1}
}