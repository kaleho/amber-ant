"""Integration tests for tithing API endpoints."""
import pytest
from httpx import AsyncClient
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
import json

from src.main import app
from src.database import get_tenant_database_session
from src.tenant.context import set_tenant_context


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
def sample_payment_data():
    """Sample payment data for API tests."""
    return {
        "amount": 150.00,
        "date": date.today().isoformat(),
        "method": "online",
        "recipient": "First Baptist Church",
        "recipient_address": "123 Church St, City, State 12345",
        "reference_number": "TXN-123456",
        "notes": "Monthly tithe payment",
        "purpose": "regular_tithe",
        "is_tax_deductible": True
    }


@pytest.fixture
def sample_schedule_data():
    """Sample schedule data for API tests."""
    return {
        "name": "Monthly Tithe",
        "amount": 200.00,
        "frequency": "monthly",
        "recipient": "First Baptist Church",
        "start_date": date.today().isoformat(),
        "end_date": (date.today().replace(year=date.today().year + 1)).isoformat(),
        "is_active": True,
        "auto_execute": False
    }


@pytest.fixture
def sample_goal_data():
    """Sample goal data for API tests."""
    return {
        "name": "Annual Tithe Goal",
        "target_amount": 2400.00,
        "target_percentage": 10.0,
        "year": 2024,
        "description": "10% of annual income goal"
    }


