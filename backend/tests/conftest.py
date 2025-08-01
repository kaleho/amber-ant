"""Pytest configuration and shared fixtures."""
import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from libsql_client import create_client
from alembic import command
from alembic.config import Config

# Import our application modules
from src.main import create_app
from src.config import settings
from src.database import get_global_database, get_tenant_database, GlobalDatabase, TenantDatabase
from src.tenant.context import TenantContext
from src.users.models import User
from src.accounts.models import Account
from src.transactions.models import Transaction
from src.families.models import Family, FamilyMember


# Test configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_GLOBAL_DB_URL = "sqlite+aiosqlite:///test_global.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    original_env = dict(os.environ)
    
    # Set test environment variables
    os.environ.update({
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "DATABASE_URL": TEST_DATABASE_URL,
        "GLOBAL_DATABASE_URL": TEST_GLOBAL_DB_URL,
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_API_AUDIENCE": "test-audience",
        "PLAID_CLIENT_ID": "test-plaid-id",
        "PLAID_SECRET": "test-plaid-secret",
        "STRIPE_PUBLISHABLE_KEY": "pk_test_123",
        "STRIPE_SECRET_KEY": "sk_test_123",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001",
    })
    
    # Reload settings module to pick up test values
    import importlib
    from src import config
    importlib.reload(config)
    
    yield config.settings
    
    # Cleanup: restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest_asyncio.fixture
