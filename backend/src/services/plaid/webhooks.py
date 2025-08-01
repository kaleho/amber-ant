"""Plaid webhook handling service."""

from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone
from enum import Enum

import structlog

from .client import PlaidClient, get_plaid_client
from src.exceptions import PlaidError, ValidationError

logger = structlog.get_logger(__name__)


class PlaidWebhookType(Enum):
    """Plaid webhook types."""
    TRANSACTIONS = "TRANSACTIONS"
    ITEM = "ITEM"
    AUTH = "AUTH"
    IDENTITY = "IDENTITY"
    ASSETS = "ASSETS"
    HOLDINGS = "HOLDINGS"
    LIABILITIES = "LIABILITIES"


class PlaidWebhookCode(Enum):
    """Plaid webhook codes."""
    # Transaction webhooks
    INITIAL_UPDATE = "INITIAL_UPDATE"
    HISTORICAL_UPDATE = "HISTORICAL_UPDATE"
    DEFAULT_UPDATE = "DEFAULT_UPDATE"
    TRANSACTIONS_REMOVED = "TRANSACTIONS_REMOVED"
    
    # Item webhooks
    ERROR = "ERROR"
    NEW_ACCOUNTS_AVAILABLE = "NEW_ACCOUNTS_AVAILABLE"
    PENDING_EXPIRATION = "PENDING_EXPIRATION"
    USER_PERMISSION_REVOKED = "USER_PERMISSION_REVOKED"
    WEBHOOK_UPDATE_ACKNOWLEDGED = "WEBHOOK_UPDATE_ACKNOWLEDGED"