class TestTithingPaymentAPI:
    """Test tithing payment API endpoints."""

    @pytest.mark.asyncio
    async def test_create_payment_success(self, client, auth_headers, sample_payment_data):
        """Test successful payment creation via API."""
        # Mock authentication and authorization
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.auth.dependencies.require_permission') as mock_perm:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_perm.return_value = True
            
            response = await client.post(
                "/api/v1/tithing/payments",
                headers=auth_headers,
                json=sample_payment_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["amount"] == "150.00"
            assert data["recipient"] == "First Baptist Church"
            assert data["method"] == "online"

    @pytest.mark.asyncio
    async def test_create_payment_validation_error(self, client, auth_headers):
        """Test payment creation with invalid data."""
        invalid_data = {
            "amount": -50.00,  # Negative amount
            "date": "invalid-date",
            "method": "invalid_method",
            "recipient": ""  # Empty recipient
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            response = await client.post(
                "/api/v1/tithing/payments",
                headers=auth_headers,
                json=invalid_data
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "validation_failed" in data["error"]

    @pytest.mark.asyncio
    async def test_get_payment_success(self, client, auth_headers):
        """Test successful payment retrieval."""
        payment_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.get_payment') as mock_get:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_payment = Mock()
            mock_payment.id = payment_id
            mock_payment.amount = Decimal("150.00")
            mock_payment.recipient = "First Baptist Church"
            mock_get.return_value = mock_payment
            
            response = await client.get(
                f"/api/v1/tithing/payments/{payment_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == payment_id

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, client, auth_headers):
        """Test payment retrieval when payment not found."""
        payment_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.get_payment') as mock_get:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_get.side_effect = NotFoundError("Tithing payment not found")
            
            response = await client.get(
                f"/api/v1/tithing/payments/{payment_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_update_payment_success(self, client, auth_headers):
        """Test successful payment update."""
        payment_id = str(uuid4())
        update_data = {
            "amount": 175.00,
            "notes": "Updated monthly tithe payment"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.update_payment') as mock_update:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_updated_payment = Mock()
            mock_updated_payment.id = payment_id
            mock_updated_payment.amount = Decimal("175.00")
            mock_update.return_value = mock_updated_payment
            
            response = await client.put(
                f"/api/v1/tithing/payments/{payment_id}",
                headers=auth_headers,
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["amount"] == "175.00"

    @pytest.mark.asyncio
    async def test_delete_payment_success(self, client, auth_headers):
        """Test successful payment deletion."""
        payment_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.delete_payment') as mock_delete:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_delete.return_value = True
            
            response = await client.delete(
                f"/api/v1/tithing/payments/{payment_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_list_payments_with_filters(self, client, auth_headers):
        """Test listing payments with various filters."""
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "method": "online",
            "recipient": "First Baptist Church",
            "limit": 10,
            "offset": 0
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.list_payments') as mock_list:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_payments = [Mock() for _ in range(5)]
            mock_list.return_value = mock_payments
            
            response = await client.get(
                "/api/v1/tithing/payments",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["payments"]) == 5

    @pytest.mark.asyncio
    async def test_get_payment_analytics(self, client, auth_headers):
        """Test payment analytics endpoint."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.get_payment_analytics') as mock_analytics:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_analytics_data = {
                "total_amount": Decimal("1800.00"),
                "payment_count": 12,
                "average_payment": Decimal("150.00"),
                "monthly_breakdown": {},
                "method_breakdown": {},
                "recipient_breakdown": {}
            }
            mock_analytics.return_value = mock_analytics_data
            
            response = await client.get(
                "/api/v1/tithing/payments/analytics",
                headers=auth_headers,
                params={"year": 2024}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_amount"] == "1800.00"
            assert data["payment_count"] == 12


class TestTithingScheduleAPI:
    """Test tithing schedule API endpoints."""

    @pytest.mark.asyncio
    async def test_create_schedule_success(self, client, auth_headers, sample_schedule_data):
        """Test successful schedule creation."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.create_schedule') as mock_create:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_schedule = Mock()
            mock_schedule.id = str(uuid4())
            mock_schedule.name = "Monthly Tithe"
            mock_create.return_value = mock_schedule
            
            response = await client.post(
                "/api/v1/tithing/schedules",
                headers=auth_headers,
                json=sample_schedule_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Monthly Tithe"

    @pytest.mark.asyncio
    async def test_generate_schedule_payments(self, client, auth_headers):
        """Test generating payments from schedule."""
        schedule_id = str(uuid4())
        query_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-03-31"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.generate_schedule_payments') as mock_generate:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_payments = [Mock() for _ in range(3)]  # 3 months
            mock_generate.return_value = mock_payments
            
            response = await client.post(
                f"/api/v1/tithing/schedules/{schedule_id}/generate",
                headers=auth_headers,
                params=query_params
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["generated_payments"]) == 3

    @pytest.mark.asyncio
    async def test_execute_due_schedules(self, client, auth_headers):
        """Test executing due scheduled payments."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.auth.dependencies.require_permission') as mock_perm, \
             patch('src.tithing.service.TithingService.execute_due_schedules') as mock_execute:
            
            mock_auth.return_value = {"sub": "admin123", "email": "admin@example.com"}
            mock_perm.return_value = True  # Admin permission
            mock_result = {
                "executed_count": 5,
                "total_amount": Decimal("1000.00"),
                "failed_count": 0
            }
            mock_execute.return_value = mock_result
            
            response = await client.post(
                "/api/v1/tithing/schedules/execute-due",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["executed_count"] == 5
            assert data["total_amount"] == "1000.00"


class TestTithingGoalAPI:
    """Test tithing goal API endpoints."""

    @pytest.mark.asyncio
    async def test_create_goal_success(self, client, auth_headers, sample_goal_data):
        """Test successful goal creation."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.create_goal') as mock_create:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_goal = Mock()
            mock_goal.id = str(uuid4())
            mock_goal.name = "Annual Tithe Goal"
            mock_create.return_value = mock_goal
            
            response = await client.post(
                "/api/v1/tithing/goals",
                headers=auth_headers,
                json=sample_goal_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Annual Tithe Goal"

    @pytest.mark.asyncio
    async def test_get_goal_progress(self, client, auth_headers):
        """Test goal progress retrieval."""
        year = 2024
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.calculate_goal_progress') as mock_progress:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_progress_data = {
                "goal": Mock(),
                "total_paid": Decimal("1200.00"),
                "remaining_amount": Decimal("1200.00"),
                "progress_percentage": Decimal("50.0"),
                "is_on_track": False
            }
            mock_progress.return_value = mock_progress_data
            
            response = await client.get(
                f"/api/v1/tithing/goals/progress/{year}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_paid"] == "1200.00"
            assert data["progress_percentage"] == "50.0"

    @pytest.mark.asyncio
    async def test_get_goal_recommendations(self, client, auth_headers):
        """Test goal recommendations."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.get_goal_recommendations') as mock_recommendations:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_rec_data = {
                "recommended_percentage": Decimal("10.0"),
                "recommended_amount": Decimal("6000.00"),
                "suggested_monthly_amount": Decimal("500.00"),
                "historical_average": Decimal("2800.00")
            }
            mock_recommendations.return_value = mock_rec_data
            
            response = await client.get(
                "/api/v1/tithing/goals/recommendations",
                headers=auth_headers,
                params={"annual_income": 60000.00}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["recommended_percentage"] == "10.0"
            assert data["recommended_amount"] == "6000.00"


class TestTithingAnalyticsAPI:
    """Test tithing analytics API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_annual_summary(self, client, auth_headers):
        """Test annual summary generation."""
        year = 2024
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.generate_annual_summary') as mock_summary:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_summary_data = {
                "total_amount": Decimal("3600.00"),
                "payment_count": 12,
                "average_payment": Decimal("300.00"),
                "monthly_consistency_score": Decimal("95.0")
            }
            mock_summary.return_value = mock_summary_data
            
            response = await client.get(
                f"/api/v1/tithing/analytics/summary/{year}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_amount"] == "3600.00"
            assert data["payment_count"] == 12

    @pytest.mark.asyncio
    async def test_get_giving_trends(self, client, auth_headers):
        """Test giving trends analysis."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.get_giving_trends') as mock_trends:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_trends_data = {
                "yearly_totals": {
                    "2022": Decimal("2400.00"),
                    "2023": Decimal("3000.00"),
                    "2024": Decimal("3600.00")
                },
                "growth_rate": Decimal("25.0"),
                "trend_direction": "increasing"
            }
            mock_trends.return_value = mock_trends_data
            
            response = await client.get(
                "/api/v1/tithing/analytics/trends",
                headers=auth_headers,
                params={"years": "2022,2023,2024"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["growth_rate"] == "25.0"
            assert data["trend_direction"] == "increasing"

    @pytest.mark.asyncio
    async def test_calculate_tax_summary(self, client, auth_headers):
        """Test tax summary calculation."""
        tax_year = 2024
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.calculate_tax_summary') as mock_tax:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_tax_data = {
                "total_deductible": Decimal("3400.00"),
                "total_non_deductible": Decimal("200.00"),
                "payment_count": 12,
                "organizations": [
                    {
                        "name": "First Baptist Church",
                        "total": Decimal("3000.00"),
                        "payment_count": 10
                    }
                ]
            }
            mock_tax.return_value = mock_tax_data
            
            response = await client.get(
                f"/api/v1/tithing/analytics/tax-summary/{tax_year}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_deductible"] == "3400.00"
            assert len(data["organizations"]) == 1

    @pytest.mark.asyncio
    async def test_generate_giving_receipt(self, client, auth_headers):
        """Test giving receipt generation."""
        year = 2024
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.generate_giving_receipt') as mock_receipt:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_receipt_data = {
                "receipt_number": "RECEIPT-2024-USER123A",
                "year": year,
                "total_deductible": Decimal("3600.00"),
                "payment_count": 12,
                "generated_date": datetime.utcnow().isoformat(),
                "organizations": [
                    {
                        "name": "First Baptist Church",
                        "total": Decimal("3600.00"),
                        "payments": 12
                    }
                ]
            }
            mock_receipt.return_value = mock_receipt_data
            
            response = await client.post(
                f"/api/v1/tithing/analytics/receipt/{year}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["receipt_number"].startswith("RECEIPT-2024")
            assert data["total_deductible"] == "3600.00"


class TestTithingAPIPermissions:
    """Test API permission and authorization."""

    @pytest.mark.asyncio
    async def test_create_payment_unauthorized(self, client, sample_payment_data):
        """Test payment creation without authentication."""
        response = await client.post(
            "/api/v1/tithing/payments",
            json=sample_payment_data
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_only_endpoints(self, client, auth_headers):
        """Test endpoints requiring admin permissions."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.auth.dependencies.require_permission') as mock_perm:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_perm.side_effect = Exception("Insufficient permissions")
            
            # Test admin-only endpoint
            response = await client.post(
                "/api/v1/tithing/schedules/execute-due",
                headers=auth_headers
            )
            
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, client, auth_headers):
        """Test that tithing data is properly isolated by tenant."""
        # This would test multi-tenant data isolation
        # Implementation depends on tenant context middleware
        payment_id = str(uuid4())
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tenant.context.get_tenant_context') as mock_tenant:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_tenant.return_value = Mock(tenant_id="tenant1")
            
            # User from tenant1 should not access tenant2 data
            response = await client.get(
                f"/api/v1/tithing/payments/{payment_id}",
                headers={**auth_headers, "X-Tenant-ID": "tenant2"}
            )
            
            # Should handle tenant mismatch appropriately
            assert response.status_code in [404, 403]


class TestTithingAPIValidation:
    """Test API input validation and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_payment_data_validation(self, client, auth_headers):
        """Test comprehensive payment data validation."""
        invalid_test_cases = [
            # Negative amount
            {"amount": -100.00, "date": "2024-01-01", "method": "cash", "recipient": "Church"},
            # Invalid date format
            {"amount": 100.00, "date": "invalid-date", "method": "cash", "recipient": "Church"},
            # Invalid method
            {"amount": 100.00, "date": "2024-01-01", "method": "invalid", "recipient": "Church"},
            # Empty recipient
            {"amount": 100.00, "date": "2024-01-01", "method": "cash", "recipient": ""},
            # Amount too large
            {"amount": 999999.00, "date": "2024-01-01", "method": "cash", "recipient": "Church"}
        ]
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            for invalid_data in invalid_test_cases:
                response = await client.post(
                    "/api/v1/tithing/payments",
                    headers=auth_headers,
                    json=invalid_data
                )
                
                assert response.status_code == 422
                data = response.json()
                assert "validation_failed" in data["error"]

    @pytest.mark.asyncio
    async def test_pagination_validation(self, client, auth_headers):
        """Test pagination parameter validation."""
        invalid_pagination_cases = [
            {"limit": -1, "offset": 0},  # Negative limit
            {"limit": 1000, "offset": 0},  # Limit too large
            {"limit": 10, "offset": -1}  # Negative offset
        ]
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            for invalid_params in invalid_pagination_cases:
                response = await client.get(
                    "/api/v1/tithing/payments",
                    headers=auth_headers,
                    params=invalid_params
                )
                
                assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_date_range_validation(self, client, auth_headers):
        """Test date range validation in API calls."""
        # End date before start date
        invalid_params = {
            "start_date": "2024-12-31",
            "end_date": "2024-01-01"
        }
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            
            response = await client.get(
                "/api/v1/tithing/payments",
                headers=auth_headers,
                params=invalid_params
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "validation_failed" in data["error"]


class TestTithingAPIPerformance:
    """Test API performance and efficiency."""

    @pytest.mark.asyncio
    async def test_large_payment_list_performance(self, client, auth_headers):
        """Test performance with large payment lists."""
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.list_payments') as mock_list:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            # Simulate large dataset
            mock_payments = [Mock() for _ in range(1000)]
            mock_list.return_value = mock_payments
            
            start_time = datetime.utcnow()
            response = await client.get(
                "/api/v1/tithing/payments",
                headers=auth_headers,
                params={"limit": 1000}
            )
            end_time = datetime.utcnow()
            
            assert response.status_code == 200
            # Should complete within reasonable time
            assert (end_time - start_time).total_seconds() < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_payment_creation(self, client, auth_headers, sample_payment_data):
        """Test concurrent payment creation handling."""
        import asyncio
        
        with patch('src.auth.dependencies.get_current_user') as mock_auth, \
             patch('src.tithing.service.TithingService.create_payment') as mock_create:
            
            mock_auth.return_value = {"sub": "user123", "email": "test@example.com"}
            mock_payment = Mock()
            mock_create.return_value = mock_payment
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(10):
                task = client.post(
                    "/api/v1/tithing/payments",
                    headers=auth_headers,
                    json={**sample_payment_data, "reference_number": f"TXN-{i}"}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 201