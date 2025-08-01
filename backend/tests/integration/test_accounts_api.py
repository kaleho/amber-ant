"""Integration tests for accounts API endpoints."""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
import json

from tests.conftest import assert_response_structure, assert_datetime_field, assert_uuid_field, assert_currency_field


@pytest.mark.integration
class TestAccountsAPI:
    """Test accounts API endpoints integration."""
    
    def test_create_account_success(self, test_client, auth_headers, test_user, test_data_generator):
        """Test successful account creation via API."""
        # Arrange
        account_data = test_data_generator.account_data({
            "name": "Test Savings Account",
            "account_type": "savings",
            "balance": 2500.00
        })
        
        # Act
        response = test_client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        
        assert_response_structure(data, [
            "id", "name", "account_type", "balance", "currency",
            "is_active", "created_at", "updated_at"
        ])
        assert data["name"] == account_data["name"]
        assert data["account_type"] == account_data["account_type"]
        assert_currency_field(data["balance"])
        assert data["currency"] == "USD"
        assert data["is_active"] is True
        assert_uuid_field(data["id"])
        assert_datetime_field(data["created_at"])
    
    def test_create_account_with_plaid(self, test_client, auth_headers, test_user, mock_plaid):
        """Test account creation with Plaid integration."""
        # Arrange
        account_data = {
            "name": "Plaid Checking",
            "account_type": "checking",
            "plaid_account_id": "plaid_account_123",
            "balance": 0.00  # Will be updated from Plaid
        }
        
        mock_plaid.get_account_details.return_value = {
            "balance": {"current": 1500.00, "available": 1400.00},
            "name": "Chase Checking",
            "official_name": "Chase Total Checking",
            "type": "depository",
            "subtype": "checking"
        }
        
        # Act
        response = test_client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == account_data["name"]
        assert data["plaid_account_id"] == account_data["plaid_account_id"]
        # Balance should be updated from Plaid
        assert float(data["balance"]) == 1500.00
    
    def test_create_account_invalid_data(self, test_client, auth_headers):
        """Test account creation with invalid data."""
        invalid_cases = [
            # Missing required fields
            {"name": "Test Account"},  # Missing account_type
            {"account_type": "checking"},  # Missing name
            
            # Invalid account type
            {
                "name": "Test Account",
                "account_type": "invalid_type",
                "balance": 1000.00
            },
            
            # Invalid currency
            {
                "name": "Test Account", 
                "account_type": "checking",
                "balance": 1000.00,
                "currency": "INVALID"
            },
            
            # Negative balance (if not allowed)
            {
                "name": "Test Account",
                "account_type": "checking", 
                "balance": -1000.00
            }
        ]
        
        for invalid_data in invalid_cases:
            response = test_client.post(
                "/api/v1/accounts",
                json=invalid_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "error" in data
    
    def test_get_account_by_id_success(self, test_client, auth_headers, test_account):
        """Test successful account retrieval by ID."""
        # Act
        response = test_client.get(
            f"/api/v1/accounts/{test_account.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert_response_structure(data, [
            "id", "name", "account_type", "balance", "currency",
            "is_active", "created_at", "updated_at"
        ])
        assert data["id"] == test_account.id
        assert data["name"] == test_account.name
        assert data["account_type"] == test_account.account_type
    
    def test_get_account_by_id_not_found(self, test_client, auth_headers):
        """Test account retrieval with non-existent ID."""
        response = test_client.get(
            "/api/v1/accounts/non-existent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_get_user_accounts(self, test_client, auth_headers, test_user):
        """Test retrieval of user's accounts."""
        # Act
        response = test_client.get(
            "/api/v1/accounts",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "accounts" in data or isinstance(data, list)
        if "accounts" in data:
            accounts = data["accounts"]
            assert "total" in data
        else:
            accounts = data
        
        assert isinstance(accounts, list)
        for account in accounts:
            assert_response_structure(account, [
                "id", "name", "account_type", "balance", "is_active"
            ])
    
    def test_update_account_success(self, test_client, auth_headers, test_account):
        """Test successful account update."""
        # Arrange
        update_data = {
            "name": "Updated Account Name",
            "is_active": False
        }
        
        # Act
        response = test_client.patch(
            f"/api/v1/accounts/{test_account.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["is_active"] == update_data["is_active"]
        assert data["id"] == test_account.id
    
    def test_update_account_not_found(self, test_client, auth_headers):
        """Test account update with non-existent ID."""
        update_data = {"name": "Updated Name"}
        
        response = test_client.patch(
            "/api/v1/accounts/non-existent-id",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_account_success(self, test_client, auth_headers, test_account):
        """Test successful account deletion."""
        # Act
        response = test_client.delete(
            f"/api/v1/accounts/{test_account.id}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 204
        
        # Verify account is deleted
        get_response = test_client.get(
            f"/api/v1/accounts/{test_account.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_delete_account_with_transactions(self, test_client, auth_headers, test_account, test_transaction):
        """Test account deletion prevention when account has transactions."""
        # Act
        response = test_client.delete(
            f"/api/v1/accounts/{test_account.id}",
            headers=auth_headers
        )
        
        # Assert - should prevent deletion if account has transactions
        assert response.status_code in [400, 422]
        data = response.json()
        assert "transaction" in data["message"].lower()
    
    def test_sync_account_balance(self, test_client, auth_headers, test_account, mock_plaid):
        """Test account balance synchronization with Plaid."""
        # Arrange
        test_account.plaid_account_id = "plaid_account_123"
        mock_plaid.get_account_balance.return_value = {
            "current": 1750.25,
            "available": 1650.25
        }
        
        # Act
        response = test_client.post(
            f"/api/v1/accounts/{test_account.id}/sync-balance",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == 1750.25
    
    def test_sync_account_balance_no_plaid(self, test_client, auth_headers, test_account):
        """Test balance sync for account without Plaid integration."""
        # Ensure account has no Plaid ID
        test_account.plaid_account_id = None
        
        response = test_client.post(
            f"/api/v1/accounts/{test_account.id}/sync-balance",
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "plaid" in data["message"].lower()
    
    def test_get_account_summary(self, test_client, auth_headers, test_user):
        """Test account summary endpoint."""
        # Act
        response = test_client.get(
            "/api/v1/accounts/summary",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = [
            "total_balance", "active_accounts", "inactive_accounts",
            "account_types", "last_updated"
        ]
        assert_response_structure(data, expected_fields)
        assert_currency_field(data["total_balance"])
        assert isinstance(data["active_accounts"], int)
        assert isinstance(data["account_types"], dict)
    
    def test_get_accounts_by_type(self, test_client, auth_headers):
        """Test filtering accounts by type."""
        # Act
        response = test_client.get(
            "/api/v1/accounts?account_type=checking",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        accounts = data.get("accounts", data)
        for account in accounts:
            assert account["account_type"] == "checking"
    
    def test_deactivate_account(self, test_client, auth_headers, test_account):
        """Test account deactivation."""
        # Act
        response = test_client.post(
            f"/api/v1/accounts/{test_account.id}/deactivate",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["id"] == test_account.id


@pytest.mark.integration 
class TestAccountsAPIAuthentication:
    """Test accounts API authentication and authorization."""
    
    def test_unauthorized_access(self, test_client):
        """Test API access without authentication."""
        endpoints = [
            ("GET", "/api/v1/accounts"),
            ("POST", "/api/v1/accounts"), 
            ("GET", "/api/v1/accounts/test-id"),
            ("PATCH", "/api/v1/accounts/test-id"),
            ("DELETE", "/api/v1/accounts/test-id"),
            ("POST", "/api/v1/accounts/test-id/sync-balance"),
        ]
        
        for method, endpoint in endpoints:
            response = test_client.request(method, endpoint)
            assert response.status_code in [401, 403, 422]
    
    def test_account_ownership_validation(self, test_client, auth_headers, test_account):
        """Test that users can only access their own accounts."""
        # This would require creating accounts for different users
        # and verifying access restrictions
        
        # Try to access account with different user token
        different_user_headers = {
            "Authorization": "Bearer different-user-token",
            "X-Tenant-ID": "test-tenant"
        }
        
        response = test_client.get(
            f"/api/v1/accounts/{test_account.id}",
            headers=different_user_headers
        )
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404]


@pytest.mark.integration
class TestAccountsAPIPlaidIntegration:
    """Test accounts API Plaid integration scenarios."""
    
    def test_plaid_service_unavailable(self, test_client, auth_headers, test_account, mock_plaid):
        """Test handling when Plaid service is unavailable."""
        # Arrange
        from src.exceptions import ExternalServiceError
        mock_plaid.get_account_balance.side_effect = ExternalServiceError("plaid", "Service unavailable")
        test_account.plaid_account_id = "plaid_account_123"
        
        # Act
        response = test_client.post(
            f"/api/v1/accounts/{test_account.id}/sync-balance",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 502
        data = response.json()
        assert data["error"] == "external_service_error"
        assert data["service"] == "plaid"
    
    def test_plaid_rate_limiting(self, test_client, auth_headers, test_account, mock_plaid):
        """Test handling of Plaid rate limiting."""
        # Arrange
        from src.exceptions import ExternalServiceError
        mock_plaid.get_account_balance.side_effect = ExternalServiceError("plaid", "Rate limit exceeded")
        test_account.plaid_account_id = "plaid_account_123"
        
        # Act
        response = test_client.post(
            f"/api/v1/accounts/{test_account.id}/sync-balance",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 502
        data = response.json()
        assert "rate limit" in data["message"].lower()
    
    def test_invalid_plaid_account_id(self, test_client, auth_headers, test_account, mock_plaid):
        """Test handling of invalid Plaid account ID."""
        # Arrange
        from src.exceptions import ExternalServiceError
        mock_plaid.get_account_balance.side_effect = ExternalServiceError("plaid", "Account not found")
        test_account.plaid_account_id = "invalid_plaid_id"
        
        # Act
        response = test_client.post(
            f"/api/v1/accounts/{test_account.id}/sync-balance",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 502
        data = response.json()
        assert "plaid" in data["message"].lower()


@pytest.mark.integration
class TestAccountsAPIValidation:
    """Test accounts API data validation."""
    
    def test_balance_precision_validation(self, test_client, auth_headers):
        """Test balance precision handling."""
        account_data = {
            "name": "Precision Test Account",
            "account_type": "checking",
            "balance": 1000.123456789  # High precision
        }
        
        response = test_client.post(
            "/api/v1/accounts",
            json=account_data,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            # Should handle precision appropriately (likely 2 decimal places)
            balance_str = str(data["balance"])
            decimal_places = len(balance_str.split(".")[-1]) if "." in balance_str else 0
            assert decimal_places <= 2
    
    def test_currency_validation(self, test_client, auth_headers):
        """Test currency code validation."""
        valid_currencies = ["USD", "EUR", "GBP", "CAD"]
        invalid_currencies = ["INVALID", "XXX", "123"]
        
        for currency in valid_currencies:
            account_data = {
                "name": f"Test {currency} Account",
                "account_type": "checking",
                "balance": 1000.00,
                "currency": currency
            }
            
            response = test_client.post(
                "/api/v1/accounts",
                json=account_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["currency"] == currency
        
        for currency in invalid_currencies:
            account_data = {
                "name": f"Test {currency} Account",
                "account_type": "checking", 
                "balance": 1000.00,
                "currency": currency
            }
            
            response = test_client.post(
                "/api/v1/accounts",
                json=account_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422
    
    def test_account_name_validation(self, test_client, auth_headers):
        """Test account name validation."""
        test_cases = [
            ("", 422),  # Empty name
            ("A" * 255, 201),  # Max length
            ("A" * 256, 422),  # Too long
            ("Valid Account Name", 201),  # Normal case
            ("Account with numbers 123", 201),  # With numbers
            ("Account-with_special.chars", 201),  # Special characters
        ]
        
        for name, expected_status in test_cases:
            account_data = {
                "name": name,
                "account_type": "checking",
                "balance": 1000.00
            }
            
            response = test_client.post(
                "/api/v1/accounts",
                json=account_data,
                headers=auth_headers
            )
            
            assert response.status_code == expected_status
    
    def test_account_type_validation(self, test_client, auth_headers):
        """Test account type validation."""
        valid_types = ["checking", "savings", "credit", "investment", "loan"]
        invalid_types = ["invalid", "", "checking_account", "CHECKING"]
        
        for account_type in valid_types:
            account_data = {
                "name": f"Test {account_type} Account",
                "account_type": account_type,
                "balance": 1000.00
            }
            
            response = test_client.post(
                "/api/v1/accounts",
                json=account_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
        
        for account_type in invalid_types:
            account_data = {
                "name": f"Test {account_type} Account",
                "account_type": account_type,
                "balance": 1000.00
            }
            
            response = test_client.post(
                "/api/v1/accounts",
                json=account_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422


@pytest.mark.integration
class TestAccountsAPIErrorHandling:
    """Test accounts API error handling."""
    
    def test_malformed_balance_data(self, test_client, auth_headers):
        """Test handling of malformed balance data."""
        malformed_cases = [
            {"balance": "not-a-number"},
            {"balance": "1000.00.00"},  # Invalid decimal
            {"balance": ""},
            {"balance": None},
        ]
        
        for case in malformed_cases:
            account_data = {
                "name": "Test Account",
                "account_type": "checking",
                **case
            }
            
            response = test_client.post(
                "/api/v1/accounts",
                json=account_data,
                headers=auth_headers
            )
            
            assert response.status_code == 422
    
    def test_concurrent_balance_updates(self, test_client, auth_headers, test_account):
        """Test handling of concurrent balance updates."""
        import concurrent.futures
        import threading
        
        def update_account(client, headers, account_id, name_suffix):
            return client.patch(
                f"/api/v1/accounts/{account_id}",
                json={"name": f"Updated Account {name_suffix}"},
                headers=headers
            )
        
        # Perform concurrent updates
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(update_account, test_client, auth_headers, test_account.id, i)
                for i in range(5)
            ]
            
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # At least some should succeed
        successful = [r for r in responses if r.status_code == 200]
        assert len(successful) >= 1
        
        # Verify final state is consistent
        final_response = test_client.get(
            f"/api/v1/accounts/{test_account.id}",
            headers=auth_headers
        )
        assert final_response.status_code == 200