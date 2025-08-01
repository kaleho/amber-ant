"""Integration tests for transactions API endpoints."""
import pytest
from httpx import AsyncClient
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
import json
from unittest.mock import Mock, patch

from src.main import app
from src.database import get_tenant_database_session
from src.tenant.context import set_tenant_context
from src.exceptions import NotFoundError, ValidationError


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    mock_token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.test.token"
    return {
        "Authorization": mock_token,
        "X-Tenant-ID": "test-tenant",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for API tests."""
    return {
        "account_id": str(uuid4()),
        "amount": -45.67,
        "date": date.today().isoformat(),
        "description": "Coffee Shop Downtown",
        "merchant_name": "Local Coffee Co.",
        "category": "Food and Drink",
        "subcategory": "Coffee Shop",
        "pending": False,
        "plaid_transaction_id": "plaid_txn_123456",
        "plaid_account_id": "plaid_acc_789012",
        "iso_currency_code": "USD"
    }


@pytest.fixture
def sample_transaction_update():
    """Sample transaction update data."""
    return {
        "category": "Entertainment",
        "subcategory": "Movies",
        "notes": "Movie night with friends",
        "is_excluded_from_budget": False,
        "tags": ["entertainment", "social"]
    }


@pytest.fixture
def sample_split_data():
    """Sample transaction split data."""
    return {
        "splits": [
            {
                "amount": -20.00,
                "category": "Food and Drink",
                "subcategory": "Coffee",
                "description": "Coffee portion",
                "user_id": str(uuid4())
            },
            {
                "amount": -25.67,
                "category": "Food and Drink", 
                "subcategory": "Lunch",
                "description": "Lunch portion",
                "user_id": str(uuid4())
            }
        ]
    }


class TestTransactionCRUDAPI:
    """Test transaction CRUD API endpoints."""

    @pytest.mark.asyncio
    async def test_create_transaction_success(self, client, auth_headers, sample_transaction_data):
        """Test successful transaction creation via API."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.auth.dependencies.require_permission') as mock_perm:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_perm.return_value = True
            
            response = await client.post(
                "/api/v1/transactions",
                headers=auth_headers,
                json=sample_transaction_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["amount"] == "-45.67"
            assert data["description"] == "Coffee Shop Downtown"
            assert data["merchant_name"] == "Local Coffee Co."
            assert data["category"] == "Food and Drink"

    @pytest.mark.asyncio
    async def test_create_transaction_validation_error(self, client, auth_headers):
        """Test transaction creation with invalid data."""
        invalid_data = {
            "account_id": "invalid-uuid",
            "amount": "not-a-number",
            "date": "invalid-date",
            "description": "",  # Empty description
            "iso_currency_code": "INVALID"  # Invalid currency code
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            response = await client.post(
                "/api/v1/transactions",
                headers=auth_headers,
                json=invalid_data
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "validation_failed" in data["error"]

    @pytest.mark.asyncio
    async def test_get_transaction_success(self, client, auth_headers):
        """Test successful transaction retrieval."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_transaction') as mock_get:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_transaction = Mock()
            mock_transaction.id = transaction_id
            mock_transaction.amount = Decimal("-45.67")
            mock_transaction.description = "Coffee Shop Downtown"
            mock_get.return_value = mock_transaction
            
            response = await client.get(
                f"/api/v1/transactions/{transaction_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == transaction_id

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, client, auth_headers):
        """Test transaction retrieval when transaction not found."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_transaction') as mock_get:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_get.side_effect = NotFoundError("Transaction not found")
            
            response = await client.get(
                f"/api/v1/transactions/{transaction_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_update_transaction_success(self, client, auth_headers, sample_transaction_update):
        """Test successful transaction update."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.update_transaction') as mock_update:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_updated_transaction = Mock()
            mock_updated_transaction.id = transaction_id
            mock_updated_transaction.category = "Entertainment"
            mock_updated_transaction.subcategory = "Movies"
            mock_update.return_value = mock_updated_transaction
            
            response = await client.put(
                f"/api/v1/transactions/{transaction_id}",
                headers=auth_headers,
                json=sample_transaction_update
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["category"] == "Entertainment"

    @pytest.mark.asyncio
    async def test_delete_transaction_success(self, client, auth_headers):
        """Test successful transaction deletion."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.delete_transaction') as mock_delete:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_delete.return_value = True
            
            response = await client.delete(
                f"/api/v1/transactions/{transaction_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_list_transactions_with_filters(self, client, auth_headers):
        """Test listing transactions with comprehensive filters."""
        query_params = {
            "account_id": str(uuid4()),
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "category": "Food and Drink",
            "min_amount": -100.00,
            "max_amount": 0.00,
            "pending": False,
            "search": "coffee",
            "limit": 20,
            "offset": 0,
            "sort_by": "date",
            "sort_order": "desc"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.list_transactions') as mock_list:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_transactions = [Mock() for _ in range(10)]
            mock_list.return_value = {"transactions": mock_transactions, "total": 10}
            
            response = await client.get(
                "/api/v1/transactions",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["transactions"]) == 10
            assert data["total"] == 10

    @pytest.mark.asyncio
    async def test_bulk_update_transactions(self, client, auth_headers):
        """Test bulk updating multiple transactions."""
        bulk_update_data = {
            "transaction_ids": [str(uuid4()) for _ in range(5)],
            "updates": {
                "category": "Updated Category",
                "subcategory": "Updated Subcategory",
                "is_excluded_from_budget": True
            }
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.bulk_update_transactions') as mock_bulk:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_bulk.return_value = {"updated_count": 5, "failed_count": 0}
            
            response = await client.put(
                "/api/v1/transactions/bulk",
                headers=auth_headers,
                json=bulk_update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["updated_count"] == 5
            assert data["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_bulk_delete_transactions(self, client, auth_headers):
        """Test bulk deleting multiple transactions."""
        bulk_delete_data = {
            "transaction_ids": [str(uuid4()) for _ in range(3)]
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.bulk_delete_transactions') as mock_bulk_delete:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_bulk_delete.return_value = {"deleted_count": 3, "failed_count": 0}
            
            response = await client.delete(
                "/api/v1/transactions/bulk",
                headers=auth_headers,
                json=bulk_delete_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["deleted_count"] == 3


class TestTransactionSplitAPI:
    """Test transaction splitting functionality."""

    @pytest.mark.asyncio
    async def test_split_transaction_success(self, client, auth_headers, sample_split_data):
        """Test successful transaction splitting."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.split_transaction') as mock_split:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_split_result = {
                "original_transaction": Mock(),
                "split_transactions": [Mock() for _ in range(2)]
            }
            mock_split.return_value = mock_split_result
            
            response = await client.post(
                f"/api/v1/transactions/{transaction_id}/split",
                headers=auth_headers,
                json=sample_split_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["split_transactions"]) == 2

    @pytest.mark.asyncio
    async def test_split_transaction_validation_error(self, client, auth_headers):
        """Test transaction splitting with invalid split data."""
        transaction_id = str(uuid4())
        invalid_split_data = {
            "splits": [
                {
                    "amount": -20.00,
                    "category": "Food and Drink",
                    "description": "Split 1"
                    # Missing required fields
                },
                {
                    "amount": -30.00,  # Total doesn't match original
                    "category": "Transportation", 
                    "description": "Split 2"
                }
            ]
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            response = await client.post(
                f"/api/v1/transactions/{transaction_id}/split",
                headers=auth_headers,
                json=invalid_split_data
            )
            
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unsplit_transaction(self, client, auth_headers):
        """Test unsplitting a previously split transaction."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.unsplit_transaction') as mock_unsplit:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_restored_transaction = Mock()
            mock_restored_transaction.id = transaction_id
            mock_unsplit.return_value = mock_restored_transaction
            
            response = await client.post(
                f"/api/v1/transactions/{transaction_id}/unsplit",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == transaction_id


class TestTransactionCategorizationAPI:
    """Test transaction categorization functionality."""

    @pytest.mark.asyncio
    async def test_auto_categorize_transaction(self, client, auth_headers):
        """Test automatic transaction categorization."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.auto_categorize_transaction') as mock_categorize:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_categorized = Mock()
            mock_categorized.category = "Food and Drink"
            mock_categorized.subcategory = "Coffee Shop"
            mock_categorized.confidence_score = 0.95
            mock_categorize.return_value = mock_categorized
            
            response = await client.post(
                f"/api/v1/transactions/{transaction_id}/auto-categorize",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["category"] == "Food and Drink"
            assert data["subcategory"] == "Coffee Shop"

    @pytest.mark.asyncio
    async def test_bulk_auto_categorize(self, client, auth_headers):
        """Test bulk automatic categorization."""
        bulk_categorize_data = {
            "transaction_ids": [str(uuid4()) for _ in range(10)],
            "overwrite_existing": False
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.bulk_auto_categorize') as mock_bulk_cat:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_bulk_cat.return_value = {
                "categorized_count": 8,
                "skipped_count": 2,
                "failed_count": 0
            }
            
            response = await client.post(
                "/api/v1/transactions/auto-categorize/bulk",
                headers=auth_headers,
                json=bulk_categorize_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["categorized_count"] == 8
            assert data["skipped_count"] == 2

    @pytest.mark.asyncio
    async def test_get_category_suggestions(self, client, auth_headers):
        """Test getting category suggestions for a transaction."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_category_suggestions') as mock_suggestions:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_suggestions.return_value = [
                {"category": "Food and Drink", "subcategory": "Coffee Shop", "confidence": 0.95},
                {"category": "Entertainment", "subcategory": "Movies", "confidence": 0.15},
                {"category": "Transportation", "subcategory": "Gas", "confidence": 0.05}
            ]
            
            response = await client.get(
                f"/api/v1/transactions/{transaction_id}/category-suggestions",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestions"]) == 3
            assert data["suggestions"][0]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_create_categorization_rule(self, client, auth_headers):
        """Test creating custom categorization rules."""
        rule_data = {
            "name": "Coffee Shop Rule",
            "conditions": {
                "merchant_name_contains": ["starbucks", "coffee", "cafe"],
                "description_contains": ["coffee", "latte", "espresso"],
                "amount_range": {"min": -50.00, "max": -1.00}
            },
            "actions": {
                "category": "Food and Drink",
                "subcategory": "Coffee Shop",
                "tags": ["coffee", "drinks"]
            },
            "priority": 10,
            "is_active": True
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.create_categorization_rule') as mock_create_rule:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_rule = Mock()
            mock_rule.id = str(uuid4())
            mock_rule.name = "Coffee Shop Rule"
            mock_create_rule.return_value = mock_rule
            
            response = await client.post(
                "/api/v1/transactions/categorization-rules",
                headers=auth_headers,
                json=rule_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Coffee Shop Rule"


class TestTransactionAnalyticsAPI:
    """Test transaction analytics and reporting."""

    @pytest.mark.asyncio
    async def test_get_spending_analytics(self, client, auth_headers):
        """Test spending analytics endpoint."""
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "group_by": "category",
            "account_ids": f"{uuid4()},{uuid4()}"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_spending_analytics') as mock_analytics:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_analytics_data = {
                "total_spending": Decimal("2500.00"),
                "transaction_count": 150,
                "average_transaction": Decimal("16.67"),
                "category_breakdown": {
                    "Food and Drink": Decimal("800.00"),
                    "Transportation": Decimal("600.00"),
                    "Entertainment": Decimal("400.00"),
                    "Shopping": Decimal("700.00")
                },
                "monthly_trends": [
                    {"month": "2024-01", "total": Decimal("200.00"), "count": 12},
                    {"month": "2024-02", "total": Decimal("220.00"), "count": 15}
                ]
            }
            mock_analytics.return_value = mock_analytics_data
            
            response = await client.get(
                "/api/v1/transactions/analytics/spending",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_spending"] == "2500.00"
            assert data["transaction_count"] == 150
            assert len(data["category_breakdown"]) == 4

    @pytest.mark.asyncio
    async def test_get_income_analytics(self, client, auth_headers):
        """Test income analytics endpoint."""
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "include_transfers": False
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_income_analytics') as mock_income:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_income_data = {
                "total_income": Decimal("5000.00"),
                "transaction_count": 12,
                "average_income": Decimal("416.67"),
                "income_sources": {
                    "Payroll Deposit": Decimal("4500.00"),
                    "Freelance Payment": Decimal("500.00")
                },
                "monthly_income": [
                    {"month": "2024-01", "total": Decimal("4000.00")},
                    {"month": "2024-02", "total": Decimal("1000.00")}
                ]
            }
            mock_income.return_value = mock_income_data
            
            response = await client.get(
                "/api/v1/transactions/analytics/income",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_income"] == "5000.00"
            assert len(data["income_sources"]) == 2

    @pytest.mark.asyncio
    async def test_get_cashflow_analytics(self, client, auth_headers):
        """Test cashflow analytics endpoint."""
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "period": "monthly"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_cashflow_analytics') as mock_cashflow:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_cashflow_data = {
                "net_cashflow": Decimal("2500.00"),
                "total_income": Decimal("5000.00"),
                "total_expenses": Decimal("2500.00"),
                "periods": [
                    {
                        "period": "2024-01",
                        "income": Decimal("4000.00"),
                        "expenses": Decimal("2000.00"),
                        "net": Decimal("2000.00")
                    },
                    {
                        "period": "2024-02", 
                        "income": Decimal("1000.00"),
                        "expenses": Decimal("500.00"),
                        "net": Decimal("500.00")
                    }
                ]
            }
            mock_cashflow.return_value = mock_cashflow_data
            
            response = await client.get(
                "/api/v1/transactions/analytics/cashflow",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["net_cashflow"] == "2500.00"
            assert len(data["periods"]) == 2

    @pytest.mark.asyncio
    async def test_export_transactions(self, client, auth_headers):
        """Test transaction export functionality."""
        export_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "format": "csv",
            "include_splits": True,
            "include_pending": False
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.export_transactions') as mock_export:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_export_data = {
                "export_id": str(uuid4()),
                "format": "csv",
                "status": "processing",
                "created_at": datetime.utcnow().isoformat()
            }
            mock_export.return_value = mock_export_data
            
            response = await client.post(
                "/api/v1/transactions/export",
                headers=auth_headers,
                json=export_params
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["format"] == "csv"
            assert data["status"] == "processing"


class TestTransactionSearchAPI:
    """Test transaction search functionality."""

    @pytest.mark.asyncio
    async def test_advanced_search(self, client, auth_headers):
        """Test advanced transaction search."""
        search_data = {
            "query": "coffee starbucks",
            "filters": {
                "amount_range": {"min": -100.00, "max": -1.00},
                "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
                "categories": ["Food and Drink", "Entertainment"],
                "account_ids": [str(uuid4()), str(uuid4())],
                "merchant_names": ["Starbucks", "Coffee Bean"],
                "pending": False,
                "has_notes": True
            },
            "sort": {
                "field": "date",
                "order": "desc"
            },
            "pagination": {
                "limit": 50,
                "offset": 0
            }
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.advanced_search') as mock_search:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_search_results = {
                "transactions": [Mock() for _ in range(25)],
                "total": 25,
                "facets": {
                    "categories": {
                        "Food and Drink": 20,
                        "Entertainment": 5
                    },
                    "merchants": {
                        "Starbucks": 15,
                        "Coffee Bean": 10
                    }
                }
            }
            mock_search.return_value = mock_search_results
            
            response = await client.post(
                "/api/v1/transactions/search",
                headers=auth_headers,
                json=search_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["transactions"]) == 25
            assert data["total"] == 25
            assert "facets" in data

    @pytest.mark.asyncio
    async def test_saved_search(self, client, auth_headers):
        """Test saving and retrieving search queries."""
        saved_search_data = {
            "name": "Coffee Expenses",
            "description": "All coffee-related expenses",
            "query": {
                "search_text": "coffee starbucks",
                "filters": {
                    "categories": ["Food and Drink"],
                    "amount_range": {"min": -50.00, "max": -1.00}
                }
            }
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.save_search') as mock_save:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_saved_search = Mock()
            mock_saved_search.id = str(uuid4())
            mock_saved_search.name = "Coffee Expenses"
            mock_save.return_value = mock_saved_search
            
            response = await client.post(
                "/api/v1/transactions/saved-searches",
                headers=auth_headers,
                json=saved_search_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Coffee Expenses"

    @pytest.mark.asyncio
    async def test_execute_saved_search(self, client, auth_headers):
        """Test executing a saved search."""
        search_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.execute_saved_search') as mock_execute:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_results = {
                "transactions": [Mock() for _ in range(15)],
                "total": 15,
                "search_name": "Coffee Expenses"
            }
            mock_execute.return_value = mock_results
            
            response = await client.get(
                f"/api/v1/transactions/saved-searches/{search_id}/execute",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["transactions"]) == 15
            assert data["search_name"] == "Coffee Expenses"


class TestTransactionSyncAPI:
    """Test transaction synchronization with external services."""

    @pytest.mark.asyncio
    async def test_sync_with_plaid(self, client, auth_headers):
        """Test syncing transactions with Plaid."""
        sync_data = {
            "account_ids": [str(uuid4()), str(uuid4())],
            "force_full_sync": False,
            "start_date": "2024-01-01"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.auth.dependencies.require_permission') as mock_perm, \
             patch('src.transactions.service.TransactionService.sync_with_plaid') as mock_sync:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_perm.return_value = True
            mock_sync_result = {
                "sync_id": str(uuid4()),
                "status": "processing",
                "accounts_synced": 2,
                "started_at": datetime.utcnow().isoformat()
            }
            mock_sync.return_value = mock_sync_result
            
            response = await client.post(
                "/api/v1/transactions/sync/plaid",
                headers=auth_headers,
                json=sync_data
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "processing"
            assert data["accounts_synced"] == 2

    @pytest.mark.asyncio
    async def test_get_sync_status(self, client, auth_headers):
        """Test getting synchronization status."""
        sync_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_sync_status') as mock_status:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_sync_status = {
                "sync_id": sync_id,
                "status": "completed",
                "progress": 100,
                "transactions_added": 45,
                "transactions_updated": 12,
                "transactions_removed": 3,
                "completed_at": datetime.utcnow().isoformat(),
                "errors": []
            }
            mock_status.return_value = mock_sync_status
            
            response = await client.get(
                f"/api/v1/transactions/sync/{sync_id}/status",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["transactions_added"] == 45

    @pytest.mark.asyncio
    async def test_manual_transaction_import(self, client, auth_headers):
        """Test manual transaction import from CSV/OFX."""
        import_data = {
            "format": "csv",
            "account_id": str(uuid4()),
            "file_content": "date,amount,description\n2024-01-01,-25.50,Coffee Shop\n2024-01-02,-45.00,Grocery Store",
            "column_mappings": {
                "date": "date",
                "amount": "amount", 
                "description": "description"
            },
            "skip_duplicates": True
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.import_transactions') as mock_import:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_import_result = {
                "import_id": str(uuid4()),
                "status": "processing",
                "total_rows": 2,
                "valid_rows": 2,
                "invalid_rows": 0
            }
            mock_import.return_value = mock_import_result
            
            response = await client.post(
                "/api/v1/transactions/import",
                headers=auth_headers,
                json=import_data
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["total_rows"] == 2
            assert data["valid_rows"] == 2


class TestTransactionAPIPermissions:
    """Test API permissions and authorization."""

    @pytest.mark.asyncio
    async def test_create_transaction_unauthorized(self, client, sample_transaction_data):
        """Test transaction creation without authentication."""
        response = await client.post(
            "/api/v1/transactions",
            json=sample_transaction_data
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, client, auth_headers):
        """Test that transaction data is properly isolated by tenant."""
        transaction_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tenant.context.get_tenant_context') as mock_tenant:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_tenant.return_value = Mock(tenant_id="tenant1")
            
            # User from tenant1 should not access tenant2 data
            response = await client.get(
                f"/api/v1/transactions/{transaction_id}",
                headers={**auth_headers, "X-Tenant-ID": "tenant2"}
            )
            
            # Should handle tenant mismatch appropriately
            assert response.status_code in [404, 403]

    @pytest.mark.asyncio
    async def test_admin_only_operations(self, client, auth_headers):
        """Test operations requiring admin permissions."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.auth.dependencies.require_permission') as mock_perm:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_perm.side_effect = Exception("Insufficient permissions")
            
            # Test admin-only bulk operations
            response = await client.post(
                "/api/v1/transactions/sync/plaid",
                headers=auth_headers,
                json={"account_ids": [str(uuid4())]}
            )
            
            assert response.status_code == 403


class TestTransactionAPIPerformance:
    """Test API performance and efficiency."""

    @pytest.mark.asyncio
    async def test_large_transaction_list_performance(self, client, auth_headers):
        """Test performance with large transaction lists."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.list_transactions') as mock_list:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            # Simulate large dataset
            mock_transactions = [Mock() for _ in range(1000)]
            mock_list.return_value = {"transactions": mock_transactions, "total": 1000}
            
            start_time = datetime.utcnow()
            response = await client.get(
                "/api/v1/transactions",
                headers=auth_headers,
                params={"limit": 1000}
            )
            end_time = datetime.utcnow()
            
            assert response.status_code == 200
            # Should complete within reasonable time
            assert (end_time - start_time).total_seconds() < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_transaction_operations(self, client, auth_headers, sample_transaction_data):
        """Test concurrent transaction operations."""
        import asyncio
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.create_transaction') as mock_create:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_transaction = Mock()
            mock_create.return_value = mock_transaction
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                task = client.post(
                    "/api/v1/transactions",
                    headers=auth_headers,
                    json={**sample_transaction_data, "description": f"Transaction {i}"}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_search_performance_with_complex_queries(self, client, auth_headers):
        """Test search performance with complex queries."""
        complex_search_data = {
            "query": "coffee starbucks seattle downtown",
            "filters": {
                "amount_range": {"min": -100.00, "max": -1.00},
                "date_range": {"start": "2020-01-01", "end": "2024-12-31"},
                "categories": ["Food and Drink", "Entertainment", "Transportation"],
                "has_notes": True,
                "has_tags": True
            },
            "pagination": {"limit": 100, "offset": 0}
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.advanced_search') as mock_search:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_search.return_value = {"transactions": [], "total": 0, "facets": {}}
            
            start_time = datetime.utcnow()
            response = await client.post(
                "/api/v1/transactions/search",
                headers=auth_headers,
                json=complex_search_data
            )
            end_time = datetime.utcnow()
            
            assert response.status_code == 200
            # Complex search should complete within reasonable time
            assert (end_time - start_time).total_seconds() < 3.0


class TestTransactionSummaryAPI:
    """Test transaction summary and trends endpoints."""

    @pytest.mark.asyncio
    async def test_get_transaction_summary(self, client, auth_headers):
        """Test transaction summary endpoint."""
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_transaction_summary') as mock_summary:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_summary_data = {
                "total_transactions": 150,
                "total_income": Decimal("5000.00"),
                "total_expenses": Decimal("2500.00"),
                "net_amount": Decimal("2500.00"),
                "average_transaction": Decimal("16.67"),
                "largest_expense": Decimal("500.00"),
                "largest_income": Decimal("4000.00"),
                "period": "2024-01-01 to 2024-12-31"
            }
            mock_summary.return_value = mock_summary_data
            
            response = await client.get(
                "/api/v1/transactions/summary",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_transactions"] == 150
            assert data["total_income"] == "5000.00"
            assert data["net_amount"] == "2500.00"

    @pytest.mark.asyncio
    async def test_get_transaction_trends(self, client, auth_headers):
        """Test transaction trends endpoint."""
        query_params = {
            "period_days": 90
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_transaction_trend') as mock_trends:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_trends_data = {
                "period_days": 90,
                "trend_direction": "increasing",
                "average_daily_spending": Decimal("75.50"),
                "spending_velocity": Decimal("5.2"),
                "category_trends": {
                    "Food and Drink": {"trend": "stable", "change_percent": 2.5},
                    "Transportation": {"trend": "increasing", "change_percent": 15.3}
                },
                "weekly_patterns": [
                    {"week": "2024-W10", "total": Decimal("525.00")},
                    {"week": "2024-W11", "total": Decimal("600.00")}
                ]
            }
            mock_trends.return_value = mock_trends_data
            
            response = await client.get(
                "/api/v1/transactions/trends",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["trend_direction"] == "increasing"
            assert data["period_days"] == 90

    @pytest.mark.asyncio
    async def test_get_spending_by_category(self, client, auth_headers):
        """Test spending breakdown by category."""
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "category_type": "discretionary"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_spending_by_category') as mock_spending:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_spending_data = {
                "Food and Drink": Decimal("800.00"),
                "Entertainment": Decimal("400.00"),
                "Shopping": Decimal("600.00"),
                "Transportation": Decimal("300.00")
            }
            mock_spending.return_value = mock_spending_data
            
            response = await client.get(
                "/api/v1/transactions/spending/by-category",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "spending_by_category" in data
            assert len(data["spending_by_category"]) == 4


class TestTransactionUtilityAPI:
    """Test utility endpoints for transactions."""

    @pytest.mark.asyncio
    async def test_get_uncategorized_transactions(self, client, auth_headers):
        """Test getting uncategorized transactions."""
        query_params = {
            "limit": 50
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_uncategorized_transactions') as mock_uncategorized:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_transactions = [
                Mock(id=str(uuid4()), description="Unknown merchant", category=None),
                Mock(id=str(uuid4()), description="ATM withdrawal", category=None),
                Mock(id=str(uuid4()), description="Online purchase", category=None)
            ]
            mock_uncategorized.return_value = mock_transactions
            
            response = await client.get(
                "/api/v1/transactions/uncategorized",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_duplicate_transactions(self, client, auth_headers):
        """Test finding potential duplicate transactions."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_duplicate_transactions') as mock_duplicates:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_duplicate_groups = [
                [
                    Mock(id=str(uuid4()), amount=Decimal("-25.50"), description="Coffee Shop"),
                    Mock(id=str(uuid4()), amount=Decimal("-25.50"), description="Coffee Shop")
                ],
                [
                    Mock(id=str(uuid4()), amount=Decimal("-100.00"), description="Gas Station"),
                    Mock(id=str(uuid4()), amount=Decimal("-100.00"), description="Gas Station"),
                    Mock(id=str(uuid4()), amount=Decimal("-100.00"), description="Gas Station")
                ]
            ]
            mock_duplicates.return_value = mock_duplicate_groups
            
            response = await client.get(
                "/api/v1/transactions/duplicates",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_groups"] == 2
            assert data["total_duplicates"] == 5  # 2 + 3
            assert len(data["duplicate_groups"]) == 2

    @pytest.mark.asyncio
    async def test_categorize_transactions(self, client, auth_headers):
        """Test automatic transaction categorization endpoint."""
        categorize_data = {
            "transaction_ids": [str(uuid4()) for _ in range(5)],
            "overwrite_existing": False,
            "confidence_threshold": 0.8
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.categorize_transactions') as mock_categorize:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_result = {
                "processed": 5,
                "categorized": 4,
                "skipped": 1,
                "failed": 0,
                "results": [
                    {"transaction_id": str(uuid4()), "category": "Food and Drink", "confidence": 0.95},
                    {"transaction_id": str(uuid4()), "category": "Transportation", "confidence": 0.87}
                ]
            }
            mock_categorize.return_value = mock_result
            
            response = await client.post(
                "/api/v1/transactions/categorize",
                headers=auth_headers,
                json=categorize_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["processed"] == 5
            assert data["categorized"] == 4
            assert data["skipped"] == 1


class TestTransactionAccountAPI:
    """Test account-specific transaction endpoints."""

    @pytest.mark.asyncio
    async def test_get_account_transactions(self, client, auth_headers):
        """Test getting transactions for a specific account."""
        account_id = str(uuid4())
        query_params = {
            "skip": 0,
            "limit": 50,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_transactions_for_account') as mock_account_txns:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_transactions = [
                Mock(id=str(uuid4()), account_id=account_id, amount=Decimal("-25.50")),
                Mock(id=str(uuid4()), account_id=account_id, amount=Decimal("-45.00")),
                Mock(id=str(uuid4()), account_id=account_id, amount=Decimal("2000.00"))
            ]
            mock_account_txns.return_value = mock_transactions
            
            response = await client.get(
                f"/api/v1/transactions/account/{account_id}",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_account_summary(self, client, auth_headers):
        """Test getting summary for a specific account."""
        account_id = str(uuid4())
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.get_account_summary') as mock_account_summary:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_summary = {
                "account_id": account_id,
                "transaction_count": 45,
                "total_income": Decimal("3000.00"),
                "total_expenses": Decimal("1200.00"),
                "net_amount": Decimal("1800.00"),
                "average_transaction": Decimal("40.00"),
                "period": "2024-01-01 to 2024-12-31"
            }
            mock_account_summary.return_value = mock_summary
            
            response = await client.get(
                f"/api/v1/transactions/account/{account_id}/summary",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["account_id"] == account_id
            assert data["transaction_count"] == 45
            assert data["net_amount"] == "1800.00"


class TestTransactionAPIValidation:
    """Test comprehensive API input validation."""

    @pytest.mark.asyncio
    async def test_invalid_date_formats(self, client, auth_headers):
        """Test various invalid date format scenarios."""
        invalid_date_cases = [
            {"start_date": "invalid-date", "end_date": "2024-12-31"},
            {"start_date": "2024-01-01", "end_date": "not-a-date"},
            {"start_date": "2024-13-01", "end_date": "2024-12-31"},  # Invalid month
            {"start_date": "2024-01-32", "end_date": "2024-12-31"},  # Invalid day
            {"start_date": "2024-12-31", "end_date": "2024-01-01"}   # End before start
        ]
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            for invalid_params in invalid_date_cases:
                response = await client.get(
                    "/api/v1/transactions",
                    headers=auth_headers,
                    params=invalid_params
                )
                
                assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_pagination_validation(self, client, auth_headers):
        """Test pagination parameter validation."""
        invalid_pagination_cases = [
            {"skip": -1, "limit": 100},     # Negative skip
            {"skip": 0, "limit": 0},       # Zero limit
            {"skip": 0, "limit": 1001},    # Limit too large
            {"skip": "invalid", "limit": 100},  # Non-numeric skip
            {"skip": 0, "limit": "invalid"}     # Non-numeric limit
        ]
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            for invalid_params in invalid_pagination_cases:
                response = await client.get(
                    "/api/v1/transactions",
                    headers=auth_headers,
                    params=invalid_params
                )
                
                assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_amount_validation(self, client, auth_headers, sample_transaction_data):
        """Test transaction amount validation."""
        invalid_amount_cases = [
            {**sample_transaction_data, "amount": "not-a-number"},
            {**sample_transaction_data, "amount": float('inf')},
            {**sample_transaction_data, "amount": float('-inf')},
            {**sample_transaction_data, "amount": None}
        ]
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            for invalid_data in invalid_amount_cases:
                response = await client.post(
                    "/api/v1/transactions",
                    headers=auth_headers,
                    json=invalid_data
                )
                
                assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_uuid_validation(self, client, auth_headers):
        """Test UUID parameter validation."""
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456", # Incomplete UUID
            "123e4567-e89b-12d3-a456-426614174000-extra", # Too long
            "",  # Empty string
            "null"  # String null
        ]
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            for invalid_uuid in invalid_uuids:
                response = await client.get(
                    f"/api/v1/transactions/{invalid_uuid}",
                    headers=auth_headers
                )
                
                assert response.status_code == 422


class TestTransactionAPIErrorHandling:
    """Test comprehensive error handling scenarios."""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, client, auth_headers, sample_transaction_data):
        """Test handling of database connection errors."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.create_transaction') as mock_create:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_create.side_effect = Exception("Database connection failed")
            
            response = await client.post(
                "/api/v1/transactions",
                headers=auth_headers,
                json=sample_transaction_data
            )
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_service_timeout_error(self, client, auth_headers):
        """Test handling of service timeout errors."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.transactions.service.TransactionService.list_transactions') as mock_list:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_list.side_effect = TimeoutError("Service request timed out")
            
            response = await client.get(
                "/api/v1/transactions",
                headers=auth_headers
            )
            
            assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client, auth_headers, sample_transaction_data):
        """Test API rate limiting behavior."""
        import asyncio
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            # Simulate rapid requests that might trigger rate limiting
            tasks = []
            for i in range(100):  # Many rapid requests
                task = client.get(
                    "/api/v1/transactions",
                    headers=auth_headers
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Some requests should succeed, but rate limiting might kick in
            status_codes = [
                r.status_code if hasattr(r, 'status_code') else 500 
                for r in responses
            ]
            
            # Should have a mix of 200s and potentially 429s (rate limited)
            assert 200 in status_codes