async def global_db_engine():
    """Create test global database engine."""
    engine = create_async_engine(
        TEST_GLOBAL_DB_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def tenant_db_engine():
    """Create test tenant database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def global_db_session(global_db_engine):
    """Create test global database session."""
    # Create tables
    from src.tenant.models import Tenant
    from src.subscriptions.models import Subscription
    
    async with global_db_engine.begin() as conn:
        await conn.run_sync(Tenant.metadata.create_all)
    
    # Create session
    session_factory = async_sessionmaker(
        global_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def tenant_db_session(tenant_db_engine):
    """Create test tenant database session."""
    # Create tables
    from src.users.models import User
    from src.accounts.models import Account
    from src.transactions.models import Transaction
    from src.families.models import Family, FamilyMember
    from src.budgets.models import Budget, BudgetCategory
    from src.goals.models import Goal
    from src.tithing.models import TithingRecord
    
    async with tenant_db_engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)
    
    # Create session
    session_factory = async_sessionmaker(
        tenant_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_global_database(global_db_session):
    """Mock global database dependency."""
    mock_db = Mock(spec=GlobalDatabase)
    mock_db.session = global_db_session
    return mock_db


@pytest.fixture
def mock_tenant_database(tenant_db_session):
    """Mock tenant database dependency."""
    mock_db = Mock(spec=TenantDatabase)
    mock_db.session = tenant_db_session
    return mock_db


@pytest.fixture
def test_tenant_context():
    """Create test tenant context."""
    return TenantContext(
        tenant_id="test-tenant",
        tenant_slug="test-tenant",
        database_url=TEST_DATABASE_URL,
        user_id="test-user-123"
    )


@pytest.fixture
def app(test_settings, mock_global_database, mock_tenant_database, test_tenant_context):
    """Create FastAPI test application."""
    app = create_app()
    
    # Override dependencies
    app.dependency_overrides[get_global_database] = lambda: mock_global_database
    app.dependency_overrides[get_tenant_database] = lambda: mock_tenant_database
    
    # Set test tenant context
    with patch('src.tenant.context.get_tenant_context', return_value=test_tenant_context):
        yield app
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(app):
    """Create FastAPI test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(app):
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Create test authentication headers."""
    return {
        "Authorization": "Bearer test-jwt-token",
        "X-Tenant-ID": "test-tenant"
    }


@pytest.fixture
def admin_headers():
    """Create test admin authentication headers."""
    return {
        "Authorization": "Bearer test-admin-jwt-token",
        "X-Tenant-ID": "test-tenant"
    }


# Test data fixtures
@pytest.fixture
async def test_user(tenant_db_session):
    """Create test user."""
    user = User(
        id="test-user-123",
        auth0_user_id="auth0|test123",
        email="test@example.com",
        email_verified=True,
        name="Test User",
        given_name="Test",
        family_name="User",
        picture="https://example.com/avatar.jpg",
        locale="en",
        role="member"
    )
    tenant_db_session.add(user)
    await tenant_db_session.commit()
    await tenant_db_session.refresh(user)
    return user


@pytest.fixture
async def test_family(tenant_db_session, test_user):
    """Create test family."""
    family = Family(
        id="test-family-123",
        name="Test Family",
        head_of_household_id=test_user.id,
        currency="USD",
        timezone="America/New_York"
    )
    tenant_db_session.add(family)
    await tenant_db_session.commit()
    await tenant_db_session.refresh(family)
    
    # Add user as family member
    member = FamilyMember(
        id="test-member-123",
        family_id=family.id,
        user_id=test_user.id,
        role="head",
        permissions=["all"]
    )
    tenant_db_session.add(member)
    await tenant_db_session.commit()
    
    return family


@pytest.fixture
async def test_account(tenant_db_session, test_user):
    """Create test account."""
    account = Account(
        id="test-account-123",
        user_id=test_user.id,
        name="Test Checking Account",
        account_type="checking",
        balance=1000.00,
        currency="USD",
        is_active=True,
        plaid_account_id="plaid_test_123"
    )
    tenant_db_session.add(account)
    await tenant_db_session.commit()
    await tenant_db_session.refresh(account)
    return account


@pytest.fixture
async def test_transaction(tenant_db_session, test_account):
    """Create test transaction."""
    transaction = Transaction(
        id="test-transaction-123",
        account_id=test_account.id,
        amount=-50.00,
        description="Test Transaction",
        transaction_date="2024-01-15",
        category="groceries",
        subcategory="food",
        merchant_name="Test Store",
        transaction_type="purchase",
        is_pending=False,
        plaid_transaction_id="plaid_txn_123"
    )
    tenant_db_session.add(transaction)
    await tenant_db_session.commit()
    await tenant_db_session.refresh(transaction)
    return transaction


# Mock external services
@pytest.fixture
def mock_auth0():
    """Mock Auth0 service."""
    with patch('src.auth.service.Auth0Service') as mock:
        mock_instance = Mock()
        mock_instance.verify_token = AsyncMock(return_value={
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User"
        })
        mock_instance.get_user_info = AsyncMock(return_value={
            "sub": "auth0|test123",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg"
        })
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_plaid():
    """Mock Plaid service."""
    with patch('src.plaid.service.PlaidService') as mock:
        mock_instance = Mock()
        mock_instance.create_link_token = AsyncMock(return_value={
            "link_token": "test-link-token-123",
            "expiration": "2024-01-01T23:59:59Z"
        })
        mock_instance.exchange_public_token = AsyncMock(return_value={
            "access_token": "test-access-token",
            "item_id": "test-item-id"
        })
        mock_instance.get_accounts = AsyncMock(return_value=[
            {
                "account_id": "test-account-id",
                "name": "Test Checking",
                "official_name": "Test Bank Checking Account",
                "type": "depository",
                "subtype": "checking",
                "balance": {"current": 1000.00, "available": 950.00}
            }
        ])
        mock_instance.get_transactions = AsyncMock(return_value=[
            {
                "transaction_id": "test-txn-id",
                "account_id": "test-account-id",
                "amount": 50.00,
                "date": "2024-01-15",
                "name": "Test Transaction",
                "merchant_name": "Test Store"
            }
        ])
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_stripe():
    """Mock Stripe service."""
    with patch('src.subscriptions.service.StripeService') as mock:
        mock_instance = Mock()
        mock_instance.create_customer = AsyncMock(return_value={
            "id": "cus_test123",
            "email": "test@example.com"
        })
        mock_instance.create_subscription = AsyncMock(return_value={
            "id": "sub_test123",
            "status": "active",
            "current_period_start": 1640995200,
            "current_period_end": 1643673600
        })
        mock_instance.cancel_subscription = AsyncMock(return_value={
            "id": "sub_test123",
            "status": "canceled"
        })
        mock.return_value = mock_instance
        yield mock_instance


# Utility functions for tests
def assert_response_structure(response_data: dict, expected_fields: list):
    """Assert response contains expected fields."""
    for field in expected_fields:
        assert field in response_data, f"Expected field '{field}' not found in response"


def assert_datetime_field(value: str):
    """Assert field is valid ISO datetime string."""
    from datetime import datetime
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid datetime format: {value}")


def assert_uuid_field(value: str):
    """Assert field is valid UUID string."""
    import uuid
    try:
        uuid.UUID(value)
    except ValueError:
        pytest.fail(f"Invalid UUID format: {value}")


def assert_currency_field(value):
    """Assert field is valid currency amount."""
    assert isinstance(value, (int, float)), f"Currency field must be numeric, got {type(value)}"
    assert value >= 0 or abs(value) < 1000000, f"Currency amount seems invalid: {value}"


# Test data generators
class TestDataGenerator:
    """Generate test data for various entities."""
    
    @staticmethod
    def user_data(override: dict = None) -> dict:
        """Generate test user data."""
        data = {
            "auth0_user_id": "auth0|test123",
            "email": "test@example.com",
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "role": "member"
        }
        if override:
            data.update(override)
        return data
    
    @staticmethod
    def account_data(override: dict = None) -> dict:
        """Generate test account data."""
        data = {
            "name": "Test Account",
            "account_type": "checking",
            "balance": 1000.00,
            "currency": "USD",
            "is_active": True
        }
        if override:
            data.update(override)
        return data
    
    @staticmethod
    def transaction_data(override: dict = None) -> dict:
        """Generate test transaction data."""
        data = {
            "amount": -50.00,
            "description": "Test Transaction",
            "transaction_date": "2024-01-15",
            "category": "groceries",
            "subcategory": "food",
            "merchant_name": "Test Store",
            "transaction_type": "purchase"
        }
        if override:
            data.update(override)
        return data


@pytest.fixture
def test_data_generator():
    """Provide test data generator."""
    return TestDataGenerator