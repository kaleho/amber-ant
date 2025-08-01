"""Integration tests for families API endpoints."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.main import app
from src.families.models import Family, FamilyMember, FamilyInvitation, SpendingApprovalRequest
from src.families.schemas import FamilyRole, FamilyMemberStatus, InvitationStatus, ApprovalStatus


class TestFamiliesAPI:
    """Test families API endpoints with database integration."""
    
    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_family_data(self):
        """Sample family creation data."""
        return {
            "name": "The Integration Test Family",
            "description": "Family for testing API integration",
            "max_members": 6,
            "plan_type": "premium",
            "settings": {
                "allow_teen_transactions": True,
                "require_approval_over": "100.00"
            },
            "is_active": True
        }
    
    @pytest.fixture
    def sample_member_data(self):
        """Sample family member data."""
        return {
            "name": "Test Member",
            "email": "member@example.com",
            "role": "spouse",
            "spending_limit": "1000.00",
            "requires_approval_over": "500.00",
            "approved_categories": ["Food & Dining", "Transportation"],
            "permissions": {
                "can_view_budgets": True,
                "can_edit_budgets": False,
                "can_create_goals": True
            },
            "status": "active"
        }
    
    @pytest.fixture
    def sample_invitation_data(self):
        """Sample invitation data."""
        return {
            "email": "invite@example.com",
            "role": "teen",
            "message": "Welcome to our family!",
            "permissions": {
                "can_view_budgets": True,
                "spending_limit": "100.00"
            },
            "expires_in_days": 7
        }
    
    @pytest.fixture
    def sample_spending_request_data(self):
        """Sample spending request data."""
        return {
            "amount": "75.00",
            "description": "Game purchase",
            "category": "Entertainment",
            "merchant": "GameStore",
            "expires_in_hours": 24
        }

    # Family CRUD tests
    @pytest.mark.asyncio
    async def test_create_family_success(self, client, auth_headers, sample_family_data):
        """Test successful family creation."""
        response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_family_data["name"]
        assert data["description"] == sample_family_data["description"]
        assert data["max_members"] == sample_family_data["max_members"]
        assert data["current_member_count"] == 1  # Administrator
        assert data["is_active"] is True
        assert "id" in data
        assert "administrator_id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    @pytest.mark.asyncio
    async def test_create_family_validation_errors(self, client, auth_headers):
        """Test family creation validation errors."""
        # Empty name
        response = client.post(
            "/families/",
            json={
                "name": "",
                "max_members": 4
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        
        # Invalid max_members
        response = client.post(
            "/families/",
            json={
                "name": "Test Family",
                "max_members": 1
            },
            headers=auth_headers
        )
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_user_families(self, client, auth_headers, sample_family_data):
        """Test getting user families."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        
        # Get user families
        response = client.get("/families/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(family["name"] == sample_family_data["name"] for family in data)
    
    @pytest.mark.asyncio
    async def test_get_family_by_id(self, client, auth_headers, sample_family_data):
        """Test getting family by ID."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Get family by ID
        response = client.get(f"/families/{family_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == family_id
        assert data["name"] == sample_family_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_family_not_found(self, client, auth_headers):
        """Test getting non-existent family."""
        fake_id = str(uuid4())
        response = client.get(f"/families/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_family_success(self, client, auth_headers, sample_family_data):
        """Test successful family update."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Update family
        update_data = {
            "name": "Updated Family Name",
            "max_members": 8,
            "description": "Updated description"
        }
        response = client.put(
            f"/families/{family_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["max_members"] == update_data["max_members"]
        assert data["description"] == update_data["description"]
    
    @pytest.mark.asyncio
    async def test_update_family_unauthorized(self, client, auth_headers, alt_auth_headers, sample_family_data):
        """Test updating family without administrator permissions."""
        # Create family with first user
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Try to update with different user
        update_data = {"name": "Unauthorized Update"}
        response = client.put(
            f"/families/{family_id}",
            json=update_data,
            headers=alt_auth_headers
        )
        
        assert response.status_code == 404  # Not found due to access control
    
    @pytest.mark.asyncio
    async def test_delete_family_success(self, client, auth_headers, sample_family_data):
        """Test successful family deletion."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Delete family
        response = client.delete(f"/families/{family_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify family is deleted
        get_response = client.get(f"/families/{family_id}", headers=auth_headers)
        assert get_response.status_code == 404

    # Family member tests
    @pytest.mark.asyncio
    async def test_get_family_members(self, client, auth_headers, sample_family_data):
        """Test getting family members."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Get family members
        response = client.get(f"/families/{family_id}/members", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the administrator
        
        # Check administrator member
        admin_member = next((m for m in data if m["role"] == "administrator"), None)
        assert admin_member is not None
        assert admin_member["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_add_family_member_success(self, client, auth_headers, sample_family_data, sample_member_data):
        """Test successful member addition."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Add member
        response = client.post(
            f"/families/{family_id}/members",
            json=sample_member_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_member_data["name"]
        assert data["email"] == sample_member_data["email"]
        assert data["role"] == sample_member_data["role"]
        assert data["family_id"] == family_id
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_add_family_member_validation_errors(self, client, auth_headers, sample_family_data):
        """Test member addition validation errors."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Invalid member data (missing required fields)
        response = client.post(
            f"/families/{family_id}/members",
            json={
                "name": "",  # Empty name
                "email": "invalid-email",  # Invalid email
                "role": "invalid_role"  # Invalid role
            },
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_update_family_member_success(self, client, auth_headers, sample_family_data, sample_member_data):
        """Test successful member update."""
        # Create family and add member
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        member_response = client.post(
            f"/families/{family_id}/members",
            json=sample_member_data,
            headers=auth_headers
        )
        member_id = member_response.json()["id"]
        
        # Update member
        update_data = {
            "role": "teen",
            "spending_limit": "200.00",
            "requires_approval_over": "50.00"
        }
        response = client.put(
            f"/families/members/{member_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == update_data["role"]
        assert str(data["spending_limit"]) == update_data["spending_limit"]
    
    @pytest.mark.asyncio
    async def test_remove_family_member_success(self, client, auth_headers, sample_family_data, sample_member_data):
        """Test successful member removal."""
        # Create family and add member
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        member_response = client.post(
            f"/families/{family_id}/members",
            json=sample_member_data,
            headers=auth_headers
        )
        member_id = member_response.json()["id"]
        
        # Remove member
        response = client.delete(f"/families/members/{member_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify member is removed
        members_response = client.get(f"/families/{family_id}/members", headers=auth_headers)
        members = members_response.json()
        assert not any(m["id"] == member_id for m in members)

    # Family invitation tests
    @pytest.mark.asyncio
    async def test_create_invitation_success(self, client, auth_headers, sample_family_data, sample_invitation_data):
        """Test successful invitation creation."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Create invitation
        response = client.post(
            f"/families/{family_id}/invitations",
            json=sample_invitation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_invitation_data["email"]
        assert data["role"] == sample_invitation_data["role"]
        assert data["message"] == sample_invitation_data["message"]
        assert data["family_id"] == family_id
        assert data["status"] == "pending"
        assert "invitation_token" in data
        assert "expires_at" in data
    
    @pytest.mark.asyncio
    async def test_get_family_invitations(self, client, auth_headers, sample_family_data, sample_invitation_data):
        """Test getting family invitations."""
        # Create family and invitation
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        client.post(
            f"/families/{family_id}/invitations",
            json=sample_invitation_data,
            headers=auth_headers
        )
        
        # Get invitations
        response = client.get(f"/families/{family_id}/invitations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(inv["email"] == sample_invitation_data["email"] for inv in data)
    
    @pytest.mark.asyncio
    async def test_get_invitation_details(self, client, auth_headers, sample_family_data, sample_invitation_data):
        """Test getting invitation details by token."""
        # Create family and invitation
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        invitation_response = client.post(
            f"/families/{family_id}/invitations",
            json=sample_invitation_data,
            headers=auth_headers
        )
        invitation_token = invitation_response.json()["invitation_token"]
        
        # Get invitation details
        response = client.get(f"/families/invitations/{invitation_token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["family_name"] == sample_family_data["name"]
        assert data["role"] == sample_invitation_data["role"]
        assert data["message"] == sample_invitation_data["message"]
        assert "expires_at" in data
    
    @pytest.mark.asyncio
    async def test_accept_invitation_success(self, client, auth_headers, alt_auth_headers, sample_family_data, sample_invitation_data):
        """Test successful invitation acceptance."""
        # Create family and invitation with first user
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        invitation_response = client.post(
            f"/families/{family_id}/invitations",
            json=sample_invitation_data,
            headers=auth_headers
        )
        invitation_token = invitation_response.json()["invitation_token"]
        
        # Accept invitation with second user
        response = client.post(
            f"/families/invitations/{invitation_token}/accept",
            headers=alt_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["family_id"] == family_id
        assert data["role"] == sample_invitation_data["role"]
        assert data["status"] == "active"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_accept_invalid_invitation(self, client, alt_auth_headers):
        """Test accepting invalid invitation."""
        fake_token = "inv_invalid_token"
        
        response = client.post(
            f"/families/invitations/{fake_token}/accept",
            headers=alt_auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_cancel_invitation_success(self, client, auth_headers, sample_family_data, sample_invitation_data):
        """Test successful invitation cancellation."""
        # Create family and invitation
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        invitation_response = client.post(
            f"/families/{family_id}/invitations",
            json=sample_invitation_data,
            headers=auth_headers
        )
        invitation_id = invitation_response.json()["id"]
        
        # Cancel invitation
        response = client.delete(
            f"/families/invitations/{invitation_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204

    # Spending approval tests
    @pytest.mark.asyncio
    async def test_create_spending_request_success(self, client, auth_headers, sample_family_data, sample_spending_request_data):
        """Test successful spending request creation."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Create spending request
        response = client.post(
            f"/families/{family_id}/spending-requests",
            json=sample_spending_request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert str(data["amount"]) == sample_spending_request_data["amount"]
        assert data["description"] == sample_spending_request_data["description"]
        assert data["category"] == sample_spending_request_data["category"]
        assert data["merchant"] == sample_spending_request_data["merchant"]
        assert data["family_id"] == family_id
        assert data["status"] == "pending"
        assert "expires_at" in data
    
    @pytest.mark.asyncio
    async def test_get_pending_spending_requests(self, client, auth_headers, sample_family_data, sample_spending_request_data):
        """Test getting pending spending requests."""
        # Create family and spending request
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        client.post(
            f"/families/{family_id}/spending-requests",
            json=sample_spending_request_data,
            headers=auth_headers
        )
        
        # Get pending requests
        response = client.get(
            f"/families/{family_id}/spending-requests",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(req["description"] == sample_spending_request_data["description"] for req in data)
    
    @pytest.mark.asyncio
    async def test_process_spending_approval_success(self, client, auth_headers, sample_family_data, sample_spending_request_data):
        """Test successful spending approval processing."""
        # Create family and spending request
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        request_response = client.post(
            f"/families/{family_id}/spending-requests",
            json=sample_spending_request_data,
            headers=auth_headers
        )
        request_id = request_response.json()["id"]
        
        # Process approval
        decision_data = {
            "decision": "approved",
            "notes": "Approved for good behavior"
        }
        response = client.post(
            f"/families/spending-requests/{request_id}/decision",
            json=decision_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["approval_notes"] == decision_data["notes"]
        assert "approved_at" in data
        assert "approved_by" in data
    
    @pytest.mark.asyncio
    async def test_process_spending_denial(self, client, auth_headers, sample_family_data, sample_spending_request_data):
        """Test spending request denial."""
        # Create family and spending request
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        request_response = client.post(
            f"/families/{family_id}/spending-requests",
            json=sample_spending_request_data,
            headers=auth_headers
        )
        request_id = request_response.json()["id"]
        
        # Deny request
        decision_data = {
            "decision": "denied",
            "notes": "Not within budget"
        }
        response = client.post(
            f"/families/spending-requests/{request_id}/decision",
            json=decision_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "denied"
        assert data["approval_notes"] == decision_data["notes"]

    # Dashboard tests
    @pytest.mark.asyncio
    async def test_get_family_dashboard(self, client, auth_headers, sample_family_data):
        """Test getting family dashboard data."""
        # Create a family first
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Get dashboard
        response = client.get(f"/families/{family_id}/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["family_id"] == family_id
        assert "member_count" in data
        assert "pending_invitations" in data
        assert "pending_approvals" in data
        assert "shared_budgets" in data
        assert "shared_goals" in data
        assert "total_family_spending" in data
        assert "recent_activities" in data
        assert "upcoming_approvals" in data
        
        # Verify basic counts
        assert data["member_count"] >= 1  # At least administrator
        assert data["pending_invitations"] >= 0
        assert data["pending_approvals"] >= 0

    # Multi-tenant isolation tests
    @pytest.mark.asyncio
    async def test_family_isolation_between_tenants(self, client, auth_headers, alt_auth_headers, sample_family_data):
        """Test that families are isolated between different tenants."""
        # Create family with first user (tenant 1)
        response1 = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = response1.json()["id"]
        
        # Try to access family with second user (different tenant)
        response2 = client.get(f"/families/{family_id}", headers=alt_auth_headers)
        
        assert response2.status_code == 404  # Should not have access
    
    @pytest.mark.asyncio
    async def test_member_isolation_between_families(self, client, auth_headers, alt_auth_headers, sample_family_data, sample_member_data):
        """Test that members are isolated between different families."""
        # Create family with first user
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Add member to family
        member_response = client.post(
            f"/families/{family_id}/members",
            json=sample_member_data,
            headers=auth_headers
        )
        member_id = member_response.json()["id"]
        
        # Try to access member with different user
        response = client.put(
            f"/families/members/{member_id}",
            json={"role": "teen"},
            headers=alt_auth_headers
        )
        
        assert response.status_code == 404  # Should not have access

    # Performance and edge case tests
    @pytest.mark.asyncio
    async def test_family_member_limit_enforcement(self, client, auth_headers, sample_member_data):
        """Test that family member limits are enforced."""
        # Create family with low member limit
        family_data = {
            "name": "Small Family",
            "max_members": 2  # Only administrator + 1 member
        }
        
        create_response = client.post(
            "/families/",
            json=family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Add first member (should succeed)
        response1 = client.post(
            f"/families/{family_id}/members",
            json=sample_member_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Try to add second member (should fail due to limit)
        sample_member_data["email"] = "second@example.com"
        response2 = client.post(
            f"/families/{family_id}/members",
            json=sample_member_data,
            headers=auth_headers
        )
        assert response2.status_code == 403  # Forbidden due to member limit
    
    @pytest.mark.asyncio
    async def test_invitation_expiration_handling(self, client, auth_headers, alt_auth_headers, sample_family_data):
        """Test handling of expired invitations."""
        # Create family
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Create invitation with very short expiration
        invitation_data = {
            "email": "expire@example.com",
            "role": "teen",
            "expires_in_days": 1
        }
        
        invitation_response = client.post(
            f"/families/{family_id}/invitations",
            json=invitation_data,
            headers=auth_headers
        )
        invitation_token = invitation_response.json()["invitation_token"]
        
        # Simulate expired invitation by checking details after expiration
        # In a real test, you might manipulate the database or use time mocking
        response = client.get(f"/families/invitations/{invitation_token}")
        
        # Should still work if not actually expired
        # In production, this would need proper time mocking
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_spending_request_validation_limits(self, client, auth_headers, sample_family_data):
        """Test spending request validation with various limits."""
        # Create family
        create_response = client.post(
            "/families/",
            json=sample_family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Test various invalid amounts
        invalid_requests = [
            {"amount": "0", "description": "Zero amount"},
            {"amount": "-50.00", "description": "Negative amount"},
            {"amount": "abc", "description": "Invalid amount format"},
        ]
        
        for invalid_request in invalid_requests:
            response = client.post(
                f"/families/{family_id}/spending-requests",
                json={
                    **invalid_request,
                    "category": "Test",
                    "expires_in_hours": 24
                },
                headers=auth_headers
            )
            assert response.status_code in [400, 422]  # Validation error

    # Maintenance operations tests
    @pytest.mark.asyncio
    async def test_cleanup_expired_invitations(self, client, auth_headers):
        """Test cleanup of expired invitations."""
        response = client.post(
            "/families/maintenance/cleanup-invitations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cleaned_up" in data
        assert isinstance(data["cleaned_up"], int)
        assert data["cleaned_up"] >= 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_approvals(self, client, auth_headers):
        """Test cleanup of expired approval requests."""
        response = client.post(
            "/families/maintenance/cleanup-approvals",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cleaned_up" in data
        assert isinstance(data["cleaned_up"], int)
        assert data["cleaned_up"] >= 0


class TestFamiliesAPIErrorHandling:
    """Test error handling and edge cases for families API."""
    
    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_unauthenticated_access(self, client):
        """Test that endpoints require authentication."""
        endpoints = [
            ("GET", "/families/"),
            ("POST", "/families/"),
            ("GET", "/families/fake-id"),
            ("PUT", "/families/fake-id"),
            ("DELETE", "/families/fake-id"),
        ]
        
        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_malformed_json_requests(self, client, auth_headers):
        """Test handling of malformed JSON requests."""
        # Invalid JSON
        response = client.post(
            "/families/",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client, auth_headers):
        """Test that SQL injection attempts are prevented."""
        # Attempt SQL injection in family name
        malicious_data = {
            "name": "'; DROP TABLE families; --",
            "max_members": 4
        }
        
        response = client.post(
            "/families/",
            json=malicious_data,
            headers=auth_headers
        )
        
        # Should either succeed (treating as normal string) or fail validation
        # But should not cause SQL injection
        assert response.status_code in [201, 400, 422]
        
        # Verify families table still exists by making another request
        get_response = client.get("/families/", headers=auth_headers)
        assert get_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_xss_prevention_in_responses(self, client, auth_headers):
        """Test that XSS payloads are properly handled."""
        xss_payload = "<script>alert('xss')</script>"
        
        family_data = {
            "name": xss_payload,
            "description": f"Description {xss_payload}",
            "max_members": 4
        }
        
        response = client.post(
            "/families/",
            json=family_data,
            headers=auth_headers
        )
        
        # Should succeed and return escaped/sanitized data
        if response.status_code == 201:
            data = response.json()
            # The API should return the data as-is (FastAPI handles JSON encoding)
            # XSS prevention happens at the frontend
            assert data["name"] == xss_payload
            assert data["description"] == f"Description {xss_payload}"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, client, auth_headers):
        """Test behavior under rapid requests (basic load test)."""
        family_data = {
            "name": "Rate Limit Test Family",
            "max_members": 4
        }
        
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.post(
                "/families/",
                json={**family_data, "name": f"Family {i}"},
                headers=auth_headers
            )
            responses.append(response)
        
        # Most should succeed (assuming no rate limiting implemented)
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count >= 5  # At least half should succeed
    
    @pytest.mark.asyncio
    async def test_concurrent_family_operations(self, client, auth_headers):
        """Test concurrent operations on the same family."""
        # Create a family
        family_data = {"name": "Concurrent Test Family", "max_members": 10}
        create_response = client.post(
            "/families/",
            json=family_data,
            headers=auth_headers
        )
        family_id = create_response.json()["id"]
        
        # Simulate concurrent member additions
        member_data_template = {
            "name": "Test Member",
            "email": "member{}@example.com",
            "role": "teen"
        }
        
        responses = []
        for i in range(5):
            member_data = {**member_data_template, "email": f"member{i}@example.com"}
            response = client.post(
                f"/families/{family_id}/members",
                json=member_data,
                headers=auth_headers
            )
            responses.append(response)
        
        # Most should succeed if within family limits
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count >= 3  # At least some should succeed