"""Webhook routes for external service integrations."""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from typing import Optional
import structlog

from src.services.stripe import WebhookService as StripeWebhookService
from src.services.plaid import WebhookService as PlaidWebhookService
from src.exceptions import StripeError, PlaidError
from src.middleware import TenantContextMiddleware

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events."""
    if not stripe_signature:
        logger.warning("Missing Stripe signature header")
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    try:
        # Get raw request body
        payload = await request.body()
        
        # Process webhook
        webhook_service = StripeWebhookService()
        result = await webhook_service.process_webhook(payload, stripe_signature)
        
        logger.info("Stripe webhook processed successfully",
                   event_id=result.get("event_id"),
                   event_type=result.get("event_type"))
        
        return JSONResponse(
            status_code=200,
            content={"received": True, "result": result}
        )
        
    except StripeError as e:
        logger.error("Stripe webhook processing failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error("Unexpected error in Stripe webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/plaid")
async def plaid_webhook(request: Request):
    """Handle Plaid webhook events."""
    try:
        # Get request body
        payload = await request.json()
        
        # Process webhook
        webhook_service = PlaidWebhookService()
        result = await webhook_service.process_webhook(payload)
        
        logger.info("Plaid webhook processed successfully",
                   webhook_type=payload.get("webhook_type"),
                   webhook_code=payload.get("webhook_code"))
        
        return JSONResponse(
            status_code=200,
            content={"received": True, "result": result}
        )
        
    except PlaidError as e:
        logger.error("Plaid webhook processing failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error("Unexpected error in Plaid webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def webhook_health_check():
    """Health check for webhook endpoints."""
    return {
        "status": "healthy",
        "endpoints": {
            "stripe": "/webhooks/stripe",
            "plaid": "/webhooks/plaid"
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }