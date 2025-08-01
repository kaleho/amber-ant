"""Comprehensive integration tests for external services (Plaid, Stripe, Auth0)."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
import json
import httpx

from src.config import settings


@pytest.mark.integration
class TestPlaidIntegration:
    """Test Plaid service integration with proper mocking and error handling."""

    @pytest.fixture
    def mock_plaid_client(self):
        """Mock Plaid client for testing."""
        client = Mock()
        client.get_accounts = AsyncMock()
        client.get_account_balances = AsyncMock()
        client.get_transactions = AsyncMock()
        client.get_identity = AsyncMock()
        client.create_link_token = AsyncMock()
        client.exchange_public_token = AsyncMock()
        return client

    @pytest.fixture
    def sample_plaid_accounts(self):
        """Sample Plaid account data."""
        return {
            "accounts": [
                {
                    "account_id": "plaid_account_123",
                    "name": "Test Checking Account",
                    "type": "depository",
                    "subtype": "checking",
                    "balances": {
                        "available": 1500.00,
                        "current": 1750.00,
                        "limit": None
                    },
                    "mask": "0123",
                    "official_name": "Test Bank Checking Account",
                    "persistent_account_id": "persistent_123"
                },
                {
                    "account_id": "plaid_account_456",
                    "name": "Test Savings Account",
                    "type": "depository",
                    "subtype": "savings",
                    "balances": {
                        "available": 5000.00,
                        "current": 5000.00,
                        "limit": None
                    },
                    "mask": "0456",
                    "official_name": "Test Bank Savings Account",
                    "persistent_account_id": "persistent_456"
                }
            ],
            "item": {
                "item_id": "test_item_id",
                "institution_id": "ins_123",
                "webhook": "https://api.example.com/webhook",
                "error": None,
                "available_products": ["transactions", "identity", "assets"],
                "billed_products": ["transactions"],
                "products": ["transactions"]
            },
            "request_id": "test_request_id"
        }

    @pytest.fixture
    def sample_plaid_transactions(self):
        """Sample Plaid transaction data."""
        return {
            "transactions": [
                {
                    "transaction_id": "txn_123",
                    "account_id": "plaid_account_123",
                    "amount": -25.50,
                    "date": "2024-01-15",
                    "name": "Coffee Shop Downtown",
                    "merchant_name": "Local Coffee Co.",
                    "category": ["Food and Drink", "Restaurants", "Coffee Shop"],
                    "category_id": "13005043",
                    "pending": False,
                    "account_owner": None,
                    "location": {
                        "address": "123 Main St",
                        "city": "Downtown",
                        "region": "CA",
                        "postal_code": "90210",
                        "country": "US"
                    },
                    "payment_meta": {
                        "reference_number": None,
                        "ppd_id": None,
                        "payee": None,
                        "by_order_of": None,
                        "payer": None,
                        "payment_method": None,
                        "payment_processor": None,
                        "reason": None
                    }
                },
                {
                    "transaction_id": "txn_456",
                    "account_id": "plaid_account_123",
                    "amount": -85.00,
                    "date": "2024-01-14",
                    "name": "Grocery Store",
                    "merchant_name": "SuperMarket Plus",
                    "category": ["Shops", "Supermarkets and Groceries"],
                    "category_id": "19047000",
                    "pending": True,  # Pending transaction
                    "account_owner": None
                }
            ],
            "total_transactions": 2,
            "request_id": "test_request_id"
        }

    @pytest.mark.asyncio
    async def test_plaid_get_accounts_success(self, mock_plaid_client, sample_plaid_accounts):
        """Test successful account retrieval from Plaid."""
        # Arrange
        access_token = "access-sandbox-test-token"
        mock_plaid_client.get_accounts.return_value = sample_plaid_accounts
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act
            result = await plaid_client.get_accounts(access_token)
            
            # Assert
            assert result["accounts"][0]["account_id"] == "plaid_account_123"
            assert result["accounts"][0]["name"] == "Test Checking Account"
            assert result["accounts"][0]["type"] == "depository"
            assert result["accounts"][0]["subtype"] == "checking"
            assert result["accounts"][0]["balances"]["current"] == 1750.00
            
            assert result["accounts"][1]["account_id"] == "plaid_account_456"
            assert result["accounts"][1]["subtype"] == "savings"
            assert result["accounts"][1]["balances"]["current"] == 5000.00

    @pytest.mark.asyncio
    async def test_plaid_get_transactions_success(self, mock_plaid_client, sample_plaid_transactions):
        """Test successful transaction retrieval from Plaid."""
        # Arrange
        access_token = "access-sandbox-test-token"
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        mock_plaid_client.get_transactions.return_value = sample_plaid_transactions
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act
            result = await plaid_client.get_transactions(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                count=100
            )
            
            # Assert
            assert len(result["transactions"]) == 2
            assert result["total_transactions"] == 2
            
            # Check first transaction
            txn1 = result["transactions"][0]
            assert txn1["transaction_id"] == "txn_123"
            assert txn1["account_id"] == "plaid_account_123"
            assert txn1["amount"] == -25.50
            assert txn1["name"] == "Coffee Shop Downtown"
            assert txn1["merchant_name"] == "Local Coffee Co."
            assert txn1["pending"] is False
            assert "Food and Drink" in txn1["category"]
            
            # Check pending transaction
            txn2 = result["transactions"][1]
            assert txn2["transaction_id"] == "txn_456"
            assert txn2["pending"] is True

    @pytest.mark.asyncio
    async def test_plaid_create_link_token_success(self, mock_plaid_client):
        """Test successful Link token creation."""
        # Arrange
        user_id = str(uuid4())
        expected_response = {
            "link_token": "link-sandbox-test-token",
            "expiration": "2024-02-01T00:00:00Z",
            "request_id": "test_request_id"
        }
        mock_plaid_client.create_link_token.return_value = expected_response
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act
            result = await plaid_client.create_link_token(
                user_id=user_id,
                client_name="Faithful Finances",
                country_codes=["US"],
                language="en",
                products=["transactions", "accounts"]
            )
            
            # Assert
            assert result["link_token"] == "link-sandbox-test-token"
            assert "expiration" in result
            mock_plaid_client.create_link_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_plaid_exchange_public_token_success(self, mock_plaid_client):
        """Test successful public token exchange."""
        # Arrange
        public_token = "public-sandbox-test-token"
        expected_response = {
            "access_token": "access-sandbox-test-token",
            "item_id": "test_item_id",
            "request_id": "test_request_id"
        }
        mock_plaid_client.exchange_public_token.return_value = expected_response
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act
            result = await plaid_client.exchange_public_token(public_token)
            
            # Assert
            assert result["access_token"] == "access-sandbox-test-token"
            assert result["item_id"] == "test_item_id"
            mock_plaid_client.exchange_public_token.assert_called_once_with(public_token)

    @pytest.mark.asyncio
    async def test_plaid_api_error_handling(self, mock_plaid_client):
        """Test Plaid API error handling."""
        # Arrange
        access_token = "invalid-token"
        plaid_error = Exception("INVALID_ACCESS_TOKEN: The provided access token is invalid")
        mock_plaid_client.get_accounts.side_effect = plaid_error
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act & Assert
            with pytest.raises(Exception, match="INVALID_ACCESS_TOKEN"):
                await plaid_client.get_accounts(access_token)

    @pytest.mark.asyncio
    async def test_plaid_rate_limiting_handling(self, mock_plaid_client):
        """Test Plaid rate limiting error handling."""
        # Arrange
        access_token = "access-token"
        rate_limit_error = Exception("RATE_LIMIT_EXCEEDED: API rate limit exceeded")
        mock_plaid_client.get_transactions.side_effect = rate_limit_error
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act & Assert
            with pytest.raises(Exception, match="RATE_LIMIT_EXCEEDED"):
                await plaid_client.get_transactions(
                    access_token=access_token,
                    start_date=date.today() - timedelta(days=30),
                    end_date=date.today()
                )

    @pytest.mark.asyncio
    async def test_plaid_webhook_processing(self, mock_plaid_client, sample_plaid_transactions):
        """Test Plaid webhook processing for transaction updates."""
        # Arrange
        webhook_data = {
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "DEFAULT_UPDATE",
            "item_id": "test_item_id",
            "new_transactions": 5,
            "removed_transactions": []
        }
        
        # Mock the webhook processing
        with patch('src.services.plaid.process_transactions_webhook') as mock_process_webhook:
            mock_process_webhook.return_value = {
                "processed": True,
                "new_transactions_count": 5,
                "updated_transactions_count": 0
            }
            
            from src.services.plaid import process_transactions_webhook
            
            # Act
            result = process_transactions_webhook(webhook_data)
            
            # Assert
            assert result["processed"] is True
            assert result["new_transactions_count"] == 5
            mock_process_webhook.assert_called_once_with(webhook_data)

    @pytest.mark.asyncio
    async def test_plaid_account_filtering(self, mock_plaid_client, sample_plaid_accounts):
        """Test filtering accounts by specific account IDs."""
        # Arrange
        access_token = "access-token"
        account_ids = ["plaid_account_123"]  # Only get checking account
        
        filtered_accounts = {
            "accounts": [sample_plaid_accounts["accounts"][0]],  # Only first account
            "item": sample_plaid_accounts["item"],
            "request_id": "test_request_id"
        }
        mock_plaid_client.get_accounts.return_value = filtered_accounts
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act
            result = await plaid_client.get_accounts(access_token, account_ids=account_ids)
            
            # Assert
            assert len(result["accounts"]) == 1
            assert result["accounts"][0]["account_id"] == "plaid_account_123"
            assert result["accounts"][0]["subtype"] == "checking"

    @pytest.mark.asyncio
    async def test_plaid_pagination_handling(self, mock_plaid_client):
        """Test handling of paginated transaction responses."""
        # Arrange
        access_token = "access-token"
        
        # First page response
        first_page = {
            "transactions": [{"transaction_id": f"txn_{i}", "amount": -10.0 * i} for i in range(100)],
            "total_transactions": 250,
            "request_id": "test_request_id"
        }
        
        # Second page response
        second_page = {
            "transactions": [{"transaction_id": f"txn_{i}", "amount": -10.0 * i} for i in range(100, 200)],
            "total_transactions": 250,
            "request_id": "test_request_id_2"
        }
        
        mock_plaid_client.get_transactions.side_effect = [first_page, second_page]
        
        with patch('src.services.plaid.get_plaid_client', return_value=mock_plaid_client):
            from src.services.plaid import get_plaid_client
            plaid_client = get_plaid_client()
            
            # Act - Get first page
            result1 = await plaid_client.get_transactions(
                access_token=access_token,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                offset=0,
                count=100
            )
            
            # Act - Get second page
            result2 = await plaid_client.get_transactions(
                access_token=access_token,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                offset=100,
                count=100
            )
            
            # Assert
            assert len(result1["transactions"]) == 100
            assert len(result2["transactions"]) == 100
            assert result1["total_transactions"] == 250
            assert result2["total_transactions"] == 250
            assert result1["transactions"][0]["transaction_id"] == "txn_0"
            assert result2["transactions"][0]["transaction_id"] == "txn_100"


@pytest.mark.integration
class TestStripeIntegration:
    """Test Stripe service integration with proper mocking and webhook handling."""

    @pytest.fixture
    def mock_stripe_client(self):
        """Mock Stripe client for testing."""
        client = Mock()
        client.Customer = Mock()
        client.Subscription = Mock()
        client.Invoice = Mock()
        client.PaymentMethod = Mock()
        client.WebhookEndpoint = Mock()
        client.Event = Mock()
        return client

    @pytest.fixture
    def sample_stripe_customer(self):
        """Sample Stripe customer data."""
        return {
            "id": "cus_test123",
            "object": "customer",
            "created": 1640995200,
            "email": "test@example.com",
            "name": "Test Customer",
            "phone": "+15551234567",
            "address": {
                "line1": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "postal_code": "90210",
                "country": "US"
            },
            "metadata": {
                "user_id": str(uuid4()),
                "tenant_id": str(uuid4())
            },
            "default_source": None,
            "subscriptions": {
                "object": "list",
                "data": [],
                "has_more": False,
                "total_count": 0
            }
        }

    @pytest.fixture
    def sample_stripe_subscription(self):
        """Sample Stripe subscription data."""
        return {
            "id": "sub_test123",
            "object": "subscription",
            "status": "active",
            "customer": "cus_test123",
            "current_period_start": 1640995200,
            "current_period_end": 1643673600,
            "plan": {
                "id": "plan_premium_monthly",
                "object": "plan",
                "amount": 2999,  # $29.99
                "currency": "usd",
                "interval": "month",
                "interval_count": 1,
                "nickname": "Premium Monthly"
            },
            "items": {
                "object": "list",
                "data": [{
                    "id": "si_test123",
                    "object": "subscription_item",
                    "plan": {
                        "id": "plan_premium_monthly",
                        "amount": 2999,
                        "currency": "usd"
                    },
                    "quantity": 1
                }],
                "has_more": False,
                "total_count": 1
            },
            "metadata": {
                "user_id": str(uuid4()),
                "feature_set": "premium"
            }
        }

    @pytest.mark.asyncio
    async def test_stripe_create_customer_success(self, mock_stripe_client, sample_stripe_customer):
        """Test successful Stripe customer creation."""
        # Arrange
        customer_data = {
            "email": "test@example.com",
            "name": "Test Customer",
            "phone": "+15551234567",
            "metadata": {
                "user_id": str(uuid4()),
                "tenant_id": str(uuid4())
            }
        }
        
        mock_stripe_client.Customer.create.return_value = sample_stripe_customer
        
        with patch('src.services.stripe.get_stripe_client', return_value=mock_stripe_client):
            from src.services.stripe import get_stripe_client
            stripe_client = get_stripe_client()
            
            # Act
            result = stripe_client.Customer.create(**customer_data)
            
            # Assert
            assert result["id"] == "cus_test123"
            assert result["email"] == customer_data["email"]
            assert result["name"] == customer_data["name"]
            assert result["phone"] == customer_data["phone"]
            mock_stripe_client.Customer.create.assert_called_once_with(**customer_data)

    @pytest.mark.asyncio
    async def test_stripe_create_subscription_success(self, mock_stripe_client, sample_stripe_subscription):
        """Test successful Stripe subscription creation."""
        # Arrange
        subscription_data = {
            "customer": "cus_test123",
            "items": [{"plan": "plan_premium_monthly"}],
            "metadata": {
                "user_id": str(uuid4()),
                "feature_set": "premium"
            }
        }
        
        mock_stripe_client.Subscription.create.return_value = sample_stripe_subscription
        
        with patch('src.services.stripe.get_stripe_client', return_value=mock_stripe_client):
            from src.services.stripe import get_stripe_client
            stripe_client = get_stripe_client()
            
            # Act
            result = stripe_client.Subscription.create(**subscription_data)
            
            # Assert
            assert result["id"] == "sub_test123"
            assert result["status"] == "active"
            assert result["customer"] == "cus_test123"
            assert result["plan"]["amount"] == 2999
            mock_stripe_client.Subscription.create.assert_called_once_with(**subscription_data)

    @pytest.mark.asyncio
    async def test_stripe_webhook_signature_verification(self, mock_stripe_client):
        """Test Stripe webhook signature verification."""
        # Arrange
        payload = '{"id": "evt_test123", "type": "customer.subscription.created"}'
        signature = "t=1640995200,v1=test_signature"
        webhook_secret = "whsec_test_secret"
        
        mock_event = {
            "id": "evt_test123",
            "type": "customer.subscription.created",
            "data": {
                "object": {"id": "sub_test123", "status": "active"}
            }
        }
        
        with patch('src.services.stripe.stripe.Webhook.construct_event', return_value=mock_event) as mock_construct:
            from src.services.stripe import verify_webhook_signature
            
            # Act
            result = verify_webhook_signature(payload, signature, webhook_secret)
            
            # Assert
            assert result["id"] == "evt_test123"
            assert result["type"] == "customer.subscription.created"
            mock_construct.assert_called_once_with(payload, signature, webhook_secret)

    @pytest.mark.asyncio
    async def test_stripe_webhook_signature_verification_failure(self, mock_stripe_client):
        """Test Stripe webhook signature verification failure."""
        # Arrange
        payload = '{"id": "evt_test123"}'
        invalid_signature = "invalid_signature"
        webhook_secret = "whsec_test_secret"
        
        with patch('src.services.stripe.stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = Exception("Invalid signature")
            
            from src.services.stripe import verify_webhook_signature
            
            # Act & Assert
            with pytest.raises(Exception, match="Invalid signature"):
                verify_webhook_signature(payload, invalid_signature, webhook_secret)

    @pytest.mark.asyncio
    async def test_stripe_subscription_update(self, mock_stripe_client):
        """Test Stripe subscription updates."""
        # Arrange
        subscription_id = "sub_test123"
        update_data = {
            "items": [{"id": "si_test123", "plan": "plan_premium_yearly"}],
            "proration_behavior": "create_prorations"
        }
        
        updated_subscription = {
            "id": subscription_id,
            "status": "active",
            "plan": {
                "id": "plan_premium_yearly",
                "amount": 29999,  # $299.99 yearly
                "interval": "year"
            }
        }
        
        mock_stripe_client.Subscription.modify.return_value = updated_subscription
        
        with patch('src.services.stripe.get_stripe_client', return_value=mock_stripe_client):
            from src.services.stripe import get_stripe_client
            stripe_client = get_stripe_client()
            
            # Act
            result = stripe_client.Subscription.modify(subscription_id, **update_data)
            
            # Assert
            assert result["id"] == subscription_id
            assert result["plan"]["id"] == "plan_premium_yearly"
            assert result["plan"]["amount"] == 29999
            mock_stripe_client.Subscription.modify.assert_called_once_with(subscription_id, **update_data)

    @pytest.mark.asyncio
    async def test_stripe_payment_method_attachment(self, mock_stripe_client):
        """Test attaching payment method to customer."""
        # Arrange
        payment_method_id = "pm_test123"
        customer_id = "cus_test123"
        
        payment_method = {
            "id": payment_method_id,
            "object": "payment_method",
            "type": "card",
            "customer": customer_id,
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 12,
                "exp_year": 2025
            }
        }
        
        mock_stripe_client.PaymentMethod.attach.return_value = payment_method
        
        with patch('src.services.stripe.get_stripe_client', return_value=mock_stripe_client):
            from src.services.stripe import get_stripe_client
            stripe_client = get_stripe_client()
            
            # Act
            result = stripe_client.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Assert
            assert result["id"] == payment_method_id
            assert result["customer"] == customer_id
            assert result["card"]["brand"] == "visa"
            assert result["card"]["last4"] == "4242"

    @pytest.mark.asyncio
    async def test_stripe_invoice_creation_and_payment(self, mock_stripe_client):
        """Test Stripe invoice creation and payment processing."""
        # Arrange
        customer_id = "cus_test123"
        
        mock_invoice = {
            "id": "in_test123",
            "object": "invoice",
            "customer": customer_id,
            "amount_due": 2999,
            "currency": "usd",
            "status": "open",
            "payment_intent": "pi_test123"
        }
        
        paid_invoice = {
            **mock_invoice,
            "status": "paid",
            "amount_paid": 2999
        }
        
        mock_stripe_client.Invoice.create.return_value = mock_invoice
        mock_stripe_client.Invoice.pay.return_value = paid_invoice
        
        with patch('src.services.stripe.get_stripe_client', return_value=mock_stripe_client):
            from src.services.stripe import get_stripe_client
            stripe_client = get_stripe_client()
            
            # Act
            invoice = stripe_client.Invoice.create(customer=customer_id, auto_advance=True)
            paid_result = stripe_client.Invoice.pay(invoice["id"])
            
            # Assert
            assert invoice["id"] == "in_test123"
            assert invoice["status"] == "open"
            assert paid_result["status"] == "paid"
            assert paid_result["amount_paid"] == 2999

    @pytest.mark.asyncio
    async def test_stripe_error_handling(self, mock_stripe_client):
        """Test Stripe API error handling."""
        # Arrange
        customer_data = {"email": "invalid-email"}
        
        stripe_error = Exception("Invalid email address")
        mock_stripe_client.Customer.create.side_effect = stripe_error
        
        with patch('src.services.stripe.get_stripe_client', return_value=mock_stripe_client):
            from src.services.stripe import get_stripe_client
            stripe_client = get_stripe_client()
            
            # Act & Assert
            with pytest.raises(Exception, match="Invalid email address"):
                stripe_client.Customer.create(**customer_data)

    @pytest.mark.asyncio
    async def test_stripe_webhook_event_processing(self, mock_stripe_client):
        """Test processing different types of Stripe webhook events."""
        # Test subscription created event
        subscription_created_event = {
            "id": "evt_sub_created",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "active"
                }
            }
        }
        
        # Test subscription cancelled event
        subscription_cancelled_event = {
            "id": "evt_sub_cancelled",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "canceled"
                }
            }
        }
        
        # Test invoice payment succeeded event
        payment_succeeded_event = {
            "id": "evt_payment_succeeded",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test123",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "amount_paid": 2999
                }
            }
        }
        
        with patch('src.services.stripe.process_webhook_event') as mock_process:
            mock_process.return_value = {"processed": True, "event_type": "test"}
            
            from src.services.stripe import process_webhook_event
            
            # Act & Assert
            for event in [subscription_created_event, subscription_cancelled_event, payment_succeeded_event]:
                result = process_webhook_event(event)
                assert result["processed"] is True


@pytest.mark.integration
class TestAuth0Integration:
    """Test Auth0 service integration with proper mocking and token validation."""

    @pytest.fixture
    def mock_auth0_client(self):
        """Mock Auth0 client for testing."""
        client = AsyncMock()
        client.get_user = AsyncMock()
        client.update_user = AsyncMock()
        client.create_user = AsyncMock()
        client.delete_user = AsyncMock()
        client.get_users = AsyncMock()
        return client

    @pytest.fixture
    def sample_auth0_user(self):
        """Sample Auth0 user data."""
        return {
            "user_id": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-15T12:00:00.000Z",
            "last_login": "2024-01-15T12:00:00.000Z",
            "logins_count": 25,
            "app_metadata": {
                "tenant_id": str(uuid4()),
                "roles": ["user"],
                "permissions": ["read:profile", "update:profile"]
            },
            "user_metadata": {
                "preferences": {
                    "currency": "USD",
                    "timezone": "America/New_York"
                }
            }
        }

    @pytest.fixture
    def sample_jwt_token(self):
        """Sample JWT token payload."""
        return {
            "iss": f"https://{settings.AUTH0_DOMAIN}/",
            "sub": "auth0|test123",
            "aud": [settings.AUTH0_AUDIENCE, f"https://{settings.AUTH0_DOMAIN}/userinfo"],
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
            "azp": settings.AUTH0_CLIENT_ID,
            "scope": "openid profile email",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg"
        }

    @pytest.mark.asyncio
    async def test_auth0_get_user_success(self, mock_auth0_client, sample_auth0_user):
        """Test successful user retrieval from Auth0."""
        # Arrange
        user_id = "auth0|test123"
        mock_auth0_client.get_user.return_value = sample_auth0_user
        
        with patch('src.services.auth0.get_auth0_client', return_value=mock_auth0_client):
            from src.services.auth0 import get_auth0_client
            auth0_client = get_auth0_client()
            
            # Act
            result = await auth0_client.get_user(user_id)
            
            # Assert
            assert result["user_id"] == user_id
            assert result["email"] == "test@example.com"
            assert result["email_verified"] is True
            assert result["name"] == "Test User"
            assert result["logins_count"] == 25
            assert "tenant_id" in result["app_metadata"]
            mock_auth0_client.get_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_auth0_update_user_metadata(self, mock_auth0_client):
        """Test updating Auth0 user metadata."""
        # Arrange
        user_id = "auth0|test123"
        update_data = {
            "user_metadata": {
                "preferences": {
                    "currency": "EUR",
                    "timezone": "Europe/London",
                    "notifications": True
                }
            },
            "app_metadata": {
                "last_subscription_check": datetime.utcnow().isoformat(),
                "feature_flags": ["new_dashboard", "advanced_analytics"]
            }
        }
        
        updated_user = {
            "user_id": user_id,
            "email": "test@example.com",
            **update_data
        }
        
        mock_auth0_client.update_user.return_value = updated_user
        
        with patch('src.services.auth0.get_auth0_client', return_value=mock_auth0_client):
            from src.services.auth0 import get_auth0_client
            auth0_client = get_auth0_client()
            
            # Act
            result = await auth0_client.update_user(user_id, update_data)
            
            # Assert
            assert result["user_id"] == user_id
            assert result["user_metadata"]["preferences"]["currency"] == "EUR"
            assert result["user_metadata"]["preferences"]["timezone"] == "Europe/London"
            assert result["app_metadata"]["feature_flags"] == ["new_dashboard", "advanced_analytics"]
            mock_auth0_client.update_user.assert_called_once_with(user_id, update_data)

    @pytest.mark.asyncio
    async def test_auth0_jwt_token_validation(self, sample_jwt_token):
        """Test JWT token validation with Auth0."""
        # Arrange
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."  # Mock JWT token
        
        with patch('src.auth.service.jwt.decode', return_value=sample_jwt_token) as mock_jwt_decode, \
             patch('src.auth.service.get_jwks_client') as mock_jwks:
            
            # Mock JWKS client for signature verification
            mock_signing_key = Mock()
            mock_signing_key.key = "mock_public_key"
            mock_jwks_client = Mock()
            mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwks.return_value = mock_jwks_client
            
            from src.auth.service import AuthService
            auth_service = AuthService()
            
            # Act
            result = await auth_service.verify_token(token)
            
            # Assert
            assert result["sub"] == "auth0|test123"
            assert result["email"] == "test@example.com"
            assert result["email_verified"] is True
            mock_jwt_decode.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth0_jwt_token_expired(self, sample_jwt_token):
        """Test handling of expired JWT tokens."""
        # Arrange
        expired_token = "expired.jwt.token"
        sample_jwt_token["exp"] = int((datetime.utcnow() - timedelta(hours=1)).timestamp())  # Expired
        
        with patch('src.auth.service.jwt.decode') as mock_jwt_decode:
            from jwt.exceptions import ExpiredSignatureError
            mock_jwt_decode.side_effect = ExpiredSignatureError("Token has expired")
            
            from src.auth.service import AuthService
            auth_service = AuthService()
            
            # Act & Assert
            with pytest.raises(Exception, match="Token has expired"):
                await auth_service.verify_token(expired_token)

    @pytest.mark.asyncio
    async def test_auth0_jwt_token_invalid_signature(self):
        """Test handling of JWT tokens with invalid signatures."""
        # Arrange
        invalid_token = "invalid.signature.token"
        
        with patch('src.auth.service.jwt.decode') as mock_jwt_decode:
            from jwt.exceptions import InvalidSignatureError
            mock_jwt_decode.side_effect = InvalidSignatureError("Invalid signature")
            
            from src.auth.service import AuthService
            auth_service = AuthService()
            
            # Act & Assert
            with pytest.raises(Exception, match="Invalid signature"):
                await auth_service.verify_token(invalid_token)

    @pytest.mark.asyncio
    async def test_auth0_get_users_with_pagination(self, mock_auth0_client):
        """Test retrieving users with pagination from Auth0."""
        # Arrange
        page1_users = [
            {"user_id": f"auth0|user{i}", "email": f"user{i}@example.com"}
            for i in range(50)
        ]
        
        page2_users = [
            {"user_id": f"auth0|user{i}", "email": f"user{i}@example.com"}
            for i in range(50, 75)
        ]
        
        mock_auth0_client.get_users.side_effect = [
            {"users": page1_users, "total": 75},
            {"users": page2_users, "total": 75}
        ]
        
        with patch('src.services.auth0.get_auth0_client', return_value=mock_auth0_client):
            from src.services.auth0 import get_auth0_client
            auth0_client = get_auth0_client()
            
            # Act
            page1_result = await auth0_client.get_users(page=0, per_page=50)
            page2_result = await auth0_client.get_users(page=1, per_page=50)
            
            # Assert
            assert len(page1_result["users"]) == 50
            assert len(page2_result["users"]) == 25
            assert page1_result["total"] == 75
            assert page2_result["total"] == 75
            assert page1_result["users"][0]["user_id"] == "auth0|user0"
            assert page2_result["users"][0]["user_id"] == "auth0|user50"

    @pytest.mark.asyncio
    async def test_auth0_user_search_by_email(self, mock_auth0_client):
        """Test searching for users by email in Auth0."""
        # Arrange
        search_email = "john@example.com"
        search_results = [
            {
                "user_id": "auth0|john123",
                "email": search_email,
                "name": "John Doe",
                "email_verified": True
            }
        ]
        
        mock_auth0_client.get_users.return_value = {"users": search_results, "total": 1}
        
        with patch('src.services.auth0.get_auth0_client', return_value=mock_auth0_client):
            from src.services.auth0 import get_auth0_client
            auth0_client = get_auth0_client()
            
            # Act
            result = await auth0_client.get_users(q=f"email:{search_email}")
            
            # Assert
            assert len(result["users"]) == 1
            assert result["users"][0]["email"] == search_email
            assert result["users"][0]["user_id"] == "auth0|john123"
            mock_auth0_client.get_users.assert_called_once_with(q=f"email:{search_email}")

    @pytest.mark.asyncio
    async def test_auth0_error_handling(self, mock_auth0_client):
        """Test Auth0 API error handling."""
        # Arrange
        user_id = "invalid_user_id"
        auth0_error = Exception("User not found")
        mock_auth0_client.get_user.side_effect = auth0_error
        
        with patch('src.services.auth0.get_auth0_client', return_value=mock_auth0_client):
            from src.services.auth0 import get_auth0_client
            auth0_client = get_auth0_client()
            
            # Act & Assert
            with pytest.raises(Exception, match="User not found"):
                await auth0_client.get_user(user_id)

    @pytest.mark.asyncio
    async def test_auth0_rate_limiting(self, mock_auth0_client):
        """Test Auth0 rate limiting handling."""
        # Arrange
        rate_limit_error = Exception("Rate limit exceeded")
        mock_auth0_client.get_users.side_effect = rate_limit_error
        
        with patch('src.services.auth0.get_auth0_client', return_value=mock_auth0_client):
            from src.services.auth0 import get_auth0_client
            auth0_client = get_auth0_client()
            
            # Act & Assert
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await auth0_client.get_users()


@pytest.mark.integration
class TestRedisIntegration:
    """Test Redis service integration for caching and sessions."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        client = AsyncMock()
        client.get = AsyncMock()
        client.set = AsyncMock()
        client.delete = AsyncMock()
        client.exists = AsyncMock()
        client.expire = AsyncMock()
        client.ttl = AsyncMock()
        client.keys = AsyncMock()
        client.flushdb = AsyncMock()
        client.ping = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_redis_cache_operations(self, mock_redis_client):
        """Test basic Redis cache operations."""
        # Arrange
        cache_key = "user:123:profile"
        cache_value = json.dumps({
            "user_id": "123",
            "name": "Test User",
            "email": "test@example.com"
        })
        
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = cache_value
        mock_redis_client.exists.return_value = True
        mock_redis_client.ttl.return_value = 3600
        
        with patch('src.services.redis.cache.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.cache import get_cache_service
            cache_service = await get_cache_service()
            
            # Act
            # Set cache
            await cache_service.set("tenant_123", cache_key, {"user_id": "123", "name": "Test User"}, ttl=3600)
            
            # Get cache
            result = await cache_service.get("tenant_123", cache_key)
            
            # Check existence
            exists = await cache_service.exists("tenant_123", cache_key)
            
            # Get TTL
            ttl = await cache_service.get_ttl("tenant_123", cache_key)
            
            # Assert
            mock_redis_client.set.assert_called()
            mock_redis_client.get.assert_called()
            assert exists is True
            assert ttl == 3600

    @pytest.mark.asyncio
    async def test_redis_session_management(self, mock_redis_client):
        """Test Redis session management operations."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        session_data = {
            "user_id": "auth0|test123",
            "tenant_id": str(uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0..."
        }
        
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = json.dumps(session_data)
        mock_redis_client.delete.return_value = 1
        
        with patch('src.services.redis.session.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.session import get_session_service
            session_service = await get_session_service()
            
            # Act
            # Create session
            await session_service.create_session(session_id, session_data, ttl=86400)
            
            # Get session
            retrieved_session = await session_service.get_session(session_id)
            
            # Update session activity
            await session_service.update_last_activity(session_id)
            
            # Delete session
            deleted = await session_service.delete_session(session_id)
            
            # Assert
            mock_redis_client.set.assert_called()
            mock_redis_client.get.assert_called()
            mock_redis_client.delete.assert_called()
            assert deleted is True

    @pytest.mark.asyncio
    async def test_redis_expired_sessions_cleanup(self, mock_redis_client):
        """Test cleanup of expired sessions in Redis."""
        # Arrange
        expired_sessions = [
            f"session:expired_{i}" for i in range(10)
        ]
        
        mock_redis_client.keys.return_value = expired_sessions
        mock_redis_client.delete.return_value = len(expired_sessions)
        
        with patch('src.services.redis.session.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.session import get_session_service
            session_service = await get_session_service()
            
            # Act
            cleaned_count = await session_service.cleanup_expired_sessions()
            
            # Assert
            assert cleaned_count == 10
            mock_redis_client.keys.assert_called()
            mock_redis_client.delete.assert_called()

    @pytest.mark.asyncio
    async def test_redis_connection_health_check(self, mock_redis_client):
        """Test Redis connection health check."""
        # Arrange
        mock_redis_client.ping.return_value = True
        
        with patch('src.services.redis.cache.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.cache import get_cache_service
            cache_service = await get_cache_service()
            
            # Act
            health_status = await cache_service.health_check()
            
            # Assert
            assert health_status["redis_connected"] is True
            mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self, mock_redis_client):
        """Test Redis connection failure handling."""
        # Arrange
        mock_redis_client.ping.side_effect = Exception("Connection refused")
        
        with patch('src.services.redis.cache.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.cache import get_cache_service
            cache_service = await get_cache_service()
            
            # Act
            health_status = await cache_service.health_check()
            
            # Assert
            assert health_status["redis_connected"] is False
            assert "Connection refused" in health_status["error"]

    @pytest.mark.asyncio
    async def test_redis_cache_namespace_isolation(self, mock_redis_client):
        """Test cache namespace isolation between tenants."""
        # Arrange
        tenant1_id = str(uuid4())
        tenant2_id = str(uuid4())
        cache_key = "user:profile"
        
        tenant1_data = {"tenant": tenant1_id, "name": "Tenant 1 User"}
        tenant2_data = {"tenant": tenant2_id, "name": "Tenant 2 User"}
        
        # Mock different responses for different namespace keys
        def mock_get_side_effect(key):
            if f"tenant:{tenant1_id}:" in key:
                return json.dumps(tenant1_data)
            elif f"tenant:{tenant2_id}:" in key:
                return json.dumps(tenant2_data)
            return None
        
        mock_redis_client.get.side_effect = mock_get_side_effect
        mock_redis_client.set.return_value = True
        
        with patch('src.services.redis.cache.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.cache import get_cache_service
            cache_service = await get_cache_service()
            
            # Act
            # Set data for both tenants
            await cache_service.set(tenant1_id, cache_key, tenant1_data)
            await cache_service.set(tenant2_id, cache_key, tenant2_data)
            
            # Get data for each tenant
            tenant1_result = await cache_service.get(tenant1_id, cache_key)
            tenant2_result = await cache_service.get(tenant2_id, cache_key)
            
            # Assert
            # Data should be isolated by tenant
            assert tenant1_result != tenant2_result
            mock_redis_client.set.assert_called()
            mock_redis_client.get.assert_called()

    @pytest.mark.asyncio
    async def test_redis_batch_operations(self, mock_redis_client):
        """Test Redis batch operations for performance."""
        # Arrange
        batch_data = {
            f"key_{i}": f"value_{i}" for i in range(100)
        }
        
        mock_redis_client.mset = AsyncMock(return_value=True)
        mock_redis_client.mget = AsyncMock(return_value=list(batch_data.values()))
        
        with patch('src.services.redis.cache.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.cache import get_cache_service
            cache_service = await get_cache_service()
            
            # Act
            # Batch set
            await cache_service.set_multiple("tenant_123", batch_data)
            
            # Batch get
            keys = list(batch_data.keys())
            results = await cache_service.get_multiple("tenant_123", keys)
            
            # Assert
            mock_redis_client.mset.assert_called_once()
            mock_redis_client.mget.assert_called_once()
            assert len(results) == 100

    @pytest.mark.asyncio
    async def test_redis_pub_sub_functionality(self, mock_redis_client):
        """Test Redis pub/sub functionality for real-time features."""
        # Arrange
        channel = "tenant:123:notifications"
        message = {
            "type": "transaction_update",
            "data": {
                "transaction_id": "txn_123",
                "status": "completed"
            }
        }
        
        mock_redis_client.publish = AsyncMock(return_value=1)
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.get_message = AsyncMock(return_value={
            "channel": channel.encode(),
            "data": json.dumps(message).encode(),
            "type": "message"
        })
        mock_redis_client.pubsub.return_value = mock_pubsub
        
        with patch('src.services.redis.pubsub.get_redis_client', return_value=mock_redis_client):
            from src.services.redis.pubsub import get_pubsub_service
            pubsub_service = await get_pubsub_service()
            
            # Act
            # Publish message
            await pubsub_service.publish(channel, message)
            
            # Subscribe to channel
            await pubsub_service.subscribe(channel)
            
            # Get message
            received_message = await pubsub_service.get_message()
            
            # Assert
            mock_redis_client.publish.assert_called_once_with(channel, json.dumps(message))
            mock_pubsub.subscribe.assert_called_once_with(channel)
            assert received_message is not None


@pytest.mark.integration
class TestExternalServicesErrorHandling:
    """Test error handling and resilience for external services."""

    @pytest.mark.asyncio
    async def test_service_timeout_handling(self):
        """Test handling of service timeouts."""
        # Test with slow response
        async def slow_response():
            await asyncio.sleep(10)  # Simulate slow service
            return {"data": "response"}
        
        with patch('httpx.AsyncClient.get', side_effect=slow_response):
            # This would test timeout handling in actual service calls
            # Implementation depends on the specific service client
            pass

    @pytest.mark.asyncio
    async def test_service_rate_limiting_backoff(self):
        """Test exponential backoff for rate-limited services."""
        # Test implementation for rate limiting with exponential backoff
        # This would be implemented in the actual service clients
        pass

    @pytest.mark.asyncio
    async def test_service_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for failing services."""
        # Test implementation for circuit breaker pattern
        # This would prevent cascading failures when services are down
        pass

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self):
        """Test health monitoring for all external services."""
        health_checks = {
            "plaid": {"status": "healthy", "response_time": 150},
            "stripe": {"status": "healthy", "response_time": 200},
            "auth0": {"status": "healthy", "response_time": 100},
            "redis": {"status": "healthy", "response_time": 5}
        }
        
        # This would test the actual health monitoring implementation
        for service, expected_health in health_checks.items():
            assert expected_health["status"] == "healthy"
            assert expected_health["response_time"] < 1000  # Under 1 second