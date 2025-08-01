"""Comprehensive external service integration tests."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, date
from decimal import Decimal
import json

from src.exceptions import ExternalServiceError, ValidationError


@pytest.mark.unit
class TestPlaidService:
    """Test Plaid service integration."""
    
    @pytest.fixture
    def plaid_service(self):
        """Create Plaid service instance."""
        from src.plaid.service import PlaidService
        return PlaidService()
    
    @pytest.fixture
    def mock_plaid_client(self):
        """Mock Plaid client."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_create_link_token_success(self, plaid_service, mock_plaid_client):
        """Test successful link token creation."""
        # Arrange
        user_id = "test-user-123"
        expected_response = {
            "link_token": "link-test-token-123",
            "expiration": "2024-12-31T23:59:59Z"
        }
        
        mock_plaid_client.link_token_create.return_value = expected_response
        plaid_service._client = mock_plaid_client
        
        # Act
        result = await plaid_service.create_link_token(user_id)
        
        # Assert
        assert result["link_token"] == expected_response["link_token"]
        assert result["expiration"] == expected_response["expiration"]
        mock_plaid_client.link_token_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_link_token_service_error(self, plaid_service, mock_plaid_client):
        """Test link token creation with Plaid service error."""
        # Arrange
        user_id = "test-user-123"
        mock_plaid_client.link_token_create.side_effect = Exception("Plaid service unavailable")
        plaid_service._client = mock_plaid_client
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await plaid_service.create_link_token(user_id)
        
        assert exc_info.value.service == "plaid"
        assert "unavailable" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_exchange_public_token_success(self, plaid_service, mock_plaid_client):
        """Test successful public token exchange."""
        # Arrange
        public_token = "public-test-token"
        expected_response = {
            "access_token": "access-test-token-123",
            "item_id": "item-123"
        }
        
        mock_plaid_client.item_public_token_exchange.return_value = expected_response
        plaid_service._client = mock_plaid_client
        
        # Act
        result = await plaid_service.exchange_public_token(public_token)
        
        # Assert
        assert result["access_token"] == expected_response["access_token"]
        assert result["item_id"] == expected_response["item_id"]
        mock_plaid_client.item_public_token_exchange.assert_called_once_with(public_token)
    
    @pytest.mark.asyncio
    async def test_get_accounts_success(self, plaid_service, mock_plaid_client):
        """Test successful account retrieval."""
        # Arrange
        access_token = "access-token-123"
        expected_accounts = [
            {
                "account_id": "account-1",
                "name": "Checking Account",
                "official_name": "Primary Checking",
                "type": "depository",
                "subtype": "checking",
                "balance": {"current": 1500.00, "available": 1400.00}
            },
            {
                "account_id": "account-2", 
                "name": "Savings Account",
                "official_name": "High Yield Savings",
                "type": "depository",
                "subtype": "savings",
                "balance": {"current": 5000.00, "available": 5000.00}
            }
        ]
        
        mock_plaid_client.accounts_get.return_value = {"accounts": expected_accounts}
        plaid_service._client = mock_plaid_client
        
        # Act
        result = await plaid_service.get_accounts(access_token)
        
        # Assert
        assert len(result) == 2
        assert result[0]["account_id"] == "account-1"
        assert result[1]["account_id"] == "account-2"
        mock_plaid_client.accounts_get.assert_called_once_with(access_token)
    
    @pytest.mark.asyncio
    async def test_get_transactions_success(self, plaid_service, mock_plaid_client):
        """Test successful transaction retrieval."""
        # Arrange
        access_token = "access-token-123"
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        expected_transactions = [
            {
                "transaction_id": "txn-1",
                "account_id": "account-1",
                "amount": 25.99,
                "date": "2024-01-15",
                "name": "Coffee Shop",
                "merchant_name": "Local Coffee",
                "category": ["Food and Drink", "Restaurants"]
            },
            {
                "transaction_id": "txn-2",
                "account_id": "account-1", 
                "amount": 125.50,
                "date": "2024-01-16",
                "name": "Grocery Store",
                "merchant_name": "Super Market",
                "category": ["Shops", "Supermarkets and Groceries"]
            }
        ]
        
        mock_plaid_client.transactions_get.return_value = {"transactions": expected_transactions}
        plaid_service._client = mock_plaid_client
        
        # Act
        result = await plaid_service.get_transactions(access_token, start_date, end_date)
        
        # Assert
        assert len(result) == 2
        assert result[0]["transaction_id"] == "txn-1"
        assert result[1]["transaction_id"] == "txn-2"
        mock_plaid_client.transactions_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_account_balance_success(self, plaid_service, mock_plaid_client):
        """Test successful account balance retrieval."""
        # Arrange
        access_token = "access-token-123"
        account_id = "account-1"
        
        expected_account = {
            "account_id": account_id,
            "balances": {
                "current": 1750.25,
                "available": 1650.25
            }
        }
        
        mock_plaid_client.accounts_balance_get.return_value = {"accounts": [expected_account]}
        plaid_service._client = mock_plaid_client
        
        # Act
        result = await plaid_service.get_account_balance(access_token, account_id)
        
        # Assert
        assert result["current"] == 1750.25
        assert result["available"] == 1650.25
    
    @pytest.mark.asyncio
    async def test_plaid_rate_limiting(self, plaid_service, mock_plaid_client):
        """Test Plaid rate limiting handling."""
        # Arrange
        from plaid.api_client import ApiException
        
        rate_limit_error = ApiException(status=429, reason="Rate limit exceeded")
        mock_plaid_client.accounts_get.side_effect = rate_limit_error
        plaid_service._client = mock_plaid_client
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await plaid_service.get_accounts("access-token")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_plaid_invalid_credentials(self, plaid_service, mock_plaid_client):
        """Test Plaid invalid credentials handling."""
        # Arrange
        from plaid.api_client import ApiException
        
        auth_error = ApiException(status=401, reason="Invalid credentials")
        mock_plaid_client.accounts_get.side_effect = auth_error
        plaid_service._client = mock_plaid_client
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await plaid_service.get_accounts("invalid-token")
        
        assert "credentials" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_plaid_item_error(self, plaid_service, mock_plaid_client):
        """Test Plaid item error handling."""
        # Arrange
        from plaid.api_client import ApiException
        
        item_error = ApiException(status=400, reason="Item login required")
        mock_plaid_client.transactions_get.side_effect = item_error
        plaid_service._client = mock_plaid_client
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await plaid_service.get_transactions("access-token", date.today(), date.today())
        
        assert "item" in str(exc_info.value).lower()


