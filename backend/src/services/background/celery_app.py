"""Celery application configuration for background tasks."""

import os
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    
    app = Celery(
        "faithful_finances_tasks",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "src.services.background.tasks",
        ]
    )
    
    # Configure Celery
    app.conf.update(
        # Task settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        
        # Task routing
        task_routes={
            "src.services.background.tasks.sync_account_data": {"queue": "high_priority"},
            "src.services.background.tasks.process_transactions": {"queue": "medium_priority"},
            "src.services.background.tasks.send_notification_email": {"queue": "notifications"},
            "src.services.background.tasks.generate_monthly_report": {"queue": "reports"},
            "src.services.background.tasks.cleanup_expired_sessions": {"queue": "maintenance"},
        },
        
        # Task execution settings
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_time_limit=300,  # 5 minutes
        task_soft_time_limit=240,  # 4 minutes
        
        # Worker settings
        worker_max_tasks_per_child=1000,
        worker_prefetch_multiplier=1,
        worker_max_memory_per_child=200000,  # 200MB
        
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_backend_transport_options={
            "master_name": "mymaster",
            "retry_on_timeout": True,
        },
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Error handling
        task_annotations={
            "*": {
                "rate_limit": "100/m",  # 100 tasks per minute per worker
                "retry_policy": {
                    "max_retries": 3,
                    "interval_start": 0,
                    "interval_step": 2,
                    "interval_max": 30,
                }
            },
            "src.services.background.tasks.sync_account_data": {
                "rate_limit": "10/m",  # More conservative for external API calls
                "retry_policy": {
                    "max_retries": 5,
                    "interval_start": 5,
                    "interval_step": 5,
                    "interval_max": 60,
                }
            },
        },
        
        # Beat schedule (for periodic tasks)
        beat_schedule={
            "sync-all-accounts": {
                "task": "src.services.background.tasks.sync_all_accounts",
                "schedule": 1800.0,  # Every 30 minutes
                "options": {"queue": "high_priority"}
            },
            "cleanup-expired-sessions": {
                "task": "src.services.background.tasks.cleanup_expired_sessions",
                "schedule": 3600.0,  # Every hour
                "options": {"queue": "maintenance"}
            },
            "generate-daily-reports": {
                "task": "src.services.background.tasks.generate_daily_reports",
                "schedule": 86400.0,  # Every day
                "options": {"queue": "reports"}
            },
        },
    )
    
    # Set up task discovery
    app.autodiscover_tasks()
    
    return app


# Create the Celery app instance
celery_app = create_celery_app()


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    logger.info("Celery worker ready", worker=sender.hostname)


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown signal."""
    logger.info("Celery worker shutting down", worker=sender.hostname)


def get_celery_app() -> Celery:
    """Get Celery application instance."""
    return celery_app


# Task decorators for common patterns
def tenant_task(bind=True, **options):
    """Decorator for tasks that operate on tenant data."""
    default_options = {
        "bind": True,
        "autoretry_for": (Exception,),
        "retry_kwargs": {"max_retries": 3, "countdown": 60},
        "retry_backoff": True,
        "retry_jitter": True,
    }
    default_options.update(options)
    
    return celery_app.task(**default_options)


def external_api_task(bind=True, **options):
    """Decorator for tasks that call external APIs."""
    default_options = {
        "bind": True,
        "autoretry_for": (Exception,),
        "retry_kwargs": {"max_retries": 5, "countdown": 300},  # 5 minute delay
        "retry_backoff": True,
        "retry_jitter": True,
        "rate_limit": "10/m",  # Conservative rate limiting
    }
    default_options.update(options)
    
    return celery_app.task(**default_options)


def notification_task(bind=True, **options):
    """Decorator for notification tasks."""
    default_options = {
        "bind": True,
        "autoretry_for": (Exception,),
        "retry_kwargs": {"max_retries": 3, "countdown": 30},
        "queue": "notifications",
    }
    default_options.update(options)
    
    return celery_app.task(**default_options)


def maintenance_task(bind=True, **options):
    """Decorator for maintenance tasks."""
    default_options = {
        "bind": True,
        "autoretry_for": (Exception,),
        "retry_kwargs": {"max_retries": 2, "countdown": 60},
        "queue": "maintenance",
    }
    default_options.update(options)
    
    return celery_app.task(**default_options)


# Health check task
@celery_app.task(bind=True)
def health_check_task(self):
    """Simple health check task."""
    logger.info("Health check task executed", task_id=self.request.id)
    return {
        "status": "healthy",
        "task_id": self.request.id,
        "worker": self.request.hostname,
        "timestamp": self.request.get("timestamp"),
    }


if __name__ == "__main__":
    # Allow running celery app directly
    celery_app.start()