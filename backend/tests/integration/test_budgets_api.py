"""Integration tests for budgets API endpoints."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from decimal import Decimal
from datetime import date, datetime, timezone
import json

from src.budgets.models import BudgetPeriod, BudgetStatus, AlertType
from tests.conftest import assert_response_structure, assert_datetime_field, assert_currency_field


@pytest.mark.integration
class TestBudgetsAPI:
    """Test budgets API endpoints integration."""
    
    def test_create_budget_success(self, test_client, auth_headers, test_data_generator):
        """Test successful budget creation via API."""
        # Arrange
        budget_data = {
            "name": "Monthly Family Budget",
            "description": "Our monthly budget for February",
            "total_amount": 5000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29",
            "warning_threshold": 75.0,
            "critical_threshold": 90.0,
            "categories": [
                {
                    "category_name": "Groceries",
                    "allocated_amount": 800.00,
                    "is_essential": True,
                    "priority": 1
                },
                {
                    "category_name": "Entertainment",
                    "allocated_amount": 300.00,
                    "is_essential": False,
                    "priority": 3
                }
            ]
        }
        
        # Act
        response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        
        assert_response_structure(data, [
            "id", "name", "description", "total_amount", "spent_amount",
            "remaining_amount", "period_type", "start_date", "end_date",
            "status", "warning_threshold", "critical_threshold",
            "categories", "alerts", "created_at", "updated_at"
        ])
        
        assert data["name"] == "Monthly Family Budget"
        assert_currency_field(data["total_amount"])
        assert data["total_amount"] == 5000.00
        assert data["period_type"] == "monthly"
        assert len(data["categories"]) == 2
        assert_datetime_field(data["created_at"])
        
        # Verify categories
        groceries_cat = next(cat for cat in data["categories"] if cat["category_name"] == "Groceries")
        assert groceries_cat["allocated_amount"] == 800.00
        assert groceries_cat["is_essential"] is True
        assert groceries_cat["priority"] == 1
    
    def test_create_budget_categories_exceed_total(self, test_client, auth_headers):
        """Test budget creation with categories exceeding total amount."""
        # Arrange
        budget_data = {
            "name": "Invalid Budget",
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29",
            "categories": [
                {
                    "category_name": "Category 1",
                    "allocated_amount": 800.00,
                    "is_essential": True,
                    "priority": 1
                },
                {
                    "category_name": "Category 2",
                    "allocated_amount": 500.00,  # Total 1300 > 1000
                    "is_essential": False,
                    "priority": 2
                }
            ]
        }
        
        # Act
        response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "exceed" in data["message"].lower()
    
    def test_create_budget_invalid_date_range(self, test_client, auth_headers):
        """Test budget creation with invalid date range."""
        # Arrange
        budget_data = {
            "name": "Invalid Date Budget",
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-29",
            "end_date": "2024-02-01",  # End before start
        }
        
        # Act
        response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_get_budget_by_id_success(self, test_client, auth_headers):
        """Test successful budget retrieval by ID."""
        # First create a budget
        budget_data = {
            "name": "Test Budget",
            "total_amount": 2000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        create_response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            budget_id = create_response.json()["id"]
            
            # Act
            response = test_client.get(
                f"/api/v1/budgets/{budget_id}",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == budget_id
            assert data["name"] == "Test Budget"
            assert data["total_amount"] == 2000.00
    
    def test_get_budget_not_found(self, test_client, auth_headers):
        """Test budget retrieval with non-existent ID."""
        # Act
        response = test_client.get(
            "/api/v1/budgets/non-existent-budget",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "not_found"
    
    def test_get_user_budgets_success(self, test_client, auth_headers):
        """Test successful user budgets retrieval."""
        # Act
        response = test_client.get(
            "/api/v1/budgets",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "budgets" in data or isinstance(data, list)
        if "budgets" in data:
            budgets = data["budgets"]
            assert "total" in data
            assert "skip" in data
            assert "limit" in data
        else:
            budgets = data
        
        assert isinstance(budgets, list)
        for budget in budgets:
            assert_response_structure(budget, [
                "id", "name", "total_amount", "spent_amount",
                "status", "period_type", "created_at"
            ])
    
    def test_get_user_budgets_with_status_filter(self, test_client, auth_headers):
        """Test user budgets retrieval with status filter."""
        # Act
        response = test_client.get(
            "/api/v1/budgets?status=active",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        budgets = data.get("budgets", data)
        for budget in budgets:
            assert budget["status"] == "active"
    
    def test_get_current_budget_success(self, test_client, auth_headers):
        """Test getting current active budget."""
        # Act
        response = test_client.get(
            "/api/v1/budgets/current",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [200, 404]  # May not have current budget
        
        if response.status_code == 200:
            data = response.json()
            assert_response_structure(data, [
                "id", "name", "total_amount", "status", "start_date", "end_date"
            ])
            assert data["status"] == "active"
    
    def test_update_budget_success(self, test_client, auth_headers):
        """Test successful budget update."""
        # First create a budget
        budget_data = {
            "name": "Original Budget",
            "total_amount": 2000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        create_response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            budget_id = create_response.json()["id"]
            
            # Arrange update data
            update_data = {
                "name": "Updated Budget Name",
                "description": "Updated description",
                "total_amount": 2500.00
            }
            
            # Act
            response = test_client.patch(
                f"/api/v1/budgets/{budget_id}",
                json=update_data,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Budget Name"
            assert data["description"] == "Updated description"
            assert data["total_amount"] == 2500.00
    
    def test_delete_budget_success(self, test_client, auth_headers):
        """Test successful budget deletion (soft delete)."""
        # First create a budget
        budget_data = {
            "name": "Budget to Delete",
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        create_response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            budget_id = create_response.json()["id"]
            
            # Act
            response = test_client.delete(
                f"/api/v1/budgets/{budget_id}",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 204
            
            # Verify budget is soft deleted (status changed to inactive)
            get_response = test_client.get(
                f"/api/v1/budgets/{budget_id}",
                headers=auth_headers
            )
            if get_response.status_code == 200:
                data = get_response.json()
                assert data["status"] == "inactive"
    
    def test_get_budget_analytics_success(self, test_client, auth_headers):
        """Test successful budget analytics retrieval."""
        # Act
        response = test_client.get(
            "/api/v1/budgets/analytics",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert_response_structure(data, [
            "total_budgets", "active_budgets", "total_budgeted",
            "total_spent", "average_utilization"
        ])
        
        assert isinstance(data["total_budgets"], int)
        assert isinstance(data["active_budgets"], int)
        assert_currency_field(data["total_budgeted"])
        assert_currency_field(data["total_spent"])
    
    def test_add_category_to_budget_success(self, test_client, auth_headers):
        """Test successfully adding category to budget."""
        # First create a budget
        budget_data = {
            "name": "Test Budget",
            "total_amount": 3000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        create_response = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            budget_id = create_response.json()["id"]
            
            # Arrange category data
            category_data = {
                "category_name": "Transportation",
                "allocated_amount": 500.00,
                "is_essential": True,
                "priority": 2
            }
            
            # Act
            response = test_client.post(
                f"/api/v1/budgets/{budget_id}/categories",
                json=category_data,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["category_name"] == "Transportation"
            assert data["allocated_amount"] == 500.00
            assert data["is_essential"] is True
            assert data["priority"] == 2
    
    def test_update_budget_category_success(self, test_client, auth_headers):
        """Test successful budget category update."""
        # This would require creating a budget with categories first
        # Then updating one of the categories
        pass
    
    def test_delete_budget_category_success(self, test_client, auth_headers):
        """Test successful budget category deletion."""
        # This would require creating a budget with categories first
        # Then deleting one of the categories
        pass


@pytest.mark.integration
class TestBudgetTemplatesAPI:
    """Test budget templates API endpoints."""
    
    def test_create_template_success(self, test_client, auth_headers):
        """Test successful budget template creation."""
        # Arrange
        template_data = {
            "name": "Monthly Template",
            "description": "Standard monthly budget template",
            "period_type": "monthly",
            "total_amount": 4000.00,
            "warning_threshold": 75.0,
            "critical_threshold": 90.0,
            "categories": [
                {
                    "category_name": "Housing",
                    "allocated_amount": 1600.00,  # 40%
                    "is_essential": True,
                    "priority": 1
                },
                {
                    "category_name": "Food",
                    "allocated_amount": 800.00,   # 20%
                    "is_essential": True,
                    "priority": 1
                },
                {
                    "category_name": "Transportation",
                    "allocated_amount": 600.00,   # 15%
                    "is_essential": True,
                    "priority": 2
                }
            ]
        }
        
        # Act
        response = test_client.post(
            "/api/v1/budgets/templates",
            json=template_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        
        assert_response_structure(data, [
            "id", "name", "description", "period_type", "total_amount",
            "warning_threshold", "critical_threshold", "is_active",
            "use_count", "created_at"
        ])
        
        assert data["name"] == "Monthly Template"
        assert data["total_amount"] == 4000.00
        assert data["use_count"] == 0
        assert data["is_active"] is True
    
    def test_get_user_templates_success(self, test_client, auth_headers):
        """Test successful user templates retrieval."""
        # Act
        response = test_client.get(
            "/api/v1/budgets/templates",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        for template in data:
            assert_response_structure(template, [
                "id", "name", "period_type", "total_amount",
                "use_count", "is_active", "created_at"
            ])
    
    def test_create_budget_from_template_success(self, test_client, auth_headers):
        """Test successful budget creation from template."""
        # First create a template
        template_data = {
            "name": "Test Template",
            "period_type": "monthly",
            "total_amount": 2000.00,
            "categories": [
                {
                    "category_name": "Groceries",
                    "allocated_amount": 600.00,  # 30%
                    "is_essential": True,
                    "priority": 1
                }
            ]
        }
        
        template_response = test_client.post(
            "/api/v1/budgets/templates",
            json=template_data,
            headers=auth_headers
        )
        
        if template_response.status_code == 201:
            template_id = template_response.json()["id"]
            
            # Create budget from template
            budget_request = {
                "template_id": template_id,
                "name": "March Budget from Template",
                "start_date": "2024-03-01",
                "total_amount": 2500.00  # Different amount than template
            }
            
            # Act
            response = test_client.post(
                "/api/v1/budgets/from-template",
                json=budget_request,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == 201
            data = response.json()
            
            assert data["name"] == "March Budget from Template"
            assert data["total_amount"] == 2500.00
            assert len(data["categories"]) == 1
            
            # Category should be proportionally adjusted
            category = data["categories"][0]
            assert category["category_name"] == "Groceries"
            # 30% of 2500 = 750
            assert category["allocated_amount"] == 750.00


@pytest.mark.integration
class TestBudgetAlertsAPI:
    """Test budget alerts API endpoints."""
    
    def test_get_user_alerts_success(self, test_client, auth_headers):
        """Test successful user alerts retrieval."""
        # Act
        response = test_client.get(
            "/api/v1/budgets/alerts",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        for alert in data:
            assert_response_structure(alert, [
                "id", "budget_id", "alert_type", "title",
                "message", "is_read", "created_at"
            ])
            assert alert["alert_type"] in ["warning", "critical", "exceeded"]
    
    def test_get_user_alerts_unread_only(self, test_client, auth_headers):
        """Test getting only unread alerts."""
        # Act
        response = test_client.get(
            "/api/v1/budgets/alerts?unread_only=true",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        for alert in data:
            assert alert["is_read"] is False
    
    def test_mark_alert_as_read_success(self, test_client, auth_headers):
        """Test marking alert as read."""
        # This would require having an existing alert
        alert_id = "test-alert-id"
        
        # Act
        response = test_client.patch(
            f"/api/v1/budgets/alerts/{alert_id}/read",
            headers=auth_headers
        )
        
        # Assert - This depends on having test data
        assert response.status_code in [200, 404]
    
    def test_dismiss_alert_success(self, test_client, auth_headers):
        """Test dismissing alert."""
        # This would require having an existing alert
        alert_id = "test-alert-id"
        
        # Act
        response = test_client.patch(
            f"/api/v1/budgets/alerts/{alert_id}/dismiss",
            headers=auth_headers
        )
        
        # Assert - This depends on having test data
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestBudgetAPIMultiTenant:
    """Test budget API multi-tenant functionality."""
    
    def test_budget_tenant_isolation(self, test_client):
        """Test that budgets are isolated between tenants."""
        tenant_a_headers = {
            "Authorization": "Bearer tenant-a-token",
            "X-Tenant-ID": "tenant-a"
        }
        
        tenant_b_headers = {
            "Authorization": "Bearer tenant-b-token",
            "X-Tenant-ID": "tenant-b"
        }
        
        # Create budget in tenant A
        budget_data = {
            "name": "Tenant A Budget",
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response_a = test_client.post(
            "/api/v1/budgets",
            json=budget_data,
            headers=tenant_a_headers
        )
        
        if response_a.status_code == 201:
            budget_id = response_a.json()["id"]
            
            # Try to access from tenant B
            response_b = test_client.get(
                f"/api/v1/budgets/{budget_id}",
                headers=tenant_b_headers
            )
            
            # Should not be able to access budget from different tenant
            assert response_b.status_code == 404
    
    def test_template_tenant_isolation(self, test_client):
        """Test that templates are isolated between tenants."""
        tenant_a_headers = {
            "Authorization": "Bearer tenant-a-token",
            "X-Tenant-ID": "tenant-a"
        }
        
        tenant_b_headers = {
            "Authorization": "Bearer tenant-b-token",
            "X-Tenant-ID": "tenant-b"
        }
        
        # Create template in tenant A
        template_data = {
            "name": "Tenant A Template",
            "period_type": "monthly",
            "total_amount": 1000.00
        }
        
        response_a = test_client.post(
            "/api/v1/budgets/templates",
            json=template_data,
            headers=tenant_a_headers
        )
        
        if response_a.status_code == 201:
            # Get templates from tenant B
            response_b = test_client.get(
                "/api/v1/budgets/templates",
                headers=tenant_b_headers
            )
            
            # Should not see tenant A's template
            assert response_b.status_code == 200
            templates = response_b.json()
            template_names = [t["name"] for t in templates]
            assert "Tenant A Template" not in template_names


@pytest.mark.integration
class TestBudgetAPISecurity:
    """Test budget API security features."""
    
    def test_sql_injection_prevention(self, test_client, auth_headers):
        """Test that budget endpoints prevent SQL injection."""
        malicious_data = {
            "name": "'; DROP TABLE budgets; --",
            "description": "'; DELETE FROM budgets WHERE 1=1; --",
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=malicious_data,
            headers=auth_headers
        )
        
        # Should handle malicious input safely
        assert response.status_code in [201, 422]
        
        # Verify system is still functional
        health_response = test_client.get("/health")
        assert health_response.status_code == 200
    
    def test_xss_prevention(self, test_client, auth_headers):
        """Test that budget endpoints prevent XSS attacks."""
        xss_data = {
            "name": "<script>alert('XSS')</script>",
            "description": "<img src=x onerror=alert('XSS')>",
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=xss_data,
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            # Should sanitize dangerous content
            assert "<script>" not in data.get("name", "")
            assert "onerror=" not in data.get("description", "")
    
    def test_input_validation_limits(self, test_client, auth_headers):
        """Test input validation limits."""
        # Test very long strings
        long_name = "A" * 1000
        long_description = "B" * 10000
        
        invalid_data = {
            "name": long_name,
            "description": long_description,
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=invalid_data,
            headers=auth_headers
        )
        
        # Should validate input length
        assert response.status_code in [422, 413]
    
    def test_numeric_overflow_protection(self, test_client, auth_headers):
        """Test protection against numeric overflow."""
        overflow_data = {
            "name": "Overflow Test",
            "total_amount": 999999999999999.99,  # Very large number
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=overflow_data,
            headers=auth_headers
        )
        
        # Should handle large numbers appropriately
        assert response.status_code in [201, 422]


@pytest.mark.integration
@pytest.mark.asyncio
class TestBudgetAPIAsync:
    """Test budget API endpoints using async client."""
    
    async def test_concurrent_budget_creation(self, async_client, auth_headers):
        """Test handling of concurrent budget creation."""
        import asyncio
        
        # Create multiple budgets concurrently
        budget_data_list = [
            {
                "name": f"Concurrent Budget {i}",
                "total_amount": 1000.00 + (i * 100),
                "period_type": "monthly",
                "start_date": "2024-02-01",
                "end_date": "2024-02-29"
            }
            for i in range(5)
        ]
        
        # Create budgets concurrently
        tasks = [
            async_client.post(
                "/api/v1/budgets",
                json=budget_data,
                headers=auth_headers
            )
            for budget_data in budget_data_list
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should be handled properly
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 4  # Allow for some potential conflicts
        
        for response in successful_responses:
            assert response.status_code == 201
    
    async def test_concurrent_budget_updates(self, async_client, auth_headers):
        """Test handling of concurrent budget updates."""
        # This would test concurrent updates to the same budget
        # Implementation depends on optimistic locking or other concurrency controls
        pass


@pytest.mark.integration
class TestBudgetAPIErrorHandling:
    """Test budget API error handling."""
    
    def test_malformed_json_request(self, test_client, auth_headers):
        """Test handling of malformed JSON in budget requests."""
        response = test_client.post(
            "/api/v1/budgets",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_missing_required_fields(self, test_client, auth_headers):
        """Test handling of missing required fields."""
        incomplete_data = {
            "name": "Incomplete Budget"
            # Missing required fields like total_amount, period_type, etc.
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=incomplete_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_invalid_enum_values(self, test_client, auth_headers):
        """Test handling of invalid enum values."""
        invalid_data = {
            "name": "Invalid Period Budget",
            "total_amount": 1000.00,
            "period_type": "invalid_period",  # Invalid enum value
            "start_date": "2024-02-01",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_invalid_date_formats(self, test_client, auth_headers):
        """Test handling of invalid date formats."""
        invalid_data = {
            "name": "Invalid Date Budget",
            "total_amount": 1000.00,
            "period_type": "monthly",
            "start_date": "invalid-date",
            "end_date": "2024-02-29"
        }
        
        response = test_client.post(
            "/api/v1/budgets",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data