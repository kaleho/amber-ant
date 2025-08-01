"""Stripe payment processing service."""

from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timezone

import stripe
import structlog

from .client import StripeClient, get_stripe_client
from src.exceptions import StripeError, ValidationError

logger = structlog.get_logger(__name__)


class PaymentService:
    """Service for handling Stripe payments and payment methods."""
    
    def __init__(self, stripe_client: Optional[StripeClient] = None):
        self.stripe_client = stripe_client or get_stripe_client()
    
    async def create_setup_intent(
        self,
        tenant_id: str,
        customer_id: str,
        usage: str = "off_session",
        return_url: str = None
    ) -> Dict[str, Any]:
        """Create setup intent for collecting payment method."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            setup_intent_params = {
                "customer_id": customer_id,
                "usage": usage,
                "metadata": {
                    "tenant_id": tenant_id,
                    "created_via": "api"
                }
            }
            
            if return_url:
                setup_intent_params["return_url"] = return_url
            
            setup_intent = await self.stripe_client.create_setup_intent(**setup_intent_params)
            
            logger.info("Setup intent created",
                       tenant_id=tenant_id,
                       customer_id=customer_id,
                       setup_intent_id=setup_intent.id)
            
            return {
                "setup_intent_id": setup_intent.id,
                "client_secret": setup_intent.client_secret,
                "status": setup_intent.status,
                "usage": setup_intent.usage,
                "customer_id": customer_id
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to create setup intent",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        error=str(e))
            raise StripeError(f"Failed to create setup intent: {str(e)}")
    
    async def list_payment_methods(
        self,
        tenant_id: str,
        customer_id: str,
        type: str = "card"
    ) -> List[Dict[str, Any]]:
        """List customer payment methods."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            payment_methods = await self.stripe_client.list_payment_methods(customer_id, type)
            
            methods = []
            for pm in payment_methods.data:
                method_info = {
                    "id": pm.id,
                    "type": pm.type,
                    "created": pm.created
                }
                
                # Add type-specific details
                if pm.type == "card" and pm.card:
                    method_info["card"] = {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year,
                        "funding": pm.card.funding,
                        "country": pm.card.country
                    }
                elif pm.type == "us_bank_account" and pm.us_bank_account:
                    method_info["us_bank_account"] = {
                        "account_holder_type": pm.us_bank_account.account_holder_type,
                        "account_type": pm.us_bank_account.account_type,
                        "bank_name": pm.us_bank_account.bank_name,
                        "last4": pm.us_bank_account.last4,
                        "routing_number": pm.us_bank_account.routing_number
                    }
                
                methods.append(method_info)
            
            logger.debug("Payment methods listed",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        count=len(methods))
            
            return methods
            
        except stripe.error.StripeError as e:
            logger.error("Failed to list payment methods",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        error=str(e))
            raise StripeError(f"Failed to list payment methods: {str(e)}")
    
    async def set_default_payment_method(
        self,
        tenant_id: str,
        customer_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Set default payment method for customer."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            # Update customer's default payment method
            updated_customer = await self.stripe_client.update_customer(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )
            
            logger.info("Default payment method set",
                       tenant_id=tenant_id,
                       customer_id=customer_id,
                       payment_method_id=payment_method_id)
            
            return {
                "customer_id": customer_id,
                "default_payment_method": payment_method_id,
                "updated": True
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to set default payment method",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        payment_method_id=payment_method_id,
                        error=str(e))
            raise StripeError(f"Failed to set default payment method: {str(e)}")
    
    async def delete_payment_method(
        self,
        tenant_id: str,
        customer_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Delete customer payment method."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            # Detach payment method
            payment_method = await self.stripe_client.detach_payment_method(payment_method_id)
            
            logger.info("Payment method deleted",
                       tenant_id=tenant_id,
                       customer_id=customer_id,
                       payment_method_id=payment_method_id)
            
            return {
                "payment_method_id": payment_method_id,
                "deleted": True,
                "type": payment_method.type
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to delete payment method",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        payment_method_id=payment_method_id,
                        error=str(e))
            raise StripeError(f"Failed to delete payment method: {str(e)}")
    
    async def create_payment_intent(
        self,
        tenant_id: str,
        customer_id: str,
        amount: int,
        currency: str = "usd",
        payment_method_id: str = None,
        description: str = None,
        metadata: Dict[str, str] = None,
        automatic_payment_methods: bool = True
    ) -> Dict[str, Any]:
        """Create payment intent for one-time payment."""
        try:
            # Verify customer belongs to tenant
            customer = await self.stripe_client.get_customer(customer_id)
            if customer.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Customer does not belong to tenant")
            
            # Validate amount
            if amount <= 0:
                raise ValidationError("Amount must be greater than 0")
            
            params = {
                "amount": amount,
                "currency": currency.lower(),
                "customer": customer_id,
                "metadata": {
                    "tenant_id": tenant_id,
                    "created_via": "api",
                    **(metadata or {})
                }
            }
            
            if description:
                params["description"] = description
            
            if payment_method_id:
                params["payment_method"] = payment_method_id
                params["confirmation_method"] = "manual"
                params["confirm"] = True
            elif automatic_payment_methods:
                params["automatic_payment_methods"] = {"enabled": True}
            
            payment_intent = await self._make_request(
                "create_payment_intent",
                stripe.PaymentIntent.create,
                **params
            )
            
            logger.info("Payment intent created",
                       tenant_id=tenant_id,
                       customer_id=customer_id,
                       payment_intent_id=payment_intent.id,
                       amount=amount,
                       currency=currency)
            
            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "customer_id": customer_id,
                "next_action": payment_intent.next_action
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to create payment intent",
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        amount=amount,
                        error=str(e))
            raise StripeError(f"Failed to create payment intent: {str(e)}")
    
    async def confirm_payment_intent(
        self,
        tenant_id: str,
        payment_intent_id: str,
        payment_method_id: str = None
    ) -> Dict[str, Any]:
        """Confirm payment intent."""
        try:
            params = {}
            if payment_method_id:
                params["payment_method"] = payment_method_id
            
            payment_intent = await self._make_request(
                "confirm_payment_intent",
                stripe.PaymentIntent.confirm,
                payment_intent_id,
                **params
            )
            
            # Verify payment intent belongs to tenant
            if payment_intent.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Payment intent does not belong to tenant")
            
            logger.info("Payment intent confirmed",
                       tenant_id=tenant_id,
                       payment_intent_id=payment_intent_id,
                       status=payment_intent.status)
            
            return {
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "next_action": payment_intent.next_action
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to confirm payment intent",
                        tenant_id=tenant_id,
                        payment_intent_id=payment_intent_id,
                        error=str(e))
            raise StripeError(f"Failed to confirm payment intent: {str(e)}")
    
    async def cancel_payment_intent(
        self,
        tenant_id: str,
        payment_intent_id: str,
        cancellation_reason: str = None
    ) -> Dict[str, Any]:
        """Cancel payment intent."""
        try:
            # Get payment intent to verify ownership
            payment_intent = await self._make_request(
                "get_payment_intent",
                stripe.PaymentIntent.retrieve,
                payment_intent_id
            )
            
            # Verify payment intent belongs to tenant
            if payment_intent.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Payment intent does not belong to tenant")
            
            # Cancel payment intent
            canceled_payment_intent = await self._make_request(
                "cancel_payment_intent",
                stripe.PaymentIntent.cancel,
                payment_intent_id,
                cancellation_reason=cancellation_reason
            )
            
            logger.info("Payment intent canceled",
                       tenant_id=tenant_id,
                       payment_intent_id=payment_intent_id,
                       reason=cancellation_reason)
            
            return {
                "payment_intent_id": canceled_payment_intent.id,
                "status": canceled_payment_intent.status,
                "canceled_at": canceled_payment_intent.canceled_at,
                "cancellation_reason": cancellation_reason
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to cancel payment intent",
                        tenant_id=tenant_id,
                        payment_intent_id=payment_intent_id,
                        error=str(e))
            raise StripeError(f"Failed to cancel payment intent: {str(e)}")
    
    async def capture_payment_intent(
        self,
        tenant_id: str,
        payment_intent_id: str,
        amount_to_capture: int = None
    ) -> Dict[str, Any]:
        """Capture payment intent (for manual capture)."""
        try:
            # Get payment intent to verify ownership
            payment_intent = await self._make_request(
                "get_payment_intent",
                stripe.PaymentIntent.retrieve,
                payment_intent_id
            )
            
            # Verify payment intent belongs to tenant
            if payment_intent.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Payment intent does not belong to tenant")
            
            params = {}
            if amount_to_capture is not None:
                params["amount_to_capture"] = amount_to_capture
            
            # Capture payment intent
            captured_payment_intent = await self._make_request(
                "capture_payment_intent",
                stripe.PaymentIntent.capture,
                payment_intent_id,
                **params
            )
            
            logger.info("Payment intent captured",
                       tenant_id=tenant_id,
                       payment_intent_id=payment_intent_id,
                       amount_captured=amount_to_capture or payment_intent.amount)
            
            return {
                "payment_intent_id": captured_payment_intent.id,
                "status": captured_payment_intent.status,
                "amount_capturable": captured_payment_intent.amount_capturable,
                "amount_received": captured_payment_intent.amount_received
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to capture payment intent",
                        tenant_id=tenant_id,
                        payment_intent_id=payment_intent_id,
                        error=str(e))
            raise StripeError(f"Failed to capture payment intent: {str(e)}")
    
    async def create_refund(
        self,
        tenant_id: str,
        payment_intent_id: str,
        amount: int = None,
        reason: str = None,
        metadata: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create refund for payment intent."""
        try:
            # Get payment intent to verify ownership
            payment_intent = await self._make_request(
                "get_payment_intent",
                stripe.PaymentIntent.retrieve,
                payment_intent_id
            )
            
            # Verify payment intent belongs to tenant
            if payment_intent.metadata.get("tenant_id") != tenant_id:
                raise ValidationError("Payment intent does not belong to tenant")
            
            params = {
                "payment_intent": payment_intent_id,
                "metadata": {
                    "tenant_id": tenant_id,
                    "refunded_via": "api",
                    **(metadata or {})
                }
            }
            
            if amount:
                params["amount"] = amount
            
            if reason:
                params["reason"] = reason
            
            refund = await self._make_request(
                "create_refund",
                stripe.Refund.create,
                **params
            )
            
            logger.info("Refund created",
                       tenant_id=tenant_id,
                       payment_intent_id=payment_intent_id,
                       refund_id=refund.id,
                       amount=refund.amount,
                       reason=reason)
            
            return {
                "refund_id": refund.id,
                "amount": refund.amount,
                "currency": refund.currency,
                "status": refund.status,
                "reason": refund.reason,
                "payment_intent_id": payment_intent_id
            }
            
        except stripe.error.StripeError as e:
            logger.error("Failed to create refund",
                        tenant_id=tenant_id,
                        payment_intent_id=payment_intent_id,
                        error=str(e))
            raise StripeError(f"Failed to create refund: {str(e)}")
    
    async def _make_request(self, operation: str, func, *args, **kwargs):
        """Make Stripe API request with error handling."""
        return await self.stripe_client._make_request(operation, func, *args, **kwargs)