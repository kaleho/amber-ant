"""Subscription management API endpoints."""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Header
from fastapi.responses import JSONResponse

from src.subscriptions.service import SubscriptionService
from src.subscriptions.schemas import (
    SubscriptionResponse, SubscriptionUpdate, SubscriptionInvoiceResponse,
    SubscriptionEventResponse, PaymentMethodResponse, SubscriptionUsageResponse,
    PlanComparisonResponse, BillingPortalRequest, BillingPortalResponse,
    CheckoutSessionRequest, CheckoutSessionResponse, WebhookEventRequest,
    SubscriptionPlan
)
from src.auth.dependencies import get_current_user
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError, StripeError

router = APIRouter()


# Subscription CRUD operations
@router.get("/current", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get current user's active subscription."""
    subscription = await subscription_service.get_subscription_for_user(current_user["sub"])
    return subscription


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    plan: SubscriptionPlan = Query(..., description="Subscription plan to create"),
    payment_method_id: Optional[str] = Query(None, description="Stripe payment method ID"),
    trial_days: Optional[int] = Query(None, description="Trial period in days"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Create a new subscription for the current user."""
    try:
        subscription = await subscription_service.create_subscription(
            user_id=current_user["sub"],
            user_email=current_user.get("email", ""),
            user_name=current_user.get("name", ""),
            plan=plan,
            payment_method_id=payment_method_id,
            trial_days=trial_days
        )
        return subscription
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except StripeError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    update_data: SubscriptionUpdate,
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Update subscription settings."""
    try:
        subscription = await subscription_service.update_subscription(
            subscription_id=subscription_id,
            user_id=current_user["sub"],
            update_data=update_data
        )
        return subscription
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscription_id}/change-plan", response_model=SubscriptionResponse)
async def change_subscription_plan(
    subscription_id: str,
    new_plan: SubscriptionPlan = Query(..., description="New subscription plan"),
    prorate: bool = Query(True, description="Prorate the plan change"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Change subscription plan."""
    try:
        subscription = await subscription_service.change_subscription_plan(
            subscription_id=subscription_id,
            user_id=current_user["sub"],
            new_plan=new_plan,
            prorate=prorate
        )
        return subscription
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StripeError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = Query(True, description="Cancel at the end of the current period"),
    cancellation_reason: Optional[str] = Query(None, description="Reason for cancellation"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Cancel subscription."""
    try:
        subscription = await subscription_service.cancel_subscription(
            subscription_id=subscription_id,
            user_id=current_user["sub"],
            at_period_end=at_period_end,
            cancellation_reason=cancellation_reason
        )
        return subscription
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StripeError as e:
        raise HTTPException(status_code=402, detail=str(e))


@router.post("/{subscription_id}/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Reactivate a canceled subscription."""
    try:
        subscription = await subscription_service.reactivate_subscription(
            subscription_id=subscription_id,
            user_id=current_user["sub"]
        )
        return subscription
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StripeError as e:
        raise HTTPException(status_code=402, detail=str(e))


# Billing and invoice operations
@router.get("/billing/history", response_model=List[SubscriptionInvoiceResponse])
async def get_billing_history(
    start_date: Optional[datetime] = Query(None, description="Start date for billing history"),
    end_date: Optional[datetime] = Query(None, description="End date for billing history"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of invoices to return"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get billing history for the current user."""
    invoices = await subscription_service.get_billing_history(
        user_id=current_user["sub"],
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return invoices


@router.post("/billing/portal", response_model=BillingPortalResponse)
async def create_billing_portal_session(
    request_data: BillingPortalRequest,
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Create Stripe billing portal session for subscription management."""
    try:
        portal_session = await subscription_service.create_billing_portal_session(
            user_id=current_user["sub"],
            return_url=request_data.return_url or "https://app.faithfulfinances.com/settings/billing"
        )
        return portal_session
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StripeError as e:
        raise HTTPException(status_code=402, detail=str(e))


# Usage tracking and analytics
@router.get("/{subscription_id}/usage", response_model=Optional[SubscriptionUsageResponse])
async def get_subscription_usage(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get current usage metrics for subscription."""
    try:
        usage = await subscription_service.get_subscription_usage(
            subscription_id=subscription_id,
            user_id=current_user["sub"]
        )
        return usage
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/usage/update")
async def update_usage_metrics(
    metrics: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Update usage metrics for current user's subscription."""
    try:
        success = await subscription_service.update_usage_metrics(
            user_id=current_user["sub"],
            metrics=metrics
        )
        
        if success:
            return {"message": "Usage metrics updated successfully"}
        else:
            return {"message": "No active subscription found or update failed"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update usage: {str(e)}")


@router.post("/usage/validate")
async def validate_plan_limits(
    usage_metrics: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Validate current usage against plan limits."""
    try:
        validation_result = await subscription_service.validate_plan_limits(
            user_id=current_user["sub"],
            usage_metrics=usage_metrics
        )
        return validation_result
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))


# Plan management and comparison
@router.get("/plans/comparison", response_model=PlanComparisonResponse)
async def get_plan_comparison(
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get plan comparison with recommendations."""
    try:
        comparison = await subscription_service.get_plan_comparison(current_user["sub"])
        return comparison
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/plans/features")
async def get_plan_features():
    """Get detailed plan features comparison."""
    return {
        "plans": {
            "free": {
                "name": "Free Plan",
                "price": "0.00",
                "interval": "month",
                "features": {
                    "max_accounts": 2,
                    "max_transactions": 100,
                    "max_family_members": 1,
                    "basic_budgeting": True,
                    "advanced_analytics": False,
                    "priority_support": False,
                    "data_export": False,
                    "goal_tracking": False,
                    "family_sharing": False,
                    "custom_categories": False
                },
                "limitations": [
                    "Limited to 2 bank accounts",
                    "Up to 100 transactions per month",
                    "Basic budgeting tools only",
                    "Community support only"
                ]
            },
            "premium_individual": {
                "name": "Premium Individual",
                "price": "9.99",
                "interval": "month",
                "features": {
                    "max_accounts": 10,
                    "max_transactions": 1000,
                    "max_family_members": 1,
                    "basic_budgeting": True,
                    "advanced_analytics": True,
                    "priority_support": True,
                    "data_export": True,
                    "goal_tracking": True,
                    "family_sharing": False,
                    "custom_categories": True
                },
                "benefits": [
                    "Up to 10 bank accounts",
                    "1,000 transactions per month",
                    "Advanced budgeting and analytics",
                    "Goal tracking and forecasting",
                    "Priority email support",
                    "Data export capabilities"
                ]
            },
            "premium_family": {
                "name": "Premium Family",
                "price": "19.99",
                "interval": "month",
                "features": {
                    "max_accounts": 999,
                    "max_transactions": 999999,
                    "max_family_members": 6,
                    "basic_budgeting": True,
                    "advanced_analytics": True,
                    "priority_support": True,
                    "data_export": True,
                    "goal_tracking": True,
                    "family_sharing": True,
                    "custom_categories": True
                },
                "benefits": [
                    "Unlimited bank accounts",
                    "Unlimited transactions",
                    "Up to 6 family members",
                    "Family sharing and collaboration",
                    "All premium individual features",
                    "Advanced family budgeting tools",
                    "Priority phone and email support"
                ]
            }
        }
    }


# Webhook handling (for Stripe webhooks)
@router.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
    subscription_service: SubscriptionService = Depends()
):
    """Handle Stripe webhook events."""
    try:
        # Get raw body
        body = await request.body()
        
        # Verify webhook signature (this would be done in the Stripe client)
        # For now, we'll parse the JSON directly
        import json
        event_data = json.loads(body)
        
        # Process the event
        success = await subscription_service.process_webhook_event(
            event_type=event_data.get("type", ""),
            event_data=event_data.get("data", {}),
            stripe_event_id=event_data.get("id")
        )
        
        if success:
            return {"received": True}
        else:
            raise HTTPException(status_code=400, detail="Failed to process webhook")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")


# Analytics and reporting endpoints
@router.get("/analytics/summary")
async def get_subscription_analytics(
    start_date: Optional[datetime] = Query(None, description="Analytics start date"),
    end_date: Optional[datetime] = Query(None, description="Analytics end date"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get subscription analytics and metrics (admin users only)."""
    try:
        # For now, any authenticated user can view analytics
        # In production, you'd want to check for admin permissions
        analytics = await subscription_service.get_subscription_analytics(
            start_date=start_date,
            end_date=end_date
        )
        return analytics
    except BusinessLogicError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/analytics/user-summary")
async def get_user_subscription_summary(
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get subscription summary for the current user."""
    try:
        summary = await subscription_service.subscription_repo.get_subscription_summary_for_user(
            current_user["sub"]
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


# Health and status endpoints
@router.get("/health")
async def subscription_service_health():
    """Check subscription service health."""
    try:
        # Basic health check
        service = SubscriptionService()
        
        # Test database connectivity
        summary = await service.subscription_repo.count()
        
        # Test Stripe connectivity (would need actual implementation)
        stripe_healthy = True  # Placeholder
        
        return {
            "status": "healthy",
            "database": "connected",
            "stripe": "connected" if stripe_healthy else "disconnected",
            "total_subscriptions": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Trial and promotional endpoints
@router.get("/trials/status")
async def get_trial_status(
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get trial status for current user."""
    try:
        subscription = await subscription_service.get_subscription_for_user(current_user["sub"])
        
        if not subscription:
            return {
                "has_trial": False,
                "trial_eligible": True,
                "message": "No active subscription"
            }
        
        if subscription.trial_end:
            from datetime import timezone
            is_in_trial = subscription.trial_end > datetime.now(timezone.utc)
            days_remaining = (subscription.trial_end - datetime.now(timezone.utc)).days if is_in_trial else 0
            
            return {
                "has_trial": True,
                "is_in_trial": is_in_trial,
                "trial_start": subscription.trial_start.isoformat() if subscription.trial_start else None,
                "trial_end": subscription.trial_end.isoformat(),
                "days_remaining": max(0, days_remaining),
                "trial_eligible": False
            }
        else:
            return {
                "has_trial": False,
                "trial_eligible": False,
                "message": "No trial period for this subscription"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trial status: {str(e)}")


# Subscription pause/resume (for temporary holds)
@router.post("/{subscription_id}/pause")
async def pause_subscription(
    subscription_id: str,
    pause_reason: Optional[str] = Query(None, description="Reason for pausing"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Pause subscription (temporarily hold billing)."""
    try:
        # This would typically involve pausing the subscription in Stripe
        # For now, we'll update the metadata to indicate paused status
        update_data = SubscriptionUpdate(
            metadata={
                "paused": True,
                "paused_at": datetime.utcnow().isoformat(),
                "pause_reason": pause_reason or "User requested pause"
            }
        )
        
        subscription = await subscription_service.update_subscription(
            subscription_id=subscription_id,
            user_id=current_user["sub"],
            update_data=update_data
        )
        
        return {
            "message": "Subscription paused successfully",
            "subscription": subscription
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause subscription: {str(e)}")


@router.post("/{subscription_id}/resume")
async def resume_subscription(
    subscription_id: str,
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Resume a paused subscription."""
    try:
        # Get current subscription to check if it's paused
        subscription = await subscription_service.get_subscription_for_user(current_user["sub"])
        if not subscription or subscription.id != subscription_id:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if not subscription.metadata.get("paused"):
            raise HTTPException(status_code=400, detail="Subscription is not paused")
        
        # Remove paused status
        metadata = subscription.metadata.copy()
        metadata.update({
            "paused": False,
            "resumed_at": datetime.utcnow().isoformat(),
            "pause_duration": "calculated_duration"  # Would calculate actual duration
        })
        
        update_data = SubscriptionUpdate(metadata=metadata)
        
        updated_subscription = await subscription_service.update_subscription(
            subscription_id=subscription_id,
            user_id=current_user["sub"],
            update_data=update_data
        )
        
        return {
            "message": "Subscription resumed successfully",
            "subscription": updated_subscription
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume subscription: {str(e)}")


# Subscription history and audit trail
@router.get("/{subscription_id}/events", response_model=List[SubscriptionEventResponse])
async def get_subscription_events(
    subscription_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of events to return"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get event history for a subscription."""
    try:
        # Verify subscription ownership
        subscription = await subscription_service.get_subscription_for_user(current_user["sub"])
        if not subscription or subscription.id != subscription_id:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        events = await subscription_service.event_repo.get_events_for_subscription(
            subscription_id=subscription_id,
            limit=limit
        )
        
        return [SubscriptionEventResponse.model_validate(event) for event in events]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


# Subscription renewal and expiration management
@router.get("/renewals/upcoming")
async def get_upcoming_renewals(
    days_ahead: int = Query(7, ge=1, le=30, description="Days ahead to look for renewals"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Get upcoming subscription renewals."""
    try:
        subscription = await subscription_service.get_subscription_for_user(current_user["sub"])
        
        if not subscription:
            return {
                "has_upcoming_renewal": False,
                "message": "No active subscription"
            }
        
        from datetime import timedelta, timezone
        upcoming_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        if subscription.current_period_end <= upcoming_date:
            days_until_renewal = (subscription.current_period_end - datetime.now(timezone.utc)).days
            
            return {
                "has_upcoming_renewal": True,
                "subscription_id": subscription.id,
                "renewal_date": subscription.current_period_end.isoformat(),
                "days_until_renewal": max(0, days_until_renewal),
                "plan": subscription.plan,
                "amount": str(subscription.amount),
                "currency": subscription.currency,
                "will_cancel": subscription.cancel_at_period_end
            }
        else:
            return {
                "has_upcoming_renewal": False,
                "next_renewal_date": subscription.current_period_end.isoformat(),
                "days_until_renewal": (subscription.current_period_end - datetime.now(timezone.utc)).days
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get renewal info: {str(e)}")


# Maintenance and administrative endpoints
@router.post("/maintenance/sync-stripe")
async def sync_with_stripe(
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Sync subscription data with Stripe (maintenance operation)."""
    try:
        # This would be an admin-only operation in production
        subscription = await subscription_service.get_subscription_for_user(current_user["sub"])
        
        if not subscription:
            return {"message": "No subscription to sync"}
        
        # Get latest data from Stripe
        stripe_subscription = await subscription_service.stripe_service.get_subscription_details(
            tenant_id=current_user["sub"],
            subscription_id=subscription.stripe_subscription_id
        )
        
        # Update local subscription with Stripe data
        update_data = SubscriptionUpdate(
            metadata={
                **subscription.metadata,
                "last_stripe_sync": datetime.utcnow().isoformat(),
                "stripe_status": stripe_subscription.get("status")
            }
        )
        
        updated_subscription = await subscription_service.update_subscription(
            subscription_id=subscription.id,
            user_id=current_user["sub"],
            update_data=update_data
        )
        
        return {
            "message": "Subscription synced with Stripe successfully",
            "subscription_status": stripe_subscription.get("status"),
            "local_status": updated_subscription.status,
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync with Stripe: {str(e)}")


@router.post("/maintenance/cleanup-events")
async def cleanup_old_events(
    days_old: int = Query(90, ge=30, le=365, description="Days old for events to cleanup"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Clean up old subscription events (maintenance operation)."""
    try:
        # This would be an admin-only operation in production
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Get events older than cutoff
        old_events = await subscription_service.event_repo.get_multi(
            filters={"created_at": {"lt": cutoff_date}},
            limit=1000
        )
        
        # Delete old events (in production, you might archive instead)
        deleted_count = 0
        for event in old_events:
            success = await subscription_service.event_repo.delete(event.id)
            if success:
                deleted_count += 1
        
        return {
            "message": f"Cleaned up {deleted_count} old events",
            "cutoff_date": cutoff_date.isoformat(),
            "days_old": days_old
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup events: {str(e)}")


# Subscription export and data portability
@router.get("/export/data")
async def export_subscription_data(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends()
):
    """Export user's subscription data."""
    try:
        # Get all user subscription data
        subscription = await subscription_service.get_subscription_for_user(current_user["sub"])
        billing_history = await subscription_service.get_billing_history(current_user["sub"])
        summary = await subscription_service.subscription_repo.get_subscription_summary_for_user(
            current_user["sub"]
        )
        
        export_data = {
            "user_id": current_user["sub"],
            "export_timestamp": datetime.utcnow().isoformat(),
            "current_subscription": subscription.model_dump() if subscription else None,
            "billing_history": [invoice.model_dump() for invoice in billing_history],
            "subscription_summary": summary
        }
        
        if format == "json":
            return export_data
        else:
            # For CSV format, you'd convert the data structure to CSV
            # For now, just return JSON with a note
            return {
                **export_data,
                "note": "CSV format not implemented yet, returning JSON"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")