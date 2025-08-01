"""Stripe API client with error handling and retry logic."""

import asyncio
from typing import Dict, Any, Optional, List
import time
from datetime import datetime

import stripe
import structlog

from src.config import settings
from src.exceptions import StripeError

logger = structlog.get_logger(__name__)


class StripeClient:
    """Enhanced Stripe API client with error handling, retries, and monitoring."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key
        stripe.api_version = "2023-10-16"  # Pin API version for consistency
        
        # Configure request options
        self.default_request_options = {
            "timeout": 30,
            "max_network_retries": 3
        }
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_remaining = 100
    
    async def _handle_rate_limiting(self):
        """Handle Stripe rate limiting."""
        current_time = time.time()
        
        # Reset counter every second
        if current_time - self.last_request_time >= 1:
            self.request_count = 0
            self.last_request_time = current_time
        
        # If we're approaching rate limits, add delay
        if self.request_count >= 25:  # Conservative limit
            await asyncio.sleep(0.1)
        
        self.request_count += 1
    
    def _handle_stripe_error(self, e: stripe.error.StripeError, operation: str) -> None:
        """Handle and log Stripe API errors."""
        error_details = {
            "operation": operation,
            "type": type(e).__name__,
            "message": str(e),
            "user_message": getattr(e, "user_message", None),
            "code": getattr(e, "code", None),
            "decline_code": getattr(e, "decline_code", None),
            "param": getattr(e, "param", None),
            "request_id": getattr(e, "request_id", None)
        }
        
        logger.error("Stripe API error", **error_details)
        
        # Map Stripe errors to our custom errors
        if isinstance(e, stripe.error.CardError):
            raise StripeError(f"Card error: {e.user_message or str(e)}", error_details)
        elif isinstance(e, stripe.error.RateLimitError):
            raise StripeError("Rate limit exceeded, please try again later", error_details)
        elif isinstance(e, stripe.error.InvalidRequestError):
            raise StripeError(f"Invalid request: {str(e)}", error_details)
        elif isinstance(e, stripe.error.AuthenticationError):
            raise StripeError("Authentication failed", error_details)
        elif isinstance(e, stripe.error.APIConnectionError):
            raise StripeError("Network error, please try again", error_details)
        elif isinstance(e, stripe.error.StripeError):
            raise StripeError(f"Stripe error: {str(e)}", error_details)
        else:
            raise StripeError(f"Unknown Stripe error: {str(e)}", error_details)
    
    async def _make_request(self, operation: str, func, *args, **kwargs):
        """Make Stripe API request with error handling and rate limiting."""
        await self._handle_rate_limiting()
        
        # Add default request options
        if "request_options" not in kwargs:
            kwargs["request_options"] = self.default_request_options.copy()
        
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            response_time = (time.time() - start_time) * 1000
            
            logger.debug(
                "Stripe API request successful",
                operation=operation,
                response_time_ms=round(response_time, 2)
            )
            
            return result
            
        except stripe.error.StripeError as e:
            self._handle_stripe_error(e, operation)
    
    # Customer operations
    async def create_customer(
        self,
        email: str,
        name: str = None,
        metadata: Dict[str, str] = None,
        **kwargs
    ) -> stripe.Customer:
        """Create Stripe customer."""
        params = {
            "email": email,
            "metadata": metadata or {}
        }
        
        if name:
            params["name"] = name
        
        params.update(kwargs)
        
        return await self._make_request(
            "create_customer",
            stripe.Customer.create,
            **params
        )
    
    async def get_customer(self, customer_id: str) -> stripe.Customer:
        """Get Stripe customer by ID."""
        return await self._make_request(
            "get_customer",
            stripe.Customer.retrieve,
            customer_id
        )
    
    async def update_customer(
        self,
        customer_id: str,
        **kwargs
    ) -> stripe.Customer:
        """Update Stripe customer."""
        return await self._make_request(
            "update_customer",
            stripe.Customer.modify,
            customer_id,
            **kwargs
        )
    
    async def delete_customer(self, customer_id: str) -> stripe.Customer:
        """Delete Stripe customer."""
        return await self._make_request(
            "delete_customer",
            stripe.Customer.delete,
            customer_id
        )
    
    # Subscription operations
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Dict[str, str] = None,
        trial_period_days: int = None,
        **kwargs
    ) -> stripe.Subscription:
        """Create Stripe subscription."""
        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "metadata": metadata or {}
        }
        
        if trial_period_days is not None:
            params["trial_period_days"] = trial_period_days
        
        params.update(kwargs)
        
        return await self._make_request(
            "create_subscription",
            stripe.Subscription.create,
            **params
        )
    
    async def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Get Stripe subscription by ID."""
        return await self._make_request(
            "get_subscription",
            stripe.Subscription.retrieve,
            subscription_id
        )
    
    async def update_subscription(
        self,
        subscription_id: str,
        **kwargs
    ) -> stripe.Subscription:
        """Update Stripe subscription."""
        return await self._make_request(
            "update_subscription",
            stripe.Subscription.modify,
            subscription_id,
            **kwargs
        )
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> stripe.Subscription:
        """Cancel Stripe subscription."""
        if at_period_end:
            return await self._make_request(
                "cancel_subscription",
                stripe.Subscription.modify,
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            return await self._make_request(
                "cancel_subscription",
                stripe.Subscription.delete,
                subscription_id
            )
    
    async def list_subscriptions(
        self,
        customer_id: str = None,
        status: str = None,
        limit: int = 10,
        **kwargs
    ) -> stripe.ListObject:
        """List Stripe subscriptions."""
        params = {"limit": limit}
        
        if customer_id:
            params["customer"] = customer_id
        
        if status:
            params["status"] = status
        
        params.update(kwargs)
        
        return await self._make_request(
            "list_subscriptions",
            stripe.Subscription.list,
            **params
        )
    
    # Payment Method operations
    async def create_setup_intent(
        self,
        customer_id: str,
        usage: str = "off_session",
        metadata: Dict[str, str] = None
    ) -> stripe.SetupIntent:
        """Create setup intent for saving payment methods."""
        params = {
            "customer": customer_id,
            "usage": usage,
            "metadata": metadata or {}
        }
        
        return await self._make_request(
            "create_setup_intent",
            stripe.SetupIntent.create,
            **params
        )
    
    async def list_payment_methods(
        self,
        customer_id: str,
        type: str = "card"
    ) -> stripe.ListObject:
        """List customer payment methods."""
        return await self._make_request(
            "list_payment_methods",
            stripe.PaymentMethod.list,
            customer=customer_id,
            type=type
        )
    
    async def detach_payment_method(self, payment_method_id: str) -> stripe.PaymentMethod:
        """Detach payment method from customer."""
        return await self._make_request(
            "detach_payment_method",
            stripe.PaymentMethod.detach,
            payment_method_id
        )
    
    # Invoice operations
    async def get_upcoming_invoice(self, customer_id: str) -> stripe.Invoice:
        """Get upcoming invoice for customer."""
        return await self._make_request(
            "get_upcoming_invoice",
            stripe.Invoice.upcoming,
            customer=customer_id
        )
    
    async def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
        **kwargs
    ) -> stripe.ListObject:
        """List customer invoices."""
        params = {
            "customer": customer_id,
            "limit": limit
        }
        params.update(kwargs)
        
        return await self._make_request(
            "list_invoices",
            stripe.Invoice.list,
            **params
        )
    
    # Price and Product operations
    async def list_prices(
        self,
        product: str = None,
        active: bool = True,
        limit: int = 100
    ) -> stripe.ListObject:
        """List Stripe prices."""
        params = {
            "active": active,
            "limit": limit
        }
        
        if product:
            params["product"] = product
        
        return await self._make_request(
            "list_prices",
            stripe.Price.list,
            **params
        )
    
    async def get_price(self, price_id: str) -> stripe.Price:
        """Get Stripe price by ID."""
        return await self._make_request(
            "get_price",
            stripe.Price.retrieve,
            price_id
        )
    
    async def list_products(self, active: bool = True, limit: int = 100) -> stripe.ListObject:
        """List Stripe products."""
        return await self._make_request(
            "list_products",
            stripe.Product.list,
            active=active,
            limit=limit
        )
    
    # Portal operations
    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> stripe.billing_portal.Session:
        """Create billing portal session."""
        return await self._make_request(
            "create_billing_portal_session",
            stripe.billing_portal.Session.create,
            customer=customer_id,
            return_url=return_url
        )
    
    # Webhook operations
    def construct_event(
        self,
        payload: bytes,
        sig_header: str,
        endpoint_secret: str
    ) -> stripe.Event:
        """Construct and verify webhook event."""
        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            logger.error("Invalid webhook payload", error=str(e))
            raise StripeError(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            logger.error("Invalid webhook signature", error=str(e))
            raise StripeError(f"Invalid signature: {str(e)}")
    
    # Usage and metering (for usage-based billing)
    async def create_usage_record(
        self,
        subscription_item_id: str,
        quantity: int,
        timestamp: int = None,
        action: str = "increment"
    ) -> stripe.UsageRecord:
        """Create usage record for metered billing."""
        params = {
            "quantity": quantity,
            "action": action
        }
        
        if timestamp:
            params["timestamp"] = timestamp
        
        return await self._make_request(
            "create_usage_record",
            stripe.SubscriptionItem.create_usage_record,
            subscription_item_id,
            **params
        )
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform Stripe API health check."""
        health_status = {
            "service": "stripe",
            "status": "unhealthy",
            "details": {}
        }
        
        try:
            start_time = time.time()
            
            # Simple API call to test connectivity
            account = await self._make_request(
                "health_check",
                stripe.Account.retrieve
            )
            
            response_time = (time.time() - start_time) * 1000
            
            health_status.update({
                "status": "healthy",
                "details": {
                    "account_id": account.id,
                    "business_profile": account.business_profile.name if account.business_profile else None,
                    "country": account.country,
                    "charges_enabled": account.charges_enabled,
                    "payouts_enabled": account.payouts_enabled,
                    "response_time_ms": round(response_time, 2),
                    "api_version": stripe.api_version
                }
            })
            
        except Exception as e:
            health_status["details"]["error"] = str(e)
            logger.error("Stripe health check failed", error=str(e))
        
        return health_status


# Global Stripe client instance
_stripe_client: Optional[StripeClient] = None


def get_stripe_client() -> StripeClient:
    """Get or create Stripe client instance."""
    global _stripe_client
    
    if _stripe_client is None:
        _stripe_client = StripeClient()
    
    return _stripe_client