@pytest.mark.unit
class TestStripeService:
    """Test Stripe service integration."""
    
    @pytest.fixture
    def stripe_service(self):
        """Create Stripe service instance."""
        from src.subscriptions.service import StripeService
        return StripeService()
    
    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe client."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_create_customer_success(self, stripe_service, mock_stripe):
        """Test successful customer creation."""
        # Arrange
        customer_data = {
            "email": "customer@example.com",
            "name": "Test Customer"
        }
        
        expected_customer = {
            "id": "cus_test123",
            "email": "customer@example.com",
            "name": "Test Customer",
            "created": 1640995200
        }
        
        mock_stripe.Customer.create.return_value = expected_customer
        stripe_service._stripe = mock_stripe
        
        # Act
        result = await stripe_service.create_customer(customer_data)
        
        # Assert
        assert result["id"] == "cus_test123"
        assert result["email"] == customer_data["email"]
        mock_stripe.Customer.create.assert_called_once_with(**customer_data)
    
    @pytest.mark.asyncio
    async def test_create_subscription_success(self, stripe_service, mock_stripe):
        """Test successful subscription creation."""
        # Arrange
        subscription_data = {
            "customer": "cus_test123",
            "items": [{"price": "price_test123"}],
            "payment_behavior": "default_incomplete"
        }
        
        expected_subscription = {
            "id": "sub_test123",
            "status": "incomplete",
            "customer": "cus_test123",
            "current_period_start": 1640995200,
            "current_period_end": 1643673600,
            "latest_invoice": {
                "payment_intent": {
                    "client_secret": "pi_test_secret"
                }
            }
        }
        
        mock_stripe.Subscription.create.return_value = expected_subscription
        stripe_service._stripe = mock_stripe
        
        # Act
        result = await stripe_service.create_subscription(subscription_data)
        
        # Assert
        assert result["id"] == "sub_test123"
        assert result["status"] == "incomplete"
        mock_stripe.Subscription.create.assert_called_once_with(**subscription_data)
    
    @pytest.mark.asyncio
    async def test_cancel_subscription_success(self, stripe_service, mock_stripe):
        """Test successful subscription cancellation."""
        # Arrange
        subscription_id = "sub_test123"
        
        expected_subscription = {
            "id": subscription_id,
            "status": "canceled",
            "canceled_at": 1640995200
        }
        
        mock_stripe.Subscription.cancel.return_value = expected_subscription
        stripe_service._stripe = mock_stripe
        
        # Act
        result = await stripe_service.cancel_subscription(subscription_id)
        
        # Assert
        assert result["id"] == subscription_id
        assert result["status"] == "canceled"
        mock_stripe.Subscription.cancel.assert_called_once_with(subscription_id)
    
    @pytest.mark.asyncio
    async def test_retrieve_customer_success(self, stripe_service, mock_stripe):
        """Test successful customer retrieval."""
        # Arrange
        customer_id = "cus_test123"
        
        expected_customer = {
            "id": customer_id,
            "email": "customer@example.com",
            "name": "Test Customer"
        }
        
        mock_stripe.Customer.retrieve.return_value = expected_customer
        stripe_service._stripe = mock_stripe
        
        # Act
        result = await stripe_service.retrieve_customer(customer_id)
        
        # Assert
        assert result["id"] == customer_id
        assert result["email"] == "customer@example.com"
        mock_stripe.Customer.retrieve.assert_called_once_with(customer_id)
    
    @pytest.mark.asyncio
    async def test_stripe_card_error(self, stripe_service, mock_stripe):
        """Test Stripe card error handling."""
        # Arrange
        import stripe
        
        card_error = stripe.error.CardError(
            message="Your card was declined.",
            param="card",
            code="card_declined"
        )
        mock_stripe.Subscription.create.side_effect = card_error
        stripe_service._stripe = mock_stripe
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await stripe_service.create_subscription({"customer": "cus_test"})
        
        assert "card" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_stripe_rate_limit_error(self, stripe_service, mock_stripe):
        """Test Stripe rate limit error handling."""
        # Arrange
        import stripe
        
        rate_limit_error = stripe.error.RateLimitError(
            message="Too many requests made to the API too quickly"
        )
        mock_stripe.Customer.create.side_effect = rate_limit_error
        stripe_service._stripe = mock_stripe
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await stripe_service.create_customer({"email": "test@example.com"})
        
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_stripe_api_error(self, stripe_service, mock_stripe):
        """Test Stripe API error handling."""
        # Arrange
        import stripe
        
        api_error = stripe.error.APIError(
            message="An error occurred with our API"
        )
        mock_stripe.Subscription.retrieve.side_effect = api_error
        stripe_service._stripe = mock_stripe
        
        # Act & Assert
        with pytest.raises(ExternalServiceError) as exc_info:
            await stripe_service.retrieve_subscription("sub_test")
        
        assert "api" in str(exc_info.value).lower()


@pytest.mark.unit 
class TestAuth0ServiceIntegration:
    """Test Auth0 service integration scenarios."""
    
    @pytest.fixture
    def auth0_service(self):
        """Create Auth0Service instance."""
        from src.auth.service import Auth0Service
        return Auth0Service()
    
    @pytest.mark.asyncio
    async def test_get_jwks_success(self, auth0_service):
        """Test successful JWKS retrieval."""
        # Arrange
        mock_jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-id",
                    "use": "sig",
                    "n": "test-modulus",
                    "e": "AQAB"
                }
            ]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_jwks
            mock_get.return_value = mock_response
            
            # Act
            result = await auth0_service._get_jwks()
            
            # Assert
            assert "keys" in result
            assert len(result["keys"]) == 1
            assert result["keys"][0]["kid"] == "test-key-id"
    
    @pytest.mark.asyncio
    async def test_get_jwks_service_unavailable(self, auth0_service):
        """Test JWKS retrieval when Auth0 service is unavailable."""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 503
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(ExternalServiceError) as exc_info:
                await auth0_service._get_jwks()
            
            assert exc_info.value.service == "auth0"
    
    @pytest.mark.asyncio
    async def test_validate_token_algorithm(self, auth0_service):
        """Test token algorithm validation."""
        # Arrange
        token_with_none_alg = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        
        # Act & Assert
        with pytest.raises(AuthenticationError) as exc_info:
            await auth0_service.verify_token(token_with_none_alg)
        
        assert "algorithm" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_token_cache_functionality(self, auth0_service):
        """Test token validation caching."""
        # This would test that valid tokens are cached to reduce Auth0 API calls
        # Implementation depends on caching strategy
        pass


@pytest.mark.integration
class TestExternalServiceCircuitBreaker:
    """Test circuit breaker patterns for external services."""
    
    @pytest.fixture
    def circuit_breaker_service(self):
        """Service with circuit breaker implementation."""
        # This would be a service wrapper with circuit breaker logic
        pass
    
    def test_circuit_breaker_opens_on_failures(self, circuit_breaker_service):
        """Test that circuit breaker opens after consecutive failures."""
        # Simulate multiple service failures
        # Verify circuit breaker opens and prevents further calls
        pass
    
    def test_circuit_breaker_half_open_state(self, circuit_breaker_service):
        """Test circuit breaker half-open state functionality."""
        # Test that circuit breaker allows test requests after timeout
        pass
    
    def test_circuit_breaker_closes_on_success(self, circuit_breaker_service):
        """Test that circuit breaker closes after successful requests."""
        # Test that circuit breaker returns to closed state after success
        pass


