"""Background task definitions using Celery."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

import structlog
from celery import current_task
from celery.exceptions import Retry

from .celery_app import (
    celery_app,
    tenant_task,
    external_api_task,
    notification_task,
    maintenance_task
)

logger = structlog.get_logger(__name__)


# Account synchronization tasks
@external_api_task()
def sync_account_data(self, tenant_id: str, access_token: str, account_id: str = None):
    """Sync account data from Plaid."""
    try:
        logger.info("Starting account data sync",
                   tenant_id=tenant_id,
                   account_id=account_id,
                   task_id=self.request.id)
        
        # Import here to avoid circular dependencies
        from src.services.plaid import get_plaid_client
        from src.services.redis.cache import get_cache_service
        from src.accounts.service import AccountService
        from src.accounts.schemas import AccountCreate, AccountBalanceUpdate
        
        # Get services
        plaid_client = get_plaid_client()
        cache_service = await get_cache_service()
        account_service = AccountService()
        
        # Sync in async context
        async def _sync_data():
            try:
                # Get account data
                accounts_response = await plaid_client.get_account_balances(access_token)
                accounts = accounts_response["accounts"]
                
                # Filter to specific account if provided
                if account_id:
                    accounts = [acc for acc in accounts if acc["account_id"] == account_id]
                
                synced_accounts = []
                for account in accounts:
                    try:
                        # Find existing account by Plaid ID
                        existing_account = await account_service.account_repo.get_by_plaid_account_id(
                            account['account_id']
                        )
                        
                        if existing_account:
                            # Update existing account balance
                            balance_update = AccountBalanceUpdate(
                                current_balance=Decimal(str(account["balances"]["current"] or 0)),
                                available_balance=Decimal(str(account["balances"]["available"] or 0)) if account["balances"]["available"] else None,
                                balance_date=datetime.utcnow()
                            )
                            
                            # Get user_id from existing account to update
                            updated_account = await account_service.update_account_balance(
                                account_id=existing_account.id,
                                user_id=existing_account.user_id,
                                balance_data=balance_update
                            )
                            
                            if updated_account:
                                synced_accounts.append({
                                    "account_id": account["account_id"],
                                    "name": account["name"],
                                    "type": account["type"],
                                    "subtype": account["subtype"],
                                    "balance": {
                                        "available": account["balances"]["available"],
                                        "current": account["balances"]["current"],
                                        "limit": account["balances"]["limit"]
                                    },
                                    "status": "updated"
                                })
                        else:
                            logger.warning("Account not found for Plaid ID", 
                                         plaid_account_id=account['account_id'])
                            
                        # Cache account data
                        cache_key = f"account:{account['account_id']}"
                        await cache_service.set(tenant_id, cache_key, account, ttl=1800)
                        
                    except Exception as e:
                        logger.error("Failed to sync individual account",
                                    account_id=account['account_id'],
                                    error=str(e))
                
                logger.info("Account data sync completed",
                           tenant_id=tenant_id,
                           accounts_synced=len(synced_accounts),
                           task_id=self.request.id)
                
                return {
                    "status": "success",
                    "accounts_synced": len(synced_accounts),
                    "accounts": synced_accounts,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error("Account data sync failed",
                            tenant_id=tenant_id,
                            error=str(e),
                            task_id=self.request.id)
                raise
        
        # Run async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_sync_data())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Sync account data task failed",
                    tenant_id=tenant_id,
                    error=str(e),
                    task_id=self.request.id)
        raise self.retry(countdown=300, max_retries=5)


@external_api_task()
def process_transactions(
    self,
    tenant_id: str,
    access_token: str,
    start_date: str = None,
    end_date: str = None,
    account_ids: List[str] = None
):
    """Process and categorize transactions from Plaid."""
    try:
        logger.info("Starting transaction processing",
                   tenant_id=tenant_id,
                   start_date=start_date,
                   end_date=end_date,
                   task_id=self.request.id)
        
        from src.services.plaid import get_plaid_client
        from src.services.redis.cache import get_cache_service
        from src.transactions.service import TransactionService
        from src.transactions.schemas import TransactionCreate
        
        plaid_client = get_plaid_client()
        cache_service = await get_cache_service()
        transaction_service = TransactionService()
        
        async def _process_transactions():
            try:
                # Set date range (default to last 30 days)
                if not start_date:
                    start_dt = datetime.utcnow() - timedelta(days=30)
                else:
                    start_dt = datetime.fromisoformat(start_date)
                
                if not end_date:
                    end_dt = datetime.utcnow()
                else:
                    end_dt = datetime.fromisoformat(end_date)
                
                # Get transactions
                transactions_response = await plaid_client.get_transactions(
                    access_token=access_token,
                    start_date=start_dt,
                    end_date=end_dt,
                    account_ids=account_ids,
                    count=500  # Max per request
                )
                
                transactions = transactions_response["transactions"]
                processed_transactions = []
                
                for transaction in transactions:
                    try:
                        # Check if transaction already exists
                        existing_transaction = await transaction_service.transaction_repo.get_by_plaid_transaction_id(
                            transaction["transaction_id"]
                        )
                        
                        if not existing_transaction:
                            # Find the account for this transaction
                            account = await transaction_service.account_repo.get_by_plaid_account_id(
                                transaction["account_id"]
                            )
                            
                            if account:
                                # Create new transaction
                                transaction_data = TransactionCreate(
                                    account_id=account.id,
                                    plaid_transaction_id=transaction["transaction_id"],
                                    amount=Decimal(str(transaction["amount"])),
                                    date=datetime.strptime(transaction["date"], "%Y-%m-%d").date(),
                                    description=transaction["name"],
                                    merchant_name=transaction.get("merchant_name"),
                                    category=transaction["category"][0] if transaction.get("category") else None,
                                    subcategory=transaction["category"][1] if transaction.get("category") and len(transaction["category"]) > 1 else None,
                                    is_pending=transaction.get("pending", False),
                                    type="debit" if transaction["amount"] < 0 else "credit"
                                )
                                
                                created_transaction = await transaction_service.create_transaction(
                                    user_id=account.user_id,
                                    transaction_data=transaction_data
                                )
                                
                                if created_transaction:
                                    processed_transactions.append({
                                        "transaction_id": transaction["transaction_id"],
                                        "account_id": transaction["account_id"],
                                        "amount": float(transaction["amount"]),
                                        "date": transaction["date"],
                                        "name": transaction["name"],
                                        "merchant_name": transaction.get("merchant_name"),
                                        "category": transaction["category"],
                                        "status": "created"
                                    })
                            else:
                                logger.warning("Account not found for transaction",
                                             plaid_account_id=transaction["account_id"])
                        else:
                            # Transaction already exists, possibly update if pending status changed
                            if existing_transaction.is_pending != transaction.get("pending", False):
                                # Update pending status
                                from src.transactions.schemas import TransactionUpdate
                                update_data = TransactionUpdate(is_pending=transaction.get("pending", False))
                                await transaction_service.update_transaction(
                                    transaction_id=existing_transaction.id,
                                    user_id=existing_transaction.user_id,
                                    transaction_data=update_data
                                )
                            
                            processed_transactions.append({
                                "transaction_id": transaction["transaction_id"],
                                "status": "updated"
                            })
                        
                        # Cache transaction
                        cache_key = f"transaction:{transaction['transaction_id']}"
                        await cache_service.set(tenant_id, cache_key, transaction, ttl=3600)
                        
                    except Exception as e:
                        logger.error("Failed to process individual transaction",
                                    transaction_id=transaction["transaction_id"],
                                    error=str(e))
                
                logger.info("Transaction processing completed",
                           tenant_id=tenant_id,
                           transactions_processed=len(processed_transactions),
                           task_id=self.request.id)
                
                return {
                    "status": "success",
                    "transactions_processed": len(processed_transactions),
                    "date_range": {
                        "start": start_dt.isoformat(),
                        "end": end_dt.isoformat()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error("Transaction processing failed",
                            tenant_id=tenant_id,
                            error=str(e),
                            task_id=self.request.id)
                raise
        
        # Run async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_process_transactions())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Process transactions task failed",
                    tenant_id=tenant_id,
                    error=str(e),
                    task_id=self.request.id)
        raise self.retry(countdown=300, max_retries=3)


@notification_task()
def send_notification_email(
    self,
    tenant_id: str,
    user_email: str,
    template: str,
    subject: str,
    data: Dict[str, Any] = None
):
    """Send notification email to user."""
    try:
        logger.info("Sending notification email",
                   tenant_id=tenant_id,
                   user_email=user_email,
                   template=template,
                   task_id=self.request.id)
        
        from src.services.email.client import get_email_service
        
        async def _send_email():
            try:
                email_service = await get_email_service()
                
                # Send template email
                success = await email_service.send_template_email(
                    to=user_email,
                    template_name=template,
                    template_data=data or {},
                    subject=subject
                )
                
                if success:
                    logger.info("Email sent successfully",
                               tenant_id=tenant_id,
                               user_email=user_email,
                               template=template,
                               subject=subject)
                    return True
                else:
                    raise Exception("Email service returned failure")
                    
            except Exception as e:
                logger.error("Email sending failed",
                            tenant_id=tenant_id,
                            user_email=user_email,
                            template=template,
                            error=str(e))
                raise
        
        # Run async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(_send_email())
        loop.close()
        
        if not success:
            raise Exception("Email sending failed")
        
        return {
            "status": "success",
            "email_sent": True,
            "recipient": user_email,
            "template": template,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Send notification email task failed",
                    tenant_id=tenant_id,
                    user_email=user_email,
                    error=str(e),
                    task_id=self.request.id)
        raise self.retry(countdown=60, max_retries=3)


@tenant_task()
def generate_monthly_report(self, tenant_id: str, month: str = None, year: int = None):
    """Generate monthly financial report for tenant."""
    try:
        # Default to current month if not specified
        if not month or not year:
            now = datetime.utcnow()
            month = month or now.strftime("%m")
            year = year or now.year
        
        logger.info("Generating monthly report",
                   tenant_id=tenant_id,
                   month=month,
                   year=year,
                   task_id=self.request.id)
        
        # TODO: Generate report
        # This would involve:
        # 1. Query transactions for the month
        # 2. Calculate spending by category
        # 3. Compare against budgets
        # 4. Generate insights and trends
        # 5. Create PDF/HTML report
        # 6. Store report and notify user
        
        report_data = {
            "tenant_id": tenant_id,
            "period": f"{year}-{month}",
            "total_income": 0.0,
            "total_expenses": 0.0,
            "categories": {},
            "budget_comparison": {},
            "savings_rate": 0.0,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Monthly report generated",
                   tenant_id=tenant_id,
                   period=f"{year}-{month}",
                   task_id=self.request.id)
        
        # Schedule email notification
        send_notification_email.delay(
            tenant_id=tenant_id,
            user_email="user@example.com",  # TODO: Get from tenant data
            template="monthly_report",
            subject=f"Your Monthly Financial Report - {month}/{year}",
            data=report_data
        )
        
        return {
            "status": "success",
            "report_generated": True,
            "period": f"{year}-{month}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Generate monthly report task failed",
                    tenant_id=tenant_id,
                    error=str(e),
                    task_id=self.request.id)
        raise self.retry(countdown=60, max_retries=2)


@maintenance_task()
def cleanup_expired_sessions(self):
    """Clean up expired sessions from Redis."""
    try:
        logger.info("Starting expired session cleanup", task_id=self.request.id)
        
        from src.services.redis.session import get_session_service
        
        async def _cleanup_sessions():
            session_service = await get_session_service()
            cleaned_count = await session_service.cleanup_expired_sessions()
            return cleaned_count
        
        # Run async code
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            cleaned_count = loop.run_until_complete(_cleanup_sessions())
        finally:
            loop.close()
        
        logger.info("Expired session cleanup completed",
                   cleaned_count=cleaned_count,
                   task_id=self.request.id)
        
        return {
            "status": "success",
            "sessions_cleaned": cleaned_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Cleanup expired sessions task failed",
                    error=str(e),
                    task_id=self.request.id)
        raise self.retry(countdown=300, max_retries=2)


# Composite tasks (tasks that orchestrate other tasks)
@tenant_task()
def sync_all_accounts(self, tenant_id: str):
    """Sync all accounts for a tenant."""
    try:
        logger.info("Starting full account sync",
                   tenant_id=tenant_id,
                   task_id=self.request.id)
        
        # TODO: Get all access tokens for tenant
        # This would query the database for all connected accounts
        access_tokens = ["access_token_1", "access_token_2"]  # Placeholder
        
        sync_tasks = []
        for access_token in access_tokens:
            # Schedule sync task for each account
            task = sync_account_data.delay(tenant_id, access_token)
            sync_tasks.append(task.id)
        
        logger.info("Account sync tasks scheduled",
                   tenant_id=tenant_id,
                   task_count=len(sync_tasks),
                   task_ids=sync_tasks,
                   task_id=self.request.id)
        
        return {
            "status": "success",
            "sync_tasks_scheduled": len(sync_tasks),
            "task_ids": sync_tasks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Sync all accounts task failed",
                    tenant_id=tenant_id,
                    error=str(e),
                    task_id=self.request.id)
        raise self.retry(countdown=60, max_retries=2)


@maintenance_task()
def generate_daily_reports(self):
    """Generate daily reports for all active tenants."""
    try:
        logger.info("Starting daily report generation", task_id=self.request.id)
        
        # TODO: Get all active tenants
        # This would query the database for tenants that need daily reports
        active_tenants = ["tenant_1", "tenant_2"]  # Placeholder
        
        report_tasks = []
        for tenant_id in active_tenants:
            # Schedule monthly report generation
            task = generate_monthly_report.delay(tenant_id)
            report_tasks.append(task.id)
        
        logger.info("Daily report tasks scheduled",
                   task_count=len(report_tasks),
                   task_ids=report_tasks,
                   task_id=self.request.id)
        
        return {
            "status": "success",
            "report_tasks_scheduled": len(report_tasks),
            "task_ids": report_tasks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Generate daily reports task failed",
                    error=str(e),
                    task_id=self.request.id)
        raise self.retry(countdown=300, max_retries=2)


# Utility tasks
@celery_app.task(bind=True)
def check_task_status(self, task_id: str):
    """Check status of a task by ID."""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "successful": result.successful(),
            "failed": result.failed(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Check task status failed",
                    task_id=task_id,
                    error=str(e))
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True)
def cancel_task(self, task_id: str):
    """Cancel a task by ID."""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        
        logger.info("Task canceled", task_id=task_id)
        
        return {
            "task_id": task_id,
            "canceled": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Cancel task failed",
                    task_id=task_id,
                    error=str(e))
        return {
            "task_id": task_id,
            "canceled": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }