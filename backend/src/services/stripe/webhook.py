"""Stripe webhook handling service."""

import json
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone
from enum import Enum

import stripe
import structlog

from .client import StripeClient, get_stripe_client
from src.exceptions import StripeError, ValidationError
from src.config import settings

logger = structlog.get_logger(__name__)


class WebhookEventType(Enum):
    """Stripe webhook event types we handle."""
    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    
    # Subscription events
    CUSTOMER_SUBSCRIPTION_CREATED = "customer.subscription.created"
    CUSTOMER_SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    CUSTOMER_SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    CUSTOMER_SUBSCRIPTION_TRIAL_WILL_END = "customer.subscription.trial_will_end"
    
    # Invoice events
    INVOICE_CREATED = "invoice.created"
    INVOICE_FINALIZED = "invoice.finalized"
    INVOICE_PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    INVOICE_UPCOMING = "invoice.upcoming"
    
    # Payment events
    PAYMENT_INTENT_CREATED = "payment_intent.created"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_INTENT_PAYMENT_FAILED = "payment_intent.payment_failed"
    
    # Setup events
    SETUP_INTENT_SUCCEEDED = "setup_intent.succeeded"
    SETUP_INTENT_SETUP_FAILED = "setup_intent.setup_failed"
    
    # Payment method events
    PAYMENT_METHOD_ATTACHED = "payment_method.attached"
    PAYMENT_METHOD_DETACHED = "payment_method.detached"


