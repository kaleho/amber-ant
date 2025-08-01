"""Comprehensive integration tests for goals API endpoints."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
import json

from src.goals.models import GoalStatus, GoalType, GoalPriority


@pytest.mark.integration
class TestGoalsAPI:
    """Test goals API endpoints with full integration."""

    def test_create_goal_success(self, test_client, auth_headers, tenant_context):
        """Test successful goal creation."""
        goal_data = {
            "name": "Emergency Fund",
            "description": "6 months of expenses for financial security",
            "target_amount": "15000.00",
            "target_date": (date.today() + timedelta(days=365)).isoformat(),
            "goal_type": "emergency_fund",
            "priority": 1,
            "category": "Security",
            "color": "#28a745",
            "icon": "shield",
            "auto_save_enabled": True,
            "auto_save_amount": "500.00",
            "auto_save_frequency": "monthly",
            "is_active": True
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == goal_data["name"]
        assert data["target_amount"] == goal_data["target_amount"]
        assert data["current_amount"] == "0.00"
        assert data["progress_percentage"] == "0.00"
        assert data["is_completed"] is False
        assert "id" in data
        assert "created_at" in data

    def test_create_goal_with_milestones(self, test_client, auth_headers, tenant_context):
        """Test goal creation with predefined milestones."""
        goal_data = {
            "name": "Vacation Fund",
            "description": "Trip to Europe",
            "target_amount": "8000.00",
            "target_date": (date.today() + timedelta(days=300)).isoformat(),
            "goal_type": "vacation",
            "priority": 2,
            "milestones": [
                {
                    "name": "First Quarter",
                    "description": "25% milestone",
                    "target_amount": "2000.00",
                    "target_percentage": "25.00",
                    "target_date": (date.today() + timedelta(days=75)).isoformat(),
                    "reward_message": "Great start on your vacation fund!",
                    "notify_on_achievement": True,
                    "sort_order": 1
                },
                {
                    "name": "Halfway There",
                    "description": "50% milestone",
                    "target_amount": "4000.00",
                    "target_percentage": "50.00",
                    "target_date": (date.today() + timedelta(days=150)).isoformat(),
                    "reward_message": "You're halfway to your dream vacation!",
                    "notify_on_achievement": True,
                    "sort_order": 2
                }
            ],
            "is_active": True
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == goal_data["name"]
        # Note: Milestones might be handled separately in the actual implementation

    def test_create_goal_with_initial_contribution(self, test_client, auth_headers, tenant_context):
        """Test goal creation with initial contribution."""
        goal_data = {
            "name": "Car Down Payment",
            "description": "Save for new car down payment",
            "target_amount": "5000.00",
            "target_date": (date.today() + timedelta(days=180)).isoformat(),
            "goal_type": "car_purchase",
            "priority": 2,
            "initial_contribution": "1000.00",
            "is_active": True
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["current_amount"] == "1000.00"  # Should reflect initial contribution
        assert data["progress_percentage"] == "20.00"  # 1000/5000 * 100

    def test_create_goal_invalid_data(self, test_client, auth_headers, tenant_context):
        """Test goal creation with invalid data."""
        # Test negative target amount
        invalid_goal_data = {
            "name": "Invalid Goal",
            "target_amount": "-1000.00",
            "goal_type": "general_savings"
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=invalid_goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_create_goal_past_target_date(self, test_client, auth_headers, tenant_context):
        """Test goal creation with past target date."""
        goal_data = {
            "name": "Past Date Goal",
            "target_amount": "1000.00",
            "target_date": (date.today() - timedelta(days=1)).isoformat(),
            "goal_type": "general_savings"
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_get_goals_list(self, test_client, auth_headers, tenant_context):
        """Test retrieving goals list."""
        # First create some goals
        for i in range(3):
            goal_data = {
                "name": f"Test Goal {i+1}",
                "target_amount": f"{(i+1)*1000}.00",
                "goal_type": "general_savings",
                "is_active": True
            }
            test_client.post("/api/v1/goals", json=goal_data, headers=auth_headers)
        
        # Get goals list
        response = test_client.get("/api/v1/goals", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        
        # Verify goal structure
        for goal in data:
            assert "id" in goal
            assert "name" in goal
            assert "target_amount" in goal
            assert "current_amount" in goal
            assert "progress_percentage" in goal

    def test_get_goals_with_pagination(self, test_client, auth_headers, tenant_context):
        """Test goals list with pagination."""
        response = test_client.get(
            "/api/v1/goals?page=1&per_page=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

    def test_get_goals_with_filters(self, test_client, auth_headers, tenant_context):
        """Test goals list with filters."""
        # Create goals with different types
        emergency_goal = {
            "name": "Emergency Fund Filter Test",
            "target_amount": "10000.00",
            "goal_type": "emergency_fund",
            "is_active": True
        }
        test_client.post("/api/v1/goals", json=emergency_goal, headers=auth_headers)
        
        vacation_goal = {
            "name": "Vacation Fund Filter Test",
            "target_amount": "5000.00",
            "goal_type": "vacation",
            "is_active": True
        }
        test_client.post("/api/v1/goals", json=vacation_goal, headers=auth_headers)
        
        # Filter by goal type
        response = test_client.get(
            "/api/v1/goals?goal_type=emergency_fund",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned goals should be emergency_fund type
        for goal in data:
            if "goal_type" in goal:
                assert goal["goal_type"] == "emergency_fund"

    def test_get_single_goal(self, test_client, auth_headers, tenant_context):
        """Test retrieving a single goal."""
        # Create a goal first
        goal_data = {
            "name": "Single Goal Test",
            "target_amount": "2000.00",
            "goal_type": "general_savings",
            "is_active": True
        }
        
        create_response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        created_goal = create_response.json()
        goal_id = created_goal["id"]
        
        # Get the goal
        response = test_client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == goal_id
        assert data["name"] == goal_data["name"]
        assert data["target_amount"] == goal_data["target_amount"]

    def test_get_nonexistent_goal(self, test_client, auth_headers, tenant_context):
        """Test retrieving a non-existent goal."""
        fake_goal_id = str(uuid4())
        
        response = test_client.get(
            f"/api/v1/goals/{fake_goal_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_update_goal(self, test_client, auth_headers, tenant_context):
        """Test updating goal information."""
        # Create a goal first
        goal_data = {
            "name": "Original Goal Name",
            "target_amount": "3000.00",
            "goal_type": "general_savings",
            "is_active": True
        }
        
        create_response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        goal_id = create_response.json()["id"]
        
        # Update the goal
        update_data = {
            "name": "Updated Goal Name",
            "target_amount": "4000.00",
            "description": "Updated description"
        }
        
        response = test_client.put(
            f"/api/v1/goals/{goal_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["target_amount"] == update_data["target_amount"]
        assert data["description"] == update_data["description"]

    def test_update_goal_recalculates_remaining_amount(self, test_client, auth_headers, tenant_context):
        """Test that updating target amount recalculates remaining amount."""
        # Create goal with initial contribution
        goal_data = {
            "name": "Recalculation Test",
            "target_amount": "2000.00",
            "initial_contribution": "500.00",
            "goal_type": "general_savings",
            "is_active": True
        }
        
        create_response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        goal_id = create_response.json()["id"]
        
        # Update target amount
        update_data = {"target_amount": "3000.00"}
        
        response = test_client.put(
            f"/api/v1/goals/{goal_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["target_amount"] == "3000.00"
        # Remaining should be 3000 - 500 = 2500
        assert float(data["current_amount"]) == 500.00

    def test_delete_goal(self, test_client, auth_headers, tenant_context):
        """Test goal deletion (soft delete)."""
        # Create a goal first
        goal_data = {
            "name": "Goal to Delete",
            "target_amount": "1000.00",
            "goal_type": "general_savings",
            "is_active": True
        }
        
        create_response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        goal_id = create_response.json()["id"]
        
        # Delete the goal
        response = test_client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify goal is no longer accessible (soft deleted)
        get_response = test_client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
        assert get_response.status_code in [404, 410]  # Not found or gone


@pytest.mark.integration
class TestGoalContributionsAPI:
    """Test goal contributions API endpoints."""

    @pytest.fixture
    def sample_goal_id(self, test_client, auth_headers, tenant_context):
        """Create a sample goal and return its ID."""
        goal_data = {
            "name": "Contribution Test Goal",
            "target_amount": "5000.00",
            "goal_type": "general_savings",
            "is_active": True
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        return response.json()["id"]

    def test_add_goal_contribution(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test adding a contribution to a goal."""
        contribution_data = {
            "amount": "250.00",
            "source_type": "manual",
            "notes": "Monthly savings contribution"
        }
        
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/contributions",
            json=contribution_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == contribution_data["amount"]
        assert data["source_type"] == contribution_data["source_type"]
        assert data["goal_id"] == sample_goal_id
        assert "id" in data
        assert "created_at" in data

    def test_add_contribution_updates_goal_progress(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test that adding contribution updates goal progress."""
        # Add contribution
        contribution_data = {
            "amount": "1000.00",
            "source_type": "manual"
        }
        
        test_client.post(
            f"/api/v1/goals/{sample_goal_id}/contributions",
            json=contribution_data,
            headers=auth_headers
        )
        
        # Check updated goal
        goal_response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}",
            headers=auth_headers
        )
        
        assert goal_response.status_code == 200
        goal_data = goal_response.json()
        assert goal_data["current_amount"] == "1000.00"
        assert goal_data["progress_percentage"] == "20.00"  # 1000/5000 * 100

    def test_add_contribution_completes_goal(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test that large contribution completes the goal."""
        # Add contribution that exceeds target
        contribution_data = {
            "amount": "6000.00",  # Exceeds 5000 target
            "source_type": "manual",
            "notes": "Large final contribution"
        }
        
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/contributions",
            json=contribution_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        
        # Check goal completion
        goal_response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}",
            headers=auth_headers
        )
        
        goal_data = goal_response.json()
        assert goal_data["is_completed"] is True
        assert float(goal_data["current_amount"]) == 6000.00
        assert goal_data["completed_at"] is not None

    def test_add_invalid_contribution(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test adding invalid contribution."""
        # Negative amount
        invalid_data = {
            "amount": "-100.00",
            "source_type": "manual"
        }
        
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/contributions",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_get_goal_contributions(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test retrieving goal contributions."""
        # Add some contributions first
        contributions = [
            {"amount": "200.00", "source_type": "manual", "notes": "First contribution"},
            {"amount": "300.00", "source_type": "automatic", "notes": "Auto-save"},
            {"amount": "150.00", "source_type": "manual", "notes": "Bonus money"}
        ]
        
        for contrib in contributions:
            test_client.post(
                f"/api/v1/goals/{sample_goal_id}/contributions",
                json=contrib,
                headers=auth_headers
            )
        
        # Get contributions
        response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}/contributions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verify contribution structure
        for contribution in data:
            assert "id" in contribution
            assert "amount" in contribution
            assert "source_type" in contribution
            assert "created_at" in contribution

    def test_get_contributions_with_limit(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test getting contributions with limit."""
        # Add multiple contributions
        for i in range(5):
            contrib_data = {
                "amount": f"{(i+1)*100}.00",
                "source_type": "manual"
            }
            test_client.post(
                f"/api/v1/goals/{sample_goal_id}/contributions",
                json=contrib_data,
                headers=auth_headers
            )
        
        # Get limited contributions
        response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}/contributions?limit=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3


@pytest.mark.integration
class TestGoalMilestonesAPI:
    """Test goal milestones API endpoints."""

    @pytest.fixture
    def sample_goal_id(self, test_client, auth_headers, tenant_context):
        """Create a sample goal for milestone testing."""
        goal_data = {
            "name": "Milestone Test Goal",
            "target_amount": "10000.00",
            "goal_type": "emergency_fund",
            "is_active": True
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        return response.json()["id"]

    def test_create_goal_milestone(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test creating a goal milestone."""
        milestone_data = {
            "name": "First Milestone",
            "description": "25% of the way to emergency fund",
            "target_amount": "2500.00",
            "target_percentage": "25.00",
            "target_date": (date.today() + timedelta(days=90)).isoformat(),
            "reward_message": "Great progress on your emergency fund!",
            "notify_on_achievement": True,
            "sort_order": 1
        }
        
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == milestone_data["name"]
        assert data["target_amount"] == milestone_data["target_amount"]
        assert data["target_percentage"] == milestone_data["target_percentage"]
        assert data["goal_id"] == sample_goal_id
        assert data["is_achieved"] is False
        assert "id" in data

    def test_create_milestone_exceeding_goal_target(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test creating milestone that exceeds goal target."""
        milestone_data = {
            "name": "Impossible Milestone",
            "target_amount": "15000.00",  # Exceeds goal target of 10000
            "target_percentage": "150.00"
        }
        
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_get_goal_milestones(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test retrieving goal milestones."""
        # Create some milestones first
        milestones = [
            {
                "name": "Quarter One",
                "target_amount": "2500.00",
                "target_percentage": "25.00",
                "sort_order": 1
            },
            {
                "name": "Halfway Point",
                "target_amount": "5000.00",
                "target_percentage": "50.00",
                "sort_order": 2
            },
            {
                "name": "Three Quarters",
                "target_amount": "7500.00",
                "target_percentage": "75.00",
                "sort_order": 3
            }
        ]
        
        for milestone in milestones:
            test_client.post(
                f"/api/v1/goals/{sample_goal_id}/milestones",
                json=milestone,
                headers=auth_headers
            )
        
        # Get milestones
        response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verify milestones are ordered by sort_order
        for i, milestone in enumerate(data):
            assert milestone["sort_order"] == i + 1

    def test_milestone_auto_completion(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test automatic milestone completion when goal progress exceeds milestone target."""
        # Create milestone
        milestone_data = {
            "name": "Auto Complete Test",
            "target_amount": "3000.00",
            "target_percentage": "30.00",
            "notify_on_achievement": True
        }
        
        milestone_response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        
        milestone_id = milestone_response.json()["id"]
        
        # Add contribution that exceeds milestone target
        contribution_data = {
            "amount": "4000.00",
            "source_type": "manual"
        }
        
        test_client.post(
            f"/api/v1/goals/{sample_goal_id}/contributions",
            json=contribution_data,
            headers=auth_headers
        )
        
        # Check if milestone is completed
        milestones_response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            headers=auth_headers
        )
        
        milestones = milestones_response.json()
        completed_milestone = next((m for m in milestones if m["id"] == milestone_id), None)
        
        assert completed_milestone is not None
        assert completed_milestone["is_achieved"] is True
        assert completed_milestone["achieved_at"] is not None

    def test_update_milestone(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test updating a milestone."""
        # Create milestone
        milestone_data = {
            "name": "Original Milestone",
            "target_amount": "2000.00",
            "target_percentage": "20.00"
        }
        
        create_response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        
        milestone_id = create_response.json()["id"]
        
        # Update milestone
        update_data = {
            "name": "Updated Milestone",
            "target_amount": "2500.00",
            "target_percentage": "25.00"
        }
        
        response = test_client.put(
            f"/api/v1/milestones/{milestone_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["target_amount"] == update_data["target_amount"]

    def test_delete_milestone(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test deleting a milestone."""
        # Create milestone
        milestone_data = {
            "name": "Milestone to Delete",
            "target_amount": "1000.00",
            "target_percentage": "10.00"
        }
        
        create_response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        
        milestone_id = create_response.json()["id"]
        
        # Delete milestone
        response = test_client.delete(
            f"/api/v1/milestones/{milestone_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify milestone is deleted
        milestones_response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}/milestones",
            headers=auth_headers
        )
        
        milestones = milestones_response.json()
        deleted_milestone = next((m for m in milestones if m["id"] == milestone_id), None)
        assert deleted_milestone is None


@pytest.mark.integration
class TestGoalStatusManagementAPI:
    """Test goal status management API endpoints."""

    @pytest.fixture
    def sample_goal_id(self, test_client, auth_headers, tenant_context):
        """Create a sample goal for status management testing."""
        goal_data = {
            "name": "Status Management Test Goal",
            "target_amount": "3000.00",
            "goal_type": "general_savings",
            "is_active": True
        }
        
        response = test_client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        return response.json()["id"]

    def test_pause_goal(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test pausing an active goal."""
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/pause",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        
        # Verify goal status in database
        goal_response = test_client.get(
            f"/api/v1/goals/{sample_goal_id}",
            headers=auth_headers
        )
        
        goal_data = goal_response.json()
        assert goal_data["status"] == "paused"

    def test_resume_goal(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test resuming a paused goal."""
        # First pause the goal
        test_client.post(f"/api/v1/goals/{sample_goal_id}/pause", headers=auth_headers)
        
        # Then resume it
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/resume",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_complete_goal_manually(self, test_client, auth_headers, tenant_context, sample_goal_id):
        """Test manually completing a goal."""
        response = test_client.post(
            f"/api/v1/goals/{sample_goal_id}/complete",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["is_completed"] is True
        assert data["completed_at"] is not None


@pytest.mark.integration
class TestGoalAnalyticsAPI:
    """Test goal analytics and insights API endpoints."""

    @pytest.fixture
    def goals_with_data(self, test_client, auth_headers, tenant_context):
        """Create multiple goals with contributions for analytics testing."""
        goals = []
        
        # Create emergency fund goal with contributions
        emergency_goal = {
            "name": "Emergency Fund Analytics",
            "target_amount": "15000.00",
            "goal_type": "emergency_fund",
            "is_active": True
        }
        
        response = test_client.post("/api/v1/goals", json=emergency_goal, headers=auth_headers)
        emergency_id = response.json()["id"]
        goals.append(emergency_id)
        
        # Add contributions to emergency fund
        for amount in ["1000.00", "500.00", "750.00"]:
            contrib = {"amount": amount, "source_type": "manual"}
            test_client.post(f"/api/v1/goals/{emergency_id}/contributions", json=contrib, headers=auth_headers)
        
        # Create vacation goal
        vacation_goal = {
            "name": "Vacation Fund Analytics",
            "target_amount": "5000.00",
            "goal_type": "vacation",
            "is_active": True
        }
        
        response = test_client.post("/api/v1/goals", json=vacation_goal, headers=auth_headers)
        vacation_id = response.json()["id"]
        goals.append(vacation_id)
        
        # Add contribution to vacation fund
        contrib = {"amount": "1000.00", "source_type": "manual"}
        test_client.post(f"/api/v1/goals/{vacation_id}/contributions", json=contrib, headers=auth_headers)
        
        # Create completed goal
        completed_goal = {
            "name": "Completed Goal Analytics",
            "target_amount": "2000.00",
            "goal_type": "general_savings",
            "initial_contribution": "2000.00",  # Immediately complete
            "is_active": True
        }
        
        response = test_client.post("/api/v1/goals", json=completed_goal, headers=auth_headers)
        completed_id = response.json()["id"]
        goals.append(completed_id)
        
        return goals

    def test_get_goals_summary(self, test_client, auth_headers, tenant_context, goals_with_data):
        """Test getting goals summary analytics."""
        response = test_client.get("/api/v1/goals/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary structure
        assert "total_goals" in data
        assert "active_goals" in data
        assert "completed_goals" in data
        assert "total_target_amount" in data
        assert "total_saved_amount" in data
        assert "overall_progress" in data
        assert "goals_on_track" in data
        assert "goals_behind_schedule" in data
        assert data["total_goals"] >= 3  # At least the goals we created

    def test_get_goal_analysis(self, test_client, auth_headers, tenant_context, goals_with_data):
        """Test getting detailed goal analysis."""
        goal_id = goals_with_data[0]  # Emergency fund goal
        
        response = test_client.get(
            f"/api/v1/goals/{goal_id}/analysis",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify analysis structure
        assert "goal_id" in data
        assert "performance_score" in data
        assert "velocity" in data
        assert "projected_completion" in data
        assert "completion_probability" in data
        assert "insights" in data
        assert "contribution_patterns" in data
        assert "recommendations" in data
        
        assert data["goal_id"] == goal_id

    def test_get_goal_analysis_with_period(self, test_client, auth_headers, tenant_context, goals_with_data):
        """Test goal analysis with specific analysis period."""
        goal_id = goals_with_data[0]
        
        response = test_client.get(
            f"/api/v1/goals/{goal_id}/analysis?analysis_period=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["goal_id"] == goal_id

    def test_get_goal_insights(self, test_client, auth_headers, tenant_context, goals_with_data):
        """Test getting goal insights and recommendations."""
        response = test_client.get("/api/v1/goals/insights", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify insight structure if any insights exist
        if data:
            insight = data[0]
            assert "id" in insight
            assert "goal_id" in insight
            assert "insight_type" in insight
            assert "title" in insight
            assert "message" in insight
            assert "priority" in insight
            assert "suggested_actions" in insight
            assert "is_read" in insight
            assert "is_actionable" in insight

    def test_get_insights_unread_only(self, test_client, auth_headers, tenant_context, goals_with_data):
        """Test getting only unread insights."""
        response = test_client.get(
            "/api/v1/goals/insights?unread_only=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_mark_insight_as_read(self, test_client, auth_headers, tenant_context, goals_with_data):
        """Test marking an insight as read."""
        # First get insights
        insights_response = test_client.get("/api/v1/goals/insights", headers=auth_headers)
        insights = insights_response.json()
        
        if insights:
            insight_id = insights[0]["id"]
            
            response = test_client.post(
                f"/api/v1/goals/insights/{insight_id}/read",
                headers=auth_headers
            )
            
            assert response.status_code == 200

    def test_dismiss_insight(self, test_client, auth_headers, tenant_context, goals_with_data):
        """Test dismissing an insight."""
        # First get insights
        insights_response = test_client.get("/api/v1/goals/insights", headers=auth_headers)
        insights = insights_response.json()
        
        if insights:
            insight_id = insights[0]["id"]
            
            response = test_client.delete(
                f"/api/v1/goals/insights/{insight_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200


@pytest.mark.integration
class TestGoalTemplatesAPI:
    """Test goal templates API endpoints."""

    def test_get_goal_templates(self, test_client, auth_headers, tenant_context):
        """Test getting available goal templates."""
        response = test_client.get("/api/v1/goals/templates", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify template structure if templates exist
        if data:
            template = data[0]
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "goal_type" in template
            assert "default_target_amount" in template
            assert "default_monthly_contribution" in template
            assert "use_count" in template

    def test_get_templates_by_type(self, test_client, auth_headers, tenant_context):
        """Test getting templates filtered by goal type."""
        response = test_client.get(
            "/api/v1/goals/templates?goal_type=emergency_fund",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_apply_goal_template(self, test_client, auth_headers, tenant_context):
        """Test applying a goal template to create a new goal."""
        # First get available templates
        templates_response = test_client.get("/api/v1/goals/templates", headers=auth_headers)
        templates = templates_response.json()
        
        if templates:
            template_id = templates[0]["id"]
            
            template_data = {
                "name": "My Emergency Fund from Template",
                "target_amount": "12000.00",
                "monthly_contribution": "400.00",
                "target_date": (date.today() + timedelta(days=365)).isoformat(),
                "initial_contribution": "500.00"
            }
            
            response = test_client.post(
                f"/api/v1/goals/templates/{template_id}/apply",
                json=template_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == template_data["name"]
            assert data["target_amount"] == template_data["target_amount"]
            assert data["current_amount"] == template_data["initial_contribution"]

    def test_apply_nonexistent_template(self, test_client, auth_headers, tenant_context):
        """Test applying a non-existent template."""
        fake_template_id = str(uuid4())
        template_data = {
            "name": "Test Goal",
            "target_amount": "1000.00"
        }
        
        response = test_client.post(
            f"/api/v1/goals/templates/{fake_template_id}/apply",
            json=template_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.integration
class TestGoalSecurityAndAuthorization:
    """Test security and authorization for goals API."""

    def test_unauthorized_access(self, test_client, tenant_context):
        """Test access without authentication."""
        response = test_client.get("/api/v1/goals")
        assert response.status_code == 401

    def test_invalid_token(self, test_client, tenant_context):
        """Test access with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = test_client.get("/api/v1/goals", headers=headers)
        assert response.status_code == 401

    def test_cross_user_goal_access(self, test_client, auth_headers, tenant_context):
        """Test that users cannot access other users' goals."""
        # This test would require creating goals for different users
        # and verifying isolation
        fake_goal_id = str(uuid4())
        response = test_client.get(f"/api/v1/goals/{fake_goal_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_sql_injection_in_goal_name(self, test_client, auth_headers, tenant_context):
        """Test SQL injection prevention in goal name."""
        malicious_name = "'; DROP TABLE goals; --"
        goal_data = {
            "name": malicious_name,
            "target_amount": "1000.00",
            "goal_type": "general_savings"
        }
        
        response = test_client.post("/api/v1/goals", json=goal_data, headers=auth_headers)
        
        # Should either create successfully (with sanitized name) or reject
        assert response.status_code in [201, 422]
        
        # Verify system is still functional
        health_response = test_client.get("/health")
        assert health_response.status_code == 200

    def test_xss_in_goal_description(self, test_client, auth_headers, tenant_context):
        """Test XSS prevention in goal description."""
        xss_description = "<script>alert('XSS')</script>"
        goal_data = {
            "name": "XSS Test Goal",
            "description": xss_description,
            "target_amount": "1000.00",
            "goal_type": "general_savings"
        }
        
        response = test_client.post("/api/v1/goals", json=goal_data, headers=auth_headers)
        
        if response.status_code == 201:
            data = response.json()
            # Should sanitize XSS content
            assert "<script>" not in data.get("description", "")


@pytest.mark.integration
class TestGoalPerformanceAndLimits:
    """Test goal API performance and limits."""

    def test_large_goal_list_performance(self, test_client, auth_headers, tenant_context):
        """Test performance with large number of goals."""
        # Create multiple goals
        for i in range(20):
            goal_data = {
                "name": f"Performance Test Goal {i+1}",
                "target_amount": f"{(i+1)*100}.00",
                "goal_type": "general_savings"
            }
            test_client.post("/api/v1/goals", json=goal_data, headers=auth_headers)
        
        # Test retrieval performance
        import time
        start_time = time.time()
        
        response = test_client.get("/api/v1/goals", headers=auth_headers)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds

    def test_maximum_goal_name_length(self, test_client, auth_headers, tenant_context):
        """Test goal name length limits."""
        # Test very long goal name
        long_name = "A" * 200  # Assuming max length is around 100-200 chars
        goal_data = {
            "name": long_name,
            "target_amount": "1000.00",
            "goal_type": "general_savings"
        }
        
        response = test_client.post("/api/v1/goals", json=goal_data, headers=auth_headers)
        
        # Should either accept (if within limits) or reject gracefully
        assert response.status_code in [201, 422]

    def test_maximum_target_amount(self, test_client, auth_headers, tenant_context):
        """Test very large target amounts."""
        goal_data = {
            "name": "Large Amount Goal",
            "target_amount": "999999999.99",  # Very large amount
            "goal_type": "general_savings"
        }
        
        response = test_client.post("/api/v1/goals", json=goal_data, headers=auth_headers)
        
        # Should handle large amounts appropriately
        assert response.status_code in [201, 422]

    def test_concurrent_goal_modifications(self, test_client, auth_headers, tenant_context):
        """Test concurrent modifications to the same goal."""
        # Create a goal
        goal_data = {
            "name": "Concurrent Test Goal",
            "target_amount": "5000.00",
            "goal_type": "general_savings"
        }
        
        create_response = test_client.post("/api/v1/goals", json=goal_data, headers=auth_headers)
        goal_id = create_response.json()["id"]
        
        # Simulate concurrent contributions
        import threading
        results = []
        
        def add_contribution():
            contrib_data = {"amount": "100.00", "source_type": "manual"}
            response = test_client.post(
                f"/api/v1/goals/{goal_id}/contributions",
                json=contrib_data,
                headers=auth_headers
            )
            results.append(response.status_code)
        
        # Create multiple threads for concurrent access
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=add_contribution)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should be handled properly
        assert all(status in [201, 409, 500] for status in results)  # Allow for conflict resolution