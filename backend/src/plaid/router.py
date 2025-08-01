"""Plaid integration API endpoints."""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse

from src.services.plaid.client import PlaidClient
from src.auth.dependencies import get_current_user
from src.exceptions import NotFoundError, ValidationError, BusinessLogicError
from src.accounts.service import AccountService
from src.transactions.service import TransactionService

router = APIRouter()


# Link Token Management
@router.post("/link/token/create")
async def create_link_token(
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends()
):
    """Create a link token for Plaid Link initialization."""
    try:
        link_token = await plaid_client.create_link_token(
            user_id=current_user["sub"],
            client_name="Faithful Finances"
        )
        
        return {
            "link_token": link_token,
            "expiration": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create link token: {str(e)}")


@router.post("/link/token/exchange")
async def exchange_public_token(
    public_token: str,
    institution_id: Optional[str] = None,
    institution_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends(),
    account_service: AccountService = Depends()
):
    """Exchange public token for access token and fetch accounts."""
    try:
        # Exchange public token for access token
        exchange_result = await plaid_client.exchange_public_token(public_token)
        access_token = exchange_result["access_token"]
        item_id = exchange_result["item_id"]
        
        # Get institution info if not provided
        if not institution_name and institution_id:
            institution_info = await plaid_client.get_institution(institution_id)
            institution_name = institution_info.get("name", "Unknown Institution")
        
        # Fetch accounts from Plaid
        accounts_response = await plaid_client.get_accounts(access_token)
        plaid_accounts = accounts_response.get("accounts", [])
        
        # Store Plaid item and create accounts in our system
        created_accounts = []
        for plaid_account in plaid_accounts:
            try:
                # Create account in our system
                account_data = {
                    "name": plaid_account.get("name", "Unknown Account"),
                    "official_name": plaid_account.get("official_name"),
                    "type": plaid_account.get("type", "depository"),
                    "subtype": plaid_account.get("subtype", "checking"),
                    "mask": plaid_account.get("mask"),
                    "plaid_account_id": plaid_account["account_id"],
                    "plaid_item_id": item_id,
                    "institution_id": institution_id,
                    "institution_name": institution_name,
                    "balance_data": plaid_account.get("balances", {}),
                    "current_balance": plaid_account.get("balances", {}).get("current"),
                    "available_balance": plaid_account.get("balances", {}).get("available"),
                    "iso_currency_code": plaid_account.get("balances", {}).get("iso_currency_code", "USD"),
                    "is_active": True,
                    "is_manual": False,
                    "sync_status": "active"
                }
                
                account = await account_service.create_account(
                    user_id=current_user["sub"],
                    account_data=account_data
                )
                created_accounts.append(account)
                
            except Exception as account_error:
                # Log error but continue with other accounts
                print(f"Failed to create account {plaid_account.get('account_id')}: {account_error}")
                continue
        
        return {
            "message": f"Successfully linked {len(created_accounts)} accounts",
            "item_id": item_id,
            "institution_name": institution_name,
            "accounts": created_accounts,
            "total_accounts": len(created_accounts)
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to exchange token: {str(e)}")


# Account Management
@router.get("/accounts")
async def get_plaid_accounts(
    current_user: dict = Depends(get_current_user),
    account_service: AccountService = Depends()
):
    """Get all Plaid-linked accounts for user."""
    try:
        # Get accounts that are linked to Plaid (have plaid_account_id)
        accounts = await account_service.get_user_accounts(
            user_id=current_user["sub"],
            filters={"is_manual": False}  # Only Plaid accounts
        )
        
        return {
            "accounts": accounts,
            "total": len(accounts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accounts: {str(e)}")


@router.post("/accounts/{account_id}/sync")
async def sync_account(
    account_id: str,
    force_sync: bool = Query(False, description="Force sync even if recently synced"),
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends(),
    account_service: AccountService = Depends(),
    transaction_service: TransactionService = Depends()
):
    """Sync account data from Plaid."""
    try:
        # Get account to verify ownership and get Plaid info
        account = await account_service.get_account(account_id, current_user["sub"])
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        if not account.plaid_account_id:
            raise HTTPException(status_code=400, detail="Account is not linked to Plaid")
        
        # Get access token for this account's item
        # Note: In a real implementation, you'd store and retrieve the access token securely
        # For now, we'll simulate the sync process
        
        # Sync account balances
        try:
            # This would call Plaid's /accounts/get endpoint
            # plaid_accounts = await plaid_client.get_accounts(access_token)
            # account_data = next((acc for acc in plaid_accounts["accounts"] 
            #                    if acc["account_id"] == account.plaid_account_id), None)
            
            # For now, simulate successful sync
            updated_account = await account_service.update_account_balance(
                account_id=account_id,
                user_id=current_user["sub"],
                balance_data={
                    "current": account.current_balance,  # Would be from Plaid
                    "available": account.available_balance,  # Would be from Plaid
                    "last_sync": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as sync_error:
            # Update sync status to error
            await account_service.update_account_sync_status(
                account_id=account_id,
                user_id=current_user["sub"],
                status="error",
                error_message=str(sync_error)
            )
            raise HTTPException(status_code=500, detail=f"Failed to sync account: {sync_error}")
        
        return {
            "message": "Account synced successfully",
            "account": updated_account,
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync account: {str(e)}")


@router.post("/accounts/sync-all")
async def sync_all_accounts(
    force_sync: bool = Query(False, description="Force sync even if recently synced"),
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends(),
    account_service: AccountService = Depends()
):
    """Sync all Plaid-linked accounts for user."""
    try:
        # Get all Plaid accounts for user
        accounts = await account_service.get_user_accounts(
            user_id=current_user["sub"],
            filters={"is_manual": False, "sync_status": "active"}
        )
        
        sync_results = []
        for account in accounts:
            try:
                # Sync each account (simplified for demo)
                updated_account = await account_service.update_account_balance(
                    account_id=account.id,
                    user_id=current_user["sub"],
                    balance_data={
                        "current": account.current_balance,
                        "available": account.available_balance,
                        "last_sync": datetime.utcnow().isoformat()
                    }
                )
                
                sync_results.append({
                    "account_id": account.id,
                    "account_name": account.name,
                    "status": "success",
                    "message": "Synced successfully"
                })
                
            except Exception as account_error:
                sync_results.append({
                    "account_id": account.id,
                    "account_name": account.name,
                    "status": "error",
                    "message": str(account_error)
                })
        
        successful_syncs = sum(1 for result in sync_results if result["status"] == "success")
        
        return {
            "message": f"Sync completed: {successful_syncs}/{len(accounts)} accounts successful",
            "results": sync_results,
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync accounts: {str(e)}")


# Transaction Management
@router.post("/transactions/sync")
async def sync_transactions(
    account_ids: Optional[List[str]] = Query(None, description="Specific account IDs to sync"),
    start_date: Optional[date] = Query(None, description="Start date for transaction sync"),
    end_date: Optional[date] = Query(None, description="End date for transaction sync"),
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends(),
    transaction_service: TransactionService = Depends(),
    account_service: AccountService = Depends()
):
    """Sync transactions from Plaid for specified accounts."""
    try:
        # Get user's Plaid accounts
        if account_ids:
            accounts = []
            for account_id in account_ids:
                account = await account_service.get_account(account_id, current_user["sub"])
                if account and account.plaid_account_id:
                    accounts.append(account)
        else:
            accounts = await account_service.get_user_accounts(
                user_id=current_user["sub"],
                filters={"is_manual": False, "sync_status": "active"}
            )
        
        if not accounts:
            return {
                "message": "No Plaid accounts found to sync",
                "synced_transactions": 0
            }
        
        # Set date range
        if not start_date:
            start_date = date.today().replace(day=1)  # Start of current month
        if not end_date:
            end_date = date.today()
        
        total_synced = 0
        sync_results = []
        
        for account in accounts:
            try:
                # In a real implementation, this would call Plaid's /transactions/get endpoint
                # transactions_response = await plaid_client.get_transactions(
                #     access_token, account.plaid_account_id, start_date, end_date
                # )
                
                # For now, simulate transaction sync
                synced_count = 0  # Would be len(transactions_response["transactions"])
                
                sync_results.append({
                    "account_id": account.id,
                    "account_name": account.name,
                    "synced_transactions": synced_count,
                    "status": "success"
                })
                
                total_synced += synced_count
                
            except Exception as account_error:
                sync_results.append({
                    "account_id": account.id,
                    "account_name": account.name,
                    "synced_transactions": 0,
                    "status": "error",
                    "error": str(account_error)
                })
        
        return {
            "message": f"Transaction sync completed: {total_synced} transactions synced",
            "total_synced": total_synced,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "results": sync_results,
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync transactions: {str(e)}")


# Institution Management
@router.get("/institutions/search")
async def search_institutions(
    query: str = Query(..., description="Institution name to search for"),
    country_codes: List[str] = Query(default=["US"], description="Country codes to search in"),
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends()
):
    """Search for institutions by name."""
    try:
        institutions = await plaid_client.search_institutions(query, country_codes)
        
        return {
            "institutions": institutions,
            "total": len(institutions),
            "query": query
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search institutions: {str(e)}")


@router.get("/institutions/{institution_id}")
async def get_institution(
    institution_id: str,
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends()
):
    """Get detailed information about an institution."""
    try:
        institution = await plaid_client.get_institution(institution_id)
        
        return {
            "institution": institution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get institution: {str(e)}")


# Item Management
@router.get("/items")
async def get_plaid_items(
    current_user: dict = Depends(get_current_user),
    account_service: AccountService = Depends()
):
    """Get all Plaid items (institution connections) for user."""
    try:
        # Get accounts grouped by Plaid item
        accounts = await account_service.get_user_accounts(
            user_id=current_user["sub"],
            filters={"is_manual": False}
        )
        
        # Group by plaid_item_id
        items = {}
        for account in accounts:
            if account.plaid_item_id:
                if account.plaid_item_id not in items:
                    items[account.plaid_item_id] = {
                        "item_id": account.plaid_item_id,
                        "institution_name": account.institution_name,
                        "institution_id": account.institution_id,
                        "accounts": [],
                        "last_sync": None
                    }
                
                items[account.plaid_item_id]["accounts"].append({
                    "id": account.id,
                    "name": account.name,
                    "type": account.type,
                    "subtype": account.subtype,
                    "mask": account.mask,
                    "current_balance": account.current_balance,
                    "sync_status": account.sync_status
                })
                
                # Update last sync time
                if account.last_sync_at:
                    current_last_sync = items[account.plaid_item_id]["last_sync"]
                    if not current_last_sync or account.last_sync_at > current_last_sync:
                        items[account.plaid_item_id]["last_sync"] = account.last_sync_at
        
        return {
            "items": list(items.values()),
            "total": len(items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get items: {str(e)}")


@router.delete("/items/{item_id}")
async def remove_plaid_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    plaid_client: PlaidClient = Depends(),
    account_service: AccountService = Depends()
):
    """Remove a Plaid item and disable associated accounts."""
    try:
        # Get all accounts for this item
        accounts = await account_service.get_user_accounts(
            user_id=current_user["sub"],
            filters={"plaid_item_id": item_id}
        )
        
        if not accounts:
            raise HTTPException(status_code=404, detail="Plaid item not found")
        
        # Disable accounts (don't delete to preserve transaction history)
        disabled_accounts = []
        for account in accounts:
            updated_account = await account_service.update_account_sync_status(
                account_id=account.id,
                user_id=current_user["sub"],
                status="stopped",
                error_message="Item removed by user"
            )
            disabled_accounts.append(updated_account.id)
        
        # In a real implementation, you would also call Plaid's /item/remove endpoint
        # await plaid_client.remove_item(access_token)
        
        return {
            "message": f"Plaid item removed and {len(disabled_accounts)} accounts disabled",
            "item_id": item_id,
            "disabled_accounts": disabled_accounts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove item: {str(e)}")


# Webhook Management
@router.post("/webhooks")
async def handle_plaid_webhook(
    request: Request,
    plaid_client: PlaidClient = Depends()
):
    """Handle Plaid webhook notifications."""
    try:
        # Get webhook payload
        webhook_data = await request.json()
        
        webhook_type = webhook_data.get("webhook_type")
        webhook_code = webhook_data.get("webhook_code")
        item_id = webhook_data.get("item_id")
        
        # Verify webhook (in production, you'd verify the webhook signature)
        
        # Process webhook based on type
        if webhook_type == "TRANSACTIONS":
            if webhook_code in ["INITIAL_UPDATE", "HISTORICAL_UPDATE", "DEFAULT_UPDATE"]:
                # Queue transaction sync for this item
                # In a real implementation, you'd queue a background job
                print(f"Queuing transaction sync for item {item_id}")
                
        elif webhook_type == "ITEM":
            if webhook_code == "ERROR":
                # Handle item errors
                error = webhook_data.get("error", {})
                print(f"Item error for {item_id}: {error}")
                
        elif webhook_type == "AUTH":
            if webhook_code == "AUTOMATICALLY_VERIFIED":
                # Handle account verification
                print(f"Account automatically verified for item {item_id}")
        
        # Return success response
        return {"acknowledged": True}
        
    except Exception as e:
        # Log error but return success to avoid webhook retries
        print(f"Webhook processing error: {e}")
        return {"acknowledged": True, "error": str(e)}


# Health and Status
@router.get("/health")
async def plaid_service_health(
    plaid_client: PlaidClient = Depends()
):
    """Check Plaid service health."""
    try:
        # Test Plaid connectivity
        # In a real implementation, you might call a simple Plaid endpoint
        
        return {
            "status": "healthy",
            "service": "plaid",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "plaid_environment": "sandbox"  # Would be from config
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "plaid",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Configuration and Settings
@router.get("/config")
async def get_plaid_config(
    current_user: dict = Depends(get_current_user)
):
    """Get Plaid configuration for frontend."""
    return {
        "environment": "sandbox",  # Would be from config
        "public_key": "public_key_placeholder",  # Not needed for Link Token
        "products": ["transactions", "accounts", "identity"],
        "country_codes": ["US"],
        "client_name": "Faithful Finances"
    }