class WebhookService:
    """Service for handling Stripe webhook events."""
    
    def __init__(self, stripe_client: Optional[StripeClient] = None):
        self.stripe_client = stripe_client or get_stripe_client()
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        
        # Event handlers registry
        self.event_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers."""
        # Subscription events
        self.register_handler(
            WebhookEventType.CUSTOMER_SUBSCRIPTION_CREATED.value,
            self._handle_subscription_created
        )
        self.register_handler(
            WebhookEventType.CUSTOMER_SUBSCRIPTION_UPDATED.value,
            self._handle_subscription_updated
        )
        self.register_handler(
            WebhookEventType.CUSTOMER_SUBSCRIPTION_DELETED.value,
            self._handle_subscription_deleted
        )
        self.register_handler(
            WebhookEventType.CUSTOMER_SUBSCRIPTION_TRIAL_WILL_END.value,
            self._handle_subscription_trial_ending
        )
        
        # Invoice events
        self.register_handler(
            WebhookEventType.INVOICE_PAYMENT_SUCCEEDED.value,
            self._handle_invoice_payment_succeeded
        )
        self.register_handler(
            WebhookEventType.INVOICE_PAYMENT_FAILED.value,
            self._handle_invoice_payment_failed
        )
        
        # Payment events
        self.register_handler(
            WebhookEventType.PAYMENT_INTENT_SUCCEEDED.value,
            self._handle_payment_succeeded
        )
        self.register_handler(
            WebhookEventType.PAYMENT_INTENT_PAYMENT_FAILED.value,
            self._handle_payment_failed
        )
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register custom event handler."""
        self.event_handlers[event_type] = handler
        logger.debug("Webhook handler registered", event_type=event_type)
    
    async def process_webhook(
        self,
        payload: bytes,
        signature_header: str
    ) -> Dict[str, Any]:
        """Process incoming webhook event."""
        try:
            # Verify webhook signature
            event = self.stripe_client.construct_event(
                payload, signature_header, self.webhook_secret
            )
            
            event_type = event["type"]
            event_data = event["data"]["object"]
            
            logger.info("Webhook event received",
                       event_id=event["id"],
                       event_type=event_type,
                       created=event["created"])
            
            # Process event
            result = await self._process_event(event)
            
            return {
                "event_id": event["id"],
                "event_type": event_type,
                "processed": True,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except stripe.error.SignatureVerificationError as e:
            logger.error("Webhook signature verification failed", error=str(e))
            raise StripeError(f"Invalid webhook signature: {str(e)}")
        
        except Exception as e:
            logger.error("Webhook processing failed", error=str(e))
            raise StripeError(f"Webhook processing failed: {str(e)}")
    
    async def _process_event(self, event: stripe.Event) -> Dict[str, Any]:
        """Process individual webhook event."""
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        # Get tenant_id from event metadata
        tenant_id = self._extract_tenant_id(event_data)
        
        # Find and execute handler
        handler = self.event_handlers.get(event_type)
        if handler:
            try:
                result = await handler(event, tenant_id)
                logger.info("Webhook event processed",
                           event_type=event_type,
                           tenant_id=tenant_id,
                           handler=handler.__name__)
                return result
            except Exception as e:
                logger.error("Webhook handler failed",
                            event_type=event_type,
                            tenant_id=tenant_id,
                            handler=handler.__name__,
                            error=str(e))
                raise
        else:
            logger.warning("No handler for webhook event", event_type=event_type)
            return {"status": "no_handler", "event_type": event_type}
    
    def _extract_tenant_id(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Extract tenant_id from event data metadata."""
        # Try to get tenant_id from various places in event data
        if hasattr(event_data, 'metadata') and event_data.metadata:
            return event_data.metadata.get("tenant_id")
        
        # For invoice events, try to get from subscription
        if hasattr(event_data, 'subscription') and event_data.subscription:
            try:
                subscription = stripe.Subscription.retrieve(event_data.subscription)
                return subscription.metadata.get("tenant_id")
            except:
                pass
        
        # For customer events, try to get from customer
        if hasattr(event_data, 'customer') and event_data.customer:
            try:
                customer = stripe.Customer.retrieve(event_data.customer)
                return customer.metadata.get("tenant_id")
            except:
                pass
        
        return None
    
    # Default event handlers
    async def _handle_subscription_created(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle subscription creation."""
        subscription = event["data"]["object"]
        
        logger.info("Subscription created webhook",
                   tenant_id=tenant_id,
                   subscription_id=subscription["id"],
                   status=subscription["status"])
        
        # Update local database with subscription details
        if tenant_id:
            try:
                from src.subscriptions.service import SubscriptionService
                from src.subscriptions.schemas import SubscriptionUpdate
                
                subscription_service = SubscriptionService()
                
                # Update subscription in database
                subscription_update = SubscriptionUpdate(
                    stripe_subscription_id=subscription["id"],
                    status=subscription["status"],
                    current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                    current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                    updated_at=datetime.utcnow()
                )
                
                # Find subscription by stripe_customer_id or create new one
                # This would require looking up tenant/user by metadata
                logger.info("Subscription data should be updated in database",
                           tenant_id=tenant_id,
                           subscription_id=subscription["id"])
                           
            except Exception as e:
                logger.error("Failed to update subscription in database", 
                           error=str(e), tenant_id=tenant_id)
        
        return {
            "action": "subscription_created",
            "subscription_id": subscription["id"],
            "status": subscription["status"],
            "tenant_id": tenant_id
        }
    
    async def _handle_subscription_updated(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle subscription updates."""
        subscription = event["data"]["object"]
        previous_attributes = event["data"].get("previous_attributes", {})
        
        logger.info("Subscription updated webhook",
                   tenant_id=tenant_id,
                   subscription_id=subscription["id"],
                   status=subscription["status"],
                   changes=list(previous_attributes.keys()))
        
        # TODO: Update local database
        # Handle changes like:
        # - Status changes (active -> past_due -> canceled)
        # - Plan changes
        # - Quantity changes
        
        return {
            "action": "subscription_updated",
            "subscription_id": subscription["id"],
            "status": subscription["status"],
            "changes": previous_attributes,
            "tenant_id": tenant_id
        }
    
    async def _handle_subscription_deleted(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        subscription = event["data"]["object"]
        
        logger.info("Subscription deleted webhook",
                   tenant_id=tenant_id,
                   subscription_id=subscription["id"])
        
        # Handle subscription cancellation
        if tenant_id:
            try:
                from src.subscriptions.service import SubscriptionService
                from src.subscriptions.schemas import SubscriptionUpdate
                
                subscription_service = SubscriptionService()
                
                # Update subscription status to cancelled
                subscription_update = SubscriptionUpdate(
                    status="cancelled",
                    cancelled_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                logger.info("Subscription should be cancelled in database",
                           tenant_id=tenant_id,
                           subscription_id=subscription["id"])
                           
                # TODO: Trigger background task to:
                # - Downgrade tenant features
                # - Send cancellation confirmation email
                # - Schedule data retention cleanup
                           
            except Exception as e:
                logger.error("Failed to handle subscription cancellation", 
                           error=str(e), tenant_id=tenant_id)
        
        return {
            "action": "subscription_deleted",
            "subscription_id": subscription["id"],
            "tenant_id": tenant_id
        }
    
    async def _handle_subscription_trial_ending(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle trial ending notification."""
        subscription = event["data"]["object"]
        
        logger.info("Subscription trial ending webhook",
                   tenant_id=tenant_id,
                   subscription_id=subscription["id"],
                   trial_end=subscription["trial_end"])
        
        # TODO: Send trial ending notification
        # - Email customer about trial ending
        # - Prompt for payment method if none on file
        
        return {
            "action": "trial_ending",
            "subscription_id": subscription["id"],
            "trial_end": subscription["trial_end"],
            "tenant_id": tenant_id
        }
    
    async def _handle_invoice_payment_succeeded(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle successful payment."""
        invoice = event["data"]["object"]
        
        logger.info("Invoice payment succeeded webhook",
                   tenant_id=tenant_id,
                   invoice_id=invoice["id"],
                   amount=invoice["amount_paid"],
                   currency=invoice["currency"])
        
        # Handle successful payment
        if tenant_id:
            try:
                # Log payment success for now
                logger.info("Payment succeeded - should update payment history",
                           tenant_id=tenant_id,
                           invoice_id=invoice["id"],
                           amount=invoice["amount_paid"])
                
                # TODO: In complete implementation:
                # 1. Create payment record in database
                # 2. Send payment confirmation email
                # 3. Ensure subscription services are active
                # 4. Update billing history
                
                # Trigger notification email
                from src.services.background.tasks import send_notification_email
                
                # send_notification_email.delay(
                #     tenant_id=tenant_id,
                #     user_email="user@example.com",  # Get from tenant data
                #     template="payment_success",
                #     subject="Payment Confirmation",
                #     data={
                #         "amount": invoice["amount_paid"] / 100,  # Convert from cents
                #         "currency": invoice["currency"].upper(),
                #         "invoice_id": invoice["id"]
                #     }
                # )
                           
            except Exception as e:
                logger.error("Failed to handle successful payment", 
                           error=str(e), tenant_id=tenant_id)
        
        return {
            "action": "payment_succeeded",
            "invoice_id": invoice["id"],
            "amount": invoice["amount_paid"],
            "currency": invoice["currency"],
            "tenant_id": tenant_id
        }
    
    async def _handle_invoice_payment_failed(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle failed payment."""
        invoice = event["data"]["object"]
        
        logger.warning("Invoice payment failed webhook",
                      tenant_id=tenant_id,
                      invoice_id=invoice["id"],
                      amount=invoice["amount_due"],
                      currency=invoice["currency"])
        
        # TODO: Handle payment failure
        # - Send payment failure notification
        # - Provide retry payment link
        # - Consider service suspension after multiple failures
        
        return {
            "action": "payment_failed",
            "invoice_id": invoice["id"],
            "amount_due": invoice["amount_due"],
            "currency": invoice["currency"],
            "tenant_id": tenant_id
        }
    
    async def _handle_payment_succeeded(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle successful payment intent."""
        payment_intent = event["data"]["object"]
        
        logger.info("Payment intent succeeded webhook",
                   tenant_id=tenant_id,
                   payment_intent_id=payment_intent["id"],
                   amount=payment_intent["amount"],
                   currency=payment_intent["currency"])
        
        return {
            "action": "payment_intent_succeeded",
            "payment_intent_id": payment_intent["id"],
            "amount": payment_intent["amount"],
            "currency": payment_intent["currency"],
            "tenant_id": tenant_id
        }
    
    async def _handle_payment_failed(
        self,
        event: stripe.Event,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle failed payment intent."""
        payment_intent = event["data"]["object"]
        
        logger.warning("Payment intent failed webhook",
                      tenant_id=tenant_id,
                      payment_intent_id=payment_intent["id"],
                      amount=payment_intent["amount"],
                      currency=payment_intent["currency"])
        
        return {
            "action": "payment_intent_failed",
            "payment_intent_id": payment_intent["id"],
            "amount": payment_intent["amount"],
            "currency": payment_intent["currency"],
            "tenant_id": tenant_id
        }
    
    async def handle_test_event(self, event_type: str) -> Dict[str, Any]:
        """Handle test webhook events for development."""
        logger.info("Test webhook event received", event_type=event_type)
        
        return {
            "action": "test_event",
            "event_type": event_type,
            "message": "Test event processed successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_supported_events(self) -> List[str]:
        """Get list of supported webhook events."""
        return list(self.event_handlers.keys())
    
    async def validate_webhook_configuration(self) -> Dict[str, Any]:
        """Validate webhook configuration."""
        validation_result = {
            "valid": True,
            "details": {},
            "errors": []
        }
        
        # Check webhook secret
        if not self.webhook_secret:
            validation_result["valid"] = False
            validation_result["errors"].append("STRIPE_WEBHOOK_SECRET not configured")
        else:
            validation_result["details"]["webhook_secret_configured"] = True
        
        # Check registered handlers
        validation_result["details"]["registered_handlers"] = len(self.event_handlers)
        validation_result["details"]["supported_events"] = self.get_supported_events()
        
        return validation_result