class WebhookService:
    """Service for handling Plaid webhook events."""
    
    def __init__(self, plaid_client: Optional[PlaidClient] = None):
        self.plaid_client = plaid_client or get_plaid_client()
        
        # Event handlers registry
        self.event_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers."""
        # Transaction webhooks
        self.register_handler(
            PlaidWebhookCode.INITIAL_UPDATE.value,
            self._handle_initial_update
        )
        self.register_handler(
            PlaidWebhookCode.HISTORICAL_UPDATE.value,
            self._handle_historical_update
        )
        self.register_handler(
            PlaidWebhookCode.DEFAULT_UPDATE.value,
            self._handle_default_update
        )
        self.register_handler(
            PlaidWebhookCode.TRANSACTIONS_REMOVED.value,
            self._handle_transactions_removed
        )
        
        # Item webhooks
        self.register_handler(
            PlaidWebhookCode.ERROR.value,
            self._handle_error
        )
        self.register_handler(
            PlaidWebhookCode.NEW_ACCOUNTS_AVAILABLE.value,
            self._handle_new_accounts_available
        )
        self.register_handler(
            PlaidWebhookCode.PENDING_EXPIRATION.value,
            self._handle_pending_expiration
        )
        self.register_handler(
            PlaidWebhookCode.USER_PERMISSION_REVOKED.value,
            self._handle_user_permission_revoked
        )
    
    def register_handler(self, webhook_code: str, handler: Callable):
        """Register custom webhook handler."""
        self.event_handlers[webhook_code] = handler
        logger.debug("Plaid webhook handler registered", webhook_code=webhook_code)
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Plaid webhook event."""
        try:
            webhook_type = payload.get("webhook_type")
            webhook_code = payload.get("webhook_code")
            item_id = payload.get("item_id")
            
            logger.info("Plaid webhook event received",
                       webhook_type=webhook_type,
                       webhook_code=webhook_code,
                       item_id=item_id)
            
            # Validate required fields
            if not webhook_type or not webhook_code:
                raise ValidationError("Missing required webhook fields")
            
            # Extract tenant_id from metadata or item_id
            tenant_id = await self._extract_tenant_id(item_id)
            
            # Process event
            result = await self._process_event(payload, tenant_id)
            
            # Acknowledge webhook
            try:
                await self.plaid_client.acknowledge_webhook(webhook_code, webhook_type)
            except Exception as e:
                logger.warning("Failed to acknowledge webhook", error=str(e))
            
            return {
                "webhook_type": webhook_type,
                "webhook_code": webhook_code,
                "item_id": item_id,
                "tenant_id": tenant_id,
                "processed": True,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Plaid webhook processing failed", error=str(e))
            raise PlaidError(f"Webhook processing failed: {str(e)}")
    
    async def _process_event(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Process individual webhook event."""
        webhook_code = payload.get("webhook_code")
        
        # Find and execute handler
        handler = self.event_handlers.get(webhook_code)
        if handler:
            try:
                result = await handler(payload, tenant_id)
                logger.info("Plaid webhook event processed",
                           webhook_code=webhook_code,
                           tenant_id=tenant_id,
                           handler=handler.__name__)
                return result
            except Exception as e:
                logger.error("Plaid webhook handler failed",
                            webhook_code=webhook_code,
                            tenant_id=tenant_id,
                            handler=handler.__name__,
                            error=str(e))
                raise
        else:
            logger.warning("No handler for Plaid webhook", webhook_code=webhook_code)
            return {"status": "no_handler", "webhook_code": webhook_code}
    
    async def _extract_tenant_id(self, item_id: str) -> Optional[str]:
        """Extract tenant_id from item_id by looking up in database."""
        try:
            from src.accounts.repository import AccountRepository
            from src.tenant.context import get_tenant_context
            
            # In a multi-tenant system, we'd need to search across all tenants
            # For now, we'll check if we're in a tenant context
            try:
                tenant_context = get_tenant_context()
                return tenant_context.tenant_id
            except:
                # If no tenant context, we'd need to query across tenant databases
                # This is a more complex operation that would require admin-level access
                return None
                
        except Exception as e:
            logger.error("Failed to extract tenant_id from item_id", 
                        item_id=item_id, error=str(e))
            return None
    
    # Default event handlers
    async def _handle_initial_update(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle initial transaction update webhook."""
        item_id = payload.get("item_id")
        new_transactions = payload.get("new_transactions", 0)
        
        logger.info("Initial transaction update webhook",
                   tenant_id=tenant_id,
                   item_id=item_id,
                   new_transactions=new_transactions)
        
        # Trigger background task to sync transactions
        from src.services.background.tasks import process_transactions
        
        if tenant_id:
            # We would need the access_token for the item_id
            # This would typically be stored in the database
            # For now, we'll log that a sync should be triggered
            logger.info("Should trigger transaction sync for item", 
                       item_id=item_id, tenant_id=tenant_id)
            
            # In a complete implementation:
            # access_token = await get_access_token_for_item(item_id)
            # process_transactions.delay(tenant_id, access_token)
        
        return {
            "action": "initial_update",
            "item_id": item_id,
            "new_transactions": new_transactions,
            "tenant_id": tenant_id
        }
    
    async def _handle_historical_update(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle historical transaction update webhook."""
        item_id = payload.get("item_id")
        new_transactions = payload.get("new_transactions", 0)
        
        logger.info("Historical transaction update webhook",
                   tenant_id=tenant_id,
                   item_id=item_id,
                   new_transactions=new_transactions)
        
        # TODO: Trigger background task to sync historical transactions
        
        return {
            "action": "historical_update",
            "item_id": item_id,
            "new_transactions": new_transactions,
            "tenant_id": tenant_id
        }
    
    async def _handle_default_update(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle default transaction update webhook."""
        item_id = payload.get("item_id")
        new_transactions = payload.get("new_transactions", 0)
        
        logger.info("Default transaction update webhook",
                   tenant_id=tenant_id,
                   item_id=item_id,
                   new_transactions=new_transactions)
        
        # TODO: Trigger background task to sync new transactions
        
        return {
            "action": "default_update",
            "item_id": item_id,
            "new_transactions": new_transactions,
            "tenant_id": tenant_id
        }
    
    async def _handle_transactions_removed(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle transactions removed webhook."""
        item_id = payload.get("item_id")
        removed_transactions = payload.get("removed_transactions", [])
        
        logger.info("Transactions removed webhook",
                   tenant_id=tenant_id,
                   item_id=item_id,
                   removed_count=len(removed_transactions))
        
        # Remove transactions from database
        if tenant_id and removed_transactions:
            try:
                from src.transactions.service import TransactionService
                transaction_service = TransactionService()
                
                for transaction_id in removed_transactions:
                    try:
                        # Find transaction by Plaid ID and mark as deleted
                        transaction = await transaction_service.transaction_repo.get_by_plaid_transaction_id(
                            transaction_id
                        )
                        if transaction:
                            # Soft delete by updating status or hard delete
                            await transaction_service.delete_transaction(
                                transaction_id=transaction.id,
                                user_id=transaction.user_id
                            )
                            logger.info("Removed transaction", 
                                       plaid_transaction_id=transaction_id)
                    except Exception as e:
                        logger.error("Failed to remove transaction", 
                                   plaid_transaction_id=transaction_id, 
                                   error=str(e))
                        
            except Exception as e:
                logger.error("Failed to process removed transactions", error=str(e))
        
        return {
            "action": "transactions_removed",
            "item_id": item_id,
            "removed_transactions": removed_transactions,
            "tenant_id": tenant_id
        }
    
    async def _handle_error(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle item error webhook."""
        item_id = payload.get("item_id")
        error = payload.get("error", {})
        
        logger.error("Plaid item error webhook",
                    tenant_id=tenant_id,
                    item_id=item_id,
                    error_type=error.get("error_type"),
                    error_code=error.get("error_code"),
                    error_message=error.get("error_message"))
        
        # TODO: Handle item error
        # - Notify user about the error
        # - Disable automatic syncing if needed
        # - Provide re-authentication link if required
        
        return {
            "action": "error",
            "item_id": item_id,
            "error": error,
            "tenant_id": tenant_id
        }
    
    async def _handle_new_accounts_available(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle new accounts available webhook."""
        item_id = payload.get("item_id")
        
        logger.info("New accounts available webhook",
                   tenant_id=tenant_id,
                   item_id=item_id)
        
        # TODO: Notify user about new accounts
        # - Send notification about new accounts
        # - Provide option to link new accounts
        
        return {
            "action": "new_accounts_available",
            "item_id": item_id,
            "tenant_id": tenant_id
        }
    
    async def _handle_pending_expiration(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle pending expiration webhook."""
        item_id = payload.get("item_id")
        consent_expiration_time = payload.get("consent_expiration_time")
        
        logger.warning("Item pending expiration webhook",
                      tenant_id=tenant_id,
                      item_id=item_id,
                      expiration_time=consent_expiration_time)
        
        # TODO: Handle pending expiration
        # - Notify user about upcoming expiration
        # - Provide re-authentication link
        # - Schedule reminder notifications
        
        return {
            "action": "pending_expiration",
            "item_id": item_id,
            "consent_expiration_time": consent_expiration_time,
            "tenant_id": tenant_id
        }
    
    async def _handle_user_permission_revoked(
        self,
        payload: Dict[str, Any],
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle user permission revoked webhook."""
        item_id = payload.get("item_id")
        
        logger.warning("User permission revoked webhook",
                      tenant_id=tenant_id,
                      item_id=item_id)
        
        # TODO: Handle permission revocation
        # - Disable item and stop syncing
        # - Notify user about revoked access
        # - Clean up associated data if required
        
        return {
            "action": "user_permission_revoked",
            "item_id": item_id,
            "tenant_id": tenant_id
        }
    
    def get_supported_events(self) -> Dict[str, list]:
        """Get list of supported webhook events by type."""
        return {
            "transaction_events": [
                PlaidWebhookCode.INITIAL_UPDATE.value,
                PlaidWebhookCode.HISTORICAL_UPDATE.value,
                PlaidWebhookCode.DEFAULT_UPDATE.value,
                PlaidWebhookCode.TRANSACTIONS_REMOVED.value,
            ],
            "item_events": [
                PlaidWebhookCode.ERROR.value,
                PlaidWebhookCode.NEW_ACCOUNTS_AVAILABLE.value,
                PlaidWebhookCode.PENDING_EXPIRATION.value,
                PlaidWebhookCode.USER_PERMISSION_REVOKED.value,
            ]
        }
    
    async def validate_webhook_configuration(self) -> Dict[str, Any]:
        """Validate webhook configuration."""
        validation_result = {
            "valid": True,
            "details": {},
            "errors": []
        }
        
        # Check registered handlers
        validation_result["details"]["registered_handlers"] = len(self.event_handlers)
        validation_result["details"]["supported_events"] = self.get_supported_events()
        
        # Check Plaid client configuration
        try:
            health_check = await self.plaid_client.health_check()
            validation_result["details"]["plaid_connectivity"] = health_check["status"]
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Plaid connectivity failed: {str(e)}")
        
        return validation_result