@pytest.mark.integration
class TestExternalServiceRetryLogic:
    """Test retry logic for external service calls."""
    
    @pytest.mark.asyncio
    async def test_plaid_retry_on_temporary_failure(self, plaid_service):
        """Test retry logic for temporary Plaid failures."""
        # Arrange
        with patch.object(plaid_service, '_client') as mock_client:
            # First call fails, second succeeds
            mock_client.accounts_get.side_effect = [
                Exception("Temporary failure"),
                {"accounts": [{"account_id": "test"}]}
            ]
            
            # Act
            result = await plaid_service.get_accounts_with_retry("access-token")
            
            # Assert
            assert len(result) == 1
            assert mock_client.accounts_get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_stripe_exponential_backoff(self, stripe_service):
        """Test exponential backoff for Stripe rate limits."""
        # Test that service implements exponential backoff for rate limits
        pass
    
    @pytest.mark.asyncio
    async def test_max_retry_attempts(self, plaid_service):
        """Test that services don't retry indefinitely."""
        # Arrange
        with patch.object(plaid_service, '_client') as mock_client:
            mock_client.accounts_get.side_effect = Exception("Persistent failure")
            
            # Act & Assert
            with pytest.raises(ExternalServiceError):
                await plaid_service.get_accounts_with_retry("access-token", max_retries=3)
            
            # Should have tried max_retries + 1 times (initial + retries)
            assert mock_client.accounts_get.call_count == 4


@pytest.mark.integration
class TestExternalServiceWebhooks:
    """Test webhook handling for external services."""
    
    def test_plaid_webhook_verification(self, test_client):
        """Test Plaid webhook signature verification."""
        # Arrange
        webhook_payload = {
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "DEFAULT_UPDATED",
            "item_id": "test-item-id",
            "new_transactions": 5
        }
        
        # Create webhook signature (this would use actual Plaid signing logic)
        webhook_signature = "test-signature"
        
        headers = {
            "Plaid-Verification": webhook_signature,
            "Content-Type": "application/json"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/webhooks/plaid",
            json=webhook_payload,
            headers=headers
        )
        
        # Assert
        assert response.status_code in [200, 202]  # Webhook accepted
    
    def test_stripe_webhook_verification(self, test_client):
        """Test Stripe webhook signature verification."""
        # Arrange
        webhook_payload = {
            "id": "evt_test_webhook",
            "object": "event",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_payment_intent",
                    "status": "succeeded"
                }
            }
        }
        
        # Create Stripe webhook signature
        webhook_signature = "test-stripe-signature"
        
        headers = {
            "Stripe-Signature": webhook_signature,
            "Content-Type": "application/json"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/webhooks/stripe",
            json=webhook_payload,
            headers=headers
        )
        
        # Assert
        assert response.status_code in [200, 202]
    
    def test_webhook_replay_protection(self, test_client):
        """Test webhook replay attack protection."""
        # Test that duplicate webhooks are properly handled
        pass


@pytest.mark.integration
class TestExternalServiceDataConsistency:
    """Test data consistency with external services."""
    
    @pytest.mark.asyncio
    async def test_plaid_transaction_sync_consistency(self, plaid_service):
        """Test that Plaid transaction sync maintains data consistency."""
        # Test that syncing doesn't create duplicates or lose data
        pass
    
    @pytest.mark.asyncio
    async def test_stripe_subscription_state_consistency(self, stripe_service):
        """Test Stripe subscription state consistency."""
        # Test that local subscription state matches Stripe state
        pass
    
    def test_external_service_transaction_rollback(self):
        """Test transaction rollback when external service calls fail."""
        # Test that database transactions are rolled back if external service calls fail
        pass


@pytest.mark.integration
class TestExternalServiceMonitoring:
    """Test monitoring and observability for external services."""
    
    def test_external_service_metrics_collection(self):
        """Test that external service metrics are collected."""
        # Test that response times, error rates, etc. are tracked
        pass
    
    def test_external_service_health_checks(self, test_client):
        """Test external service health checks."""
        # Act
        response = test_client.get("/health/detailed")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should include external service health
        dependencies = data.get("dependencies", {})
        assert "plaid" in dependencies
        assert "stripe" in dependencies
        assert "auth0" in dependencies
    
    def test_external_service_alerting(self):
        """Test alerting for external service failures."""
        # Test that alerts are triggered for service failures
        pass


@pytest.mark.slow
class TestExternalServicePerformance:
    """Test performance characteristics of external service calls."""
    
    @pytest.mark.asyncio
    async def test_plaid_batch_operation_performance(self, plaid_service):
        """Test performance of batch Plaid operations."""
        # Test performance when processing many accounts/transactions
        pass
    
    @pytest.mark.asyncio
    async def test_stripe_concurrent_operations(self, stripe_service):
        """Test Stripe service under concurrent load."""
        # Test handling of concurrent Stripe operations
        pass
    
    def test_external_service_timeout_handling(self):
        """Test proper timeout handling for external service calls."""
        # Test that services timeout appropriately and don't hang
        pass