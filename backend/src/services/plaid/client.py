"""Plaid API client with error handling and rate limiting."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.identity_get_request import IdentityGetRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.webhook_update_acknowledged_request import WebhookUpdateAcknowledgedRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.exceptions import ApiException
import structlog

from src.config import settings
from src.exceptions import PlaidError

logger = structlog.get_logger(__name__)


class PlaidClient:
    """Enhanced Plaid API client with error handling, retries, and monitoring."""
    
    def __init__(self):
        # Configure Plaid client
        configuration = Configuration(
            host=self._get_plaid_host(),
            api_key={
                'clientId': settings.PLAID_CLIENT_ID,
                'secret': settings.PLAID_SECRET
            }
        )
        
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.request_count = 0
        self.daily_request_count = 0
        self.daily_request_reset = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Products configuration
        self.products = settings.plaid_products_list
        self.country_codes = settings.plaid_country_codes_list
    
    def _get_plaid_host(self):
        """Get Plaid host based on environment."""
        env_mapping = {
            'sandbox': 'https://sandbox-api.plaid.com',
            'development': 'https://development-api.plaid.com',
            'production': 'https://production-api.plaid.com'
        }
        return env_mapping.get(settings.PLAID_ENV, 'https://sandbox-api.plaid.com')
    
    async def _handle_rate_limiting(self):
        """Handle Plaid rate limiting."""
        current_time = time.time()
        
        # Reset daily counter if needed
        now = datetime.now()
        if now >= self.daily_request_reset + timedelta(days=1):
            self.daily_request_count = 0
            self.daily_request_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Reset per-second counter
        if current_time - self.last_request_time >= 1:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check rate limits
        # Plaid allows 4 requests per second, 1000 per day for sandbox
        if self.request_count >= 4:
            await asyncio.sleep(1)
            self.request_count = 0
        
        if self.daily_request_count >= 1000 and settings.PLAID_ENV == 'sandbox':
            logger.warning("Daily Plaid API limit approaching", count=self.daily_request_count)
        
        self.request_count += 1
        self.daily_request_count += 1
    
    def _handle_plaid_error(self, e: ApiException, operation: str) -> None:
        """Handle and log Plaid API errors."""
        error_details = {
            "operation": operation,
            "status": e.status,
            "reason": e.reason,
            "body": e.body
        }
        
        try:
            # Parse error response if possible
            if e.body:
                import json
                error_body = json.loads(e.body)
                error_details.update({
                    "error_type": error_body.get("error_type"),
                    "error_code": error_body.get("error_code"),
                    "error_message": error_body.get("error_message"),
                    "display_message": error_body.get("display_message"),
                    "request_id": error_body.get("request_id")
                })
        except:
            pass
        
        logger.error("Plaid API error", **error_details)
        
        # Map common errors
        if e.status == 400:
            raise PlaidError(f"Invalid request: {error_details.get('error_message', str(e))}", error_details)
        elif e.status == 401:
            raise PlaidError("Authentication failed", error_details)
        elif e.status == 404:
            raise PlaidError("Resource not found", error_details)
        elif e.status == 429:
            raise PlaidError("Rate limit exceeded", error_details)
        elif e.status >= 500:
            raise PlaidError("Plaid service unavailable", error_details)
        else:
            raise PlaidError(f"Plaid API error: {str(e)}", error_details)
    
    async def _make_request(self, operation: str, func, *args, **kwargs):
        """Make Plaid API request with error handling and rate limiting."""
        await self._handle_rate_limiting()
        
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            response_time = (time.time() - start_time) * 1000
            
            logger.debug(
                "Plaid API request successful",
                operation=operation,
                response_time_ms=round(response_time, 2)
            )
            
            return result
            
        except ApiException as e:
            self._handle_plaid_error(e, operation)
    
    # Link Token operations
    async def create_link_token(
        self,
        user_id: str,
        client_name: str,
        country_codes: List[str] = None,
        language: str = "en",
        webhook: str = None,
        account_filters: Dict = None
    ) -> Dict[str, Any]:
        """Create Link token for Plaid Link initialization."""
        try:
            request = LinkTokenCreateRequest(
                products=self.products,
                client_name=client_name,
                country_codes=country_codes or self.country_codes,
                language=language,
                user={
                    'client_user_id': user_id
                }
            )
            
            if webhook:
                request['webhook'] = webhook
            
            if account_filters:
                request['account_filters'] = account_filters
            
            response = await self._make_request(
                "create_link_token",
                self.client.link_token_create,
                request
            )
            
            logger.info("Link token created", user_id=user_id)
            
            return {
                "link_token": response['link_token'],
                "expiration": response['expiration'],
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to create link token", user_id=user_id, error=str(e))
            raise
    
    async def exchange_public_token(
        self,
        public_token: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Exchange public token for access token."""
        try:
            request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            
            response = await self._make_request(
                "exchange_public_token",
                self.client.item_public_token_exchange,
                request
            )
            
            logger.info("Public token exchanged", tenant_id=tenant_id)
            
            return {
                "access_token": response['access_token'],
                "item_id": response['item_id'],
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to exchange public token", tenant_id=tenant_id, error=str(e))
            raise
    
    # Account operations
    async def get_accounts(self, access_token: str) -> Dict[str, Any]:
        """Get account information."""
        try:
            request = AccountsGetRequest(access_token=access_token)
            
            response = await self._make_request(
                "get_accounts",
                self.client.accounts_get,
                request
            )
            
            return {
                "accounts": response['accounts'],
                "item": response['item'],
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get accounts", error=str(e))
            raise
    
    async def get_account_balances(self, access_token: str) -> Dict[str, Any]:
        """Get real-time account balances."""
        try:
            request = AccountsBalanceGetRequest(access_token=access_token)
            
            response = await self._make_request(
                "get_account_balances",
                self.client.accounts_balance_get,
                request
            )
            
            return {
                "accounts": response['accounts'],
                "item": response['item'],
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get account balances", error=str(e))
            raise
    
    # Transaction operations
    async def get_transactions(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        account_ids: List[str] = None,
        count: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get transactions for date range."""
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                count=count,
                offset=offset
            )
            
            if account_ids:
                request['account_ids'] = account_ids
            
            response = await self._make_request(
                "get_transactions",
                self.client.transactions_get,
                request
            )
            
            return {
                "transactions": response['transactions'],
                "accounts": response['accounts'],
                "total_transactions": response['total_transactions'],
                "item": response['item'],
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get transactions", 
                        start_date=start_date,
                        end_date=end_date,
                        error=str(e))
            raise
    
    # Identity operations
    async def get_identity(self, access_token: str) -> Dict[str, Any]:
        """Get identity information."""
        try:
            request = IdentityGetRequest(access_token=access_token)
            
            response = await self._make_request(
                "get_identity",
                self.client.identity_get,
                request
            )
            
            return {
                "accounts": response['accounts'],
                "item": response['item'],
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get identity", error=str(e))
            raise
    
    # Auth operations
    async def get_auth(self, access_token: str) -> Dict[str, Any]:
        """Get auth information (account and routing numbers)."""
        try:
            request = AuthGetRequest(access_token=access_token)
            
            response = await self._make_request(
                "get_auth",
                self.client.auth_get,
                request
            )
            
            return {
                "accounts": response['accounts'],
                "numbers": response['numbers'],
                "item": response['item'],
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get auth", error=str(e))
            raise
    
    # Item operations
    async def get_item(self, access_token: str) -> Dict[str, Any]:
        """Get item information."""
        try:
            request = ItemGetRequest(access_token=access_token)
            
            response = await self._make_request(
                "get_item",
                self.client.item_get,
                request
            )
            
            return {
                "item": response['item'],
                "status": response.get('status'),
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get item", error=str(e))
            raise
    
    async def remove_item(self, access_token: str) -> Dict[str, Any]:
        """Remove item (disconnect account)."""
        try:
            request = ItemRemoveRequest(access_token=access_token)
            
            response = await self._make_request(
                "remove_item",
                self.client.item_remove,
                request
            )
            
            logger.info("Item removed")
            
            return {
                "removed": response.get('removed', True),
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to remove item", error=str(e))
            raise
    
    # Institution operations
    async def get_institutions(
        self,
        count: int = 50,
        offset: int = 0,
        country_codes: List[str] = None
    ) -> Dict[str, Any]:
        """Get institutions."""
        try:
            request = InstitutionsGetByIdRequest(
                institution_ids=[],  # Empty for get all
                country_codes=country_codes or self.country_codes,
                options={
                    'include_optional_metadata': True,
                    'include_status': True
                }
            )
            
            response = await self._make_request(
                "get_institutions",
                self.client.institutions_get,
                request
            )
            
            return {
                "institutions": response['institutions'],
                "total": response.get('total'),
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get institutions", error=str(e))
            raise
    
    async def get_institution_by_id(
        self,
        institution_id: str,
        country_codes: List[str] = None
    ) -> Dict[str, Any]:
        """Get institution by ID."""
        try:
            request = InstitutionsGetByIdRequest(
                institution_ids=[institution_id],
                country_codes=country_codes or self.country_codes,
                options={
                    'include_optional_metadata': True,
                    'include_status': True
                }
            )
            
            response = await self._make_request(
                "get_institution_by_id",
                self.client.institutions_get_by_id,
                request
            )
            
            return {
                "institution": response['institutions'][0] if response['institutions'] else None,
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to get institution", institution_id=institution_id, error=str(e))
            raise
    
    # Webhook operations
    async def acknowledge_webhook(
        self,
        webhook_code: str,
        webhook_type: str
    ) -> Dict[str, Any]:
        """Acknowledge webhook."""
        try:
            request = WebhookUpdateAcknowledgedRequest(
                webhook_code=webhook_code,
                webhook_type=webhook_type
            )
            
            response = await self._make_request(
                "acknowledge_webhook",
                self.client.webhook_update_acknowledged,
                request
            )
            
            return {
                "acknowledged": True,
                "request_id": response['request_id']
            }
            
        except Exception as e:
            logger.error("Failed to acknowledge webhook", 
                        webhook_code=webhook_code,
                        webhook_type=webhook_type,
                        error=str(e))
            raise
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Perform Plaid API health check."""
        health_status = {
            "service": "plaid",
            "status": "unhealthy",
            "details": {}
        }
        
        try:
            start_time = time.time()
            
            # Simple API call to test connectivity
            # Get institutions list with minimal data
            response = await self.get_institutions(count=1)
            
            response_time = (time.time() - start_time) * 1000
            
            health_status.update({
                "status": "healthy",
                "details": {
                    "environment": settings.PLAID_ENV,
                    "products": self.products,
                    "country_codes": self.country_codes,
                    "response_time_ms": round(response_time, 2),
                    "daily_requests": self.daily_request_count,
                    "institutions_available": len(response.get("institutions", []))
                }
            })
            
        except Exception as e:
            health_status["details"]["error"] = str(e)
            logger.error("Plaid health check failed", error=str(e))
        
        return health_status


# Global Plaid client instance
_plaid_client: Optional[PlaidClient] = None


def get_plaid_client() -> PlaidClient:
    """Get or create Plaid client instance."""
    global _plaid_client
    
    if _plaid_client is None:
        _plaid_client = PlaidClient()
    
    return _plaid_client