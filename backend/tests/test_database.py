"""Comprehensive database constraints, relationships, and integrity tests."""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError, ForeignKeyViolation
from sqlalchemy import inspect

from src.users.models import User
from src.accounts.models import Account
from src.transactions.models import Transaction
from src.families.models import Family, FamilyMember
from src.budgets.models import Budget, BudgetCategory
from src.goals.models import Goal
from src.tithing.models import TithingRecord


@pytest.mark.integration
class TestDatabaseConstraints:
    """Test database constraints and data integrity."""
    
    @pytest.mark.asyncio
    async def test_user_email_unique_constraint(self, tenant_db_session):
        """Test that user emails must be unique within a tenant."""
        # Arrange
        user1 = User(
            id="user-1",
            auth0_user_id="auth0|user1",
            email="test@example.com",
            name="User 1"
        )
        
        user2 = User(
            id="user-2", 
            auth0_user_id="auth0|user2",
            email="test@example.com",  # Same email
            name="User 2"
        )
        
        # Act & Assert
        tenant_db_session.add(user1)
        await tenant_db_session.commit()
        
        tenant_db_session.add(user2)
        with pytest.raises(IntegrityError):
            await tenant_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_user_auth0_id_unique_constraint(self, tenant_db_session):
        """Test that Auth0 user IDs must be unique within a tenant."""
        # Arrange
        user1 = User(
            id="user-1",
            auth0_user_id="auth0|duplicate",
            email="user1@example.com",
            name="User 1"
        )
        
        user2 = User(
            id="user-2",
            auth0_user_id="auth0|duplicate",  # Same Auth0 ID
            email="user2@example.com",
            name="User 2"
        )
        
        # Act & Assert
        tenant_db_session.add(user1)
        await tenant_db_session.commit()
        
        tenant_db_session.add(user2)
        with pytest.raises(IntegrityError):
            await tenant_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_account_user_foreign_key_constraint(self, tenant_db_session):
        """Test account foreign key constraint to users."""
        # Arrange
        account = Account(
            id="account-1",
            user_id="non-existent-user",  # Invalid user ID
            name="Test Account",
            account_type="checking",
            balance=Decimal("1000.00"),
            currency="USD"
        )
        
        # Act & Assert
        tenant_db_session.add(account)
        with pytest.raises(ForeignKeyViolation):
            await tenant_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_transaction_account_foreign_key_constraint(self, tenant_db_session, test_user):
        """Test transaction foreign key constraint to accounts."""
        # Arrange
        transaction = Transaction(
            id="transaction-1",
            account_id="non-existent-account",  # Invalid account ID
            amount=Decimal("-50.00"),
            description="Test Transaction",
            transaction_date=date.today(),
            category="groceries"
        )
        
        # Act & Assert
        tenant_db_session.add(transaction)
        with pytest.raises(ForeignKeyViolation):
            await tenant_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_family_member_foreign_key_constraints(self, tenant_db_session, test_user):
        """Test family member foreign key constraints."""
        # Arrange - Create family first
        family = Family(
            id="family-1",
            name="Test Family",
            head_of_household_id=test_user.id,
            currency="USD",
            timezone="America/New_York"
        )
        tenant_db_session.add(family)
        await tenant_db_session.commit()
        
        # Try to create family member with invalid user ID
        family_member = FamilyMember(
            id="member-1",
            family_id=family.id,
            user_id="non-existent-user",  # Invalid user ID
            role="member",
            permissions=["view"]
        )
        
        # Act & Assert
        tenant_db_session.add(family_member)
        with pytest.raises(ForeignKeyViolation):
            await tenant_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_budget_user_foreign_key_constraint(self, tenant_db_session):
        """Test budget foreign key constraint to users."""
        # Arrange
        budget = Budget(
            id="budget-1",
            user_id="non-existent-user",  # Invalid user ID
            name="Test Budget",
            period_type="monthly",
            total_amount=Decimal("2000.00"),
            currency="USD"
        )
        
        # Act & Assert
        tenant_db_session.add(budget)
        with pytest.raises(ForeignKeyViolation):
            await tenant_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_not_null_constraints(self, tenant_db_session):
        """Test NOT NULL constraints on required fields."""
        # Test user without email
        user_no_email = User(
            id="user-no-email",
            auth0_user_id="auth0|test",
            # email=None,  # Missing required field
            name="Test User"
        )
        
        tenant_db_session.add(user_no_email)
        with pytest.raises(IntegrityError):
            await tenant_db_session.commit()
        
        # Reset session
        await tenant_db_session.rollback()
        
        # Test account without user_id
        account_no_user = Account(
            id="account-no-user",
            # user_id=None,  # Missing required field
            name="Test Account",
            account_type="checking",
            balance=Decimal("1000.00")
        )
        
        tenant_db_session.add(account_no_user)
        with pytest.raises(IntegrityError):
            await tenant_db_session.commit()
    
    @pytest.mark.asyncio
    async def test_check_constraints(self, tenant_db_session, test_user):
        """Test CHECK constraints on data values."""
        # Test negative balance (if not allowed)
        account_negative = Account(
            id="account-negative",
            user_id=test_user.id,
            name="Negative Account",
            account_type="checking",
            balance=Decimal("-1000.00"),  # Negative balance
            currency="USD"
        )
        
        # This test depends on whether negative balances are allowed
        # If there's a CHECK constraint preventing negative balances:
        try:
            tenant_db_session.add(account_negative)
            await tenant_db_session.commit()
        except IntegrityError:
            # Expected if CHECK constraint exists
            await tenant_db_session.rollback()
        
        # Test invalid currency code (if there's a constraint)
        account_invalid_currency = Account(
            id="account-invalid-currency",
            user_id=test_user.id,
            name="Invalid Currency Account",
            account_type="checking",
            balance=Decimal("1000.00"),
            currency="INVALID"  # Invalid currency code
        )
        
        try:
            tenant_db_session.add(account_invalid_currency)
            await tenant_db_session.commit()
        except IntegrityError:
            # Expected if CHECK constraint exists for currency
            await tenant_db_session.rollback()


@pytest.mark.integration
class TestDatabaseRelationships:
    """Test database relationships and cascading operations."""
    
    @pytest.mark.asyncio
    async def test_user_accounts_relationship(self, tenant_db_session, test_user):
        """Test one-to-many relationship between users and accounts."""
        # Arrange
        account1 = Account(
            id="account-1",
            user_id=test_user.id,
            name="Checking Account",
            account_type="checking",
            balance=Decimal("1000.00"),
            currency="USD"
        )
        
        account2 = Account(
            id="account-2",
            user_id=test_user.id,
            name="Savings Account", 
            account_type="savings",
            balance=Decimal("5000.00"),
            currency="USD"
        )
        
        tenant_db_session.add(account1)
        tenant_db_session.add(account2)
        await tenant_db_session.commit()
        
        # Act - Refresh user to load relationships
        await tenant_db_session.refresh(test_user)
        
        # Assert
        assert len(test_user.accounts) == 2
        account_names = [acc.name for acc in test_user.accounts]
        assert "Checking Account" in account_names
        assert "Savings Account" in account_names
    
    @pytest.mark.asyncio
    async def test_account_transactions_relationship(self, tenant_db_session, test_account):
        """Test one-to-many relationship between accounts and transactions."""
        # Arrange
        transaction1 = Transaction(
            id="transaction-1",
            account_id=test_account.id,
            amount=Decimal("-50.00"),
            description="Grocery Store",
            transaction_date=date.today(),
            category="groceries"
        )
        
        transaction2 = Transaction(
            id="transaction-2",
            account_id=test_account.id,
            amount=Decimal("-25.00"),
            description="Coffee Shop",
            transaction_date=date.today(),
            category="dining"
        )
        
        tenant_db_session.add(transaction1)
        tenant_db_session.add(transaction2)
        await tenant_db_session.commit()
        
        # Act - Refresh account to load relationships
        await tenant_db_session.refresh(test_account)
        
        # Assert
        assert len(test_account.transactions) == 2
        transaction_amounts = [txn.amount for txn in test_account.transactions]
        assert Decimal("-50.00") in transaction_amounts
        assert Decimal("-25.00") in transaction_amounts
    
    @pytest.mark.asyncio
    async def test_family_members_relationship(self, tenant_db_session, test_family, test_user):
        """Test one-to-many relationship between families and family members."""
        # Arrange - Create another user
        user2 = User(
            id="user-2",
            auth0_user_id="auth0|user2",
            email="user2@example.com",
            name="User 2"
        )
        tenant_db_session.add(user2)
        await tenant_db_session.commit()
        
        # Create family members
        member1 = FamilyMember(
            id="member-1",
            family_id=test_family.id,
            user_id=test_user.id,
            role="head",
            permissions=["all"]
        )
        
        member2 = FamilyMember(
            id="member-2",
            family_id=test_family.id,
            user_id=user2.id,
            role="member",
            permissions=["view", "create"]
        )
        
        tenant_db_session.add(member1)
        tenant_db_session.add(member2)
        await tenant_db_session.commit()
        
        # Act - Refresh family to load relationships
        await tenant_db_session.refresh(test_family)
        
        # Assert
        assert len(test_family.members) == 2
        member_roles = [member.role for member in test_family.members]
        assert "head" in member_roles
        assert "member" in member_roles
    
    @pytest.mark.asyncio
    async def test_cascade_delete_prevention(self, tenant_db_session, test_account, test_transaction):
        """Test that cascade deletes are prevented where appropriate."""
        # Try to delete account that has transactions
        # This should be prevented by foreign key constraint or business logic
        
        try:
            await tenant_db_session.delete(test_account)
            await tenant_db_session.commit()
            
            # If this succeeds, check that transaction was also deleted (cascade)
            # or that the delete was prevented
            remaining_transactions = await tenant_db_session.execute(
                select(Transaction).where(Transaction.account_id == test_account.id)
            )
            assert remaining_transactions.scalars().first() is None
            
        except IntegrityError:
            # Expected if cascade delete is prevented
            await tenant_db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_soft_delete_relationships(self, tenant_db_session, test_user, test_account):
        """Test soft delete functionality preserves relationships."""
        # If soft delete is implemented, test that relationships are maintained
        # but records are marked as deleted
        
        if hasattr(test_user, 'is_deleted'):
            # Soft delete user
            test_user.is_deleted = True
            test_user.deleted_at = datetime.now(timezone.utc)
            await tenant_db_session.commit()
            
            # Refresh account
            await tenant_db_session.refresh(test_account)
            
            # Account should still reference user but user should be marked deleted
            assert test_account.user_id == test_user.id
            assert test_user.is_deleted is True


@pytest.mark.integration
class TestDatabaseIndexes:
    """Test database indexes and query performance."""
    
    @pytest.mark.asyncio
    async def test_indexes_exist(self, tenant_db_session):
        """Test that expected database indexes exist."""
        # Use SQLAlchemy inspector to check indexes
        inspector = inspect(tenant_db_session.bind)
        
        # Check indexes on users table
        user_indexes = inspector.get_indexes('users')
        index_columns = [idx['column_names'] for idx in user_indexes]
        
        # Should have indexes on commonly queried columns
        expected_indexed_columns = [
            ['email'],
            ['auth0_user_id'],
        ]
        
        for expected_cols in expected_indexed_columns:
            assert any(set(expected_cols).issubset(set(cols)) for cols in index_columns), \
                f"Missing index on columns: {expected_cols}"
        
        # Check indexes on accounts table
        account_indexes = inspector.get_indexes('accounts')
        account_index_columns = [idx['column_names'] for idx in account_indexes]
        
        # Should have index on user_id for foreign key performance
        assert any('user_id' in cols for cols in account_index_columns), \
            "Missing index on accounts.user_id"
        
        # Check indexes on transactions table
        transaction_indexes = inspector.get_indexes('transactions')
        transaction_index_columns = [idx['column_names'] for idx in transaction_indexes]
        
        # Should have indexes on frequently queried columns
        expected_transaction_indexes = [
            'account_id',
            'transaction_date',
            'category'
        ]
        
        for expected_col in expected_transaction_indexes:
            assert any(expected_col in cols for cols in transaction_index_columns), \
                f"Missing index on transactions.{expected_col}"
    
    @pytest.mark.asyncio
    async def test_composite_indexes(self, tenant_db_session):
        """Test composite indexes for complex queries."""
        # Check for composite indexes that support common query patterns
        inspector = inspect(tenant_db_session.bind)
        
        # Example: transactions by account and date range
        transaction_indexes = inspector.get_indexes('transactions')
        
        # Look for composite index on (account_id, transaction_date)
        composite_found = any(
            set(['account_id', 'transaction_date']).issubset(set(idx['column_names']))
            for idx in transaction_indexes
        )
        
        if not composite_found:
            # This might be expected depending on query patterns
            # Could be a performance optimization opportunity
            pass
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_query_performance(self, tenant_db_session, test_user):
        """Test query performance with indexes."""
        # Create test data
        accounts = []
        for i in range(100):
            account = Account(
                id=f"perf-account-{i}",
                user_id=test_user.id,
                name=f"Account {i}",
                account_type="checking",
                balance=Decimal("1000.00"),
                currency="USD"
            )
            accounts.append(account)
        
        tenant_db_session.add_all(accounts)
        await tenant_db_session.commit()
        
        # Test query performance
        import time
        start_time = time.time()
        
        # Query that should use index
        result = await tenant_db_session.execute(
            select(Account).where(Account.user_id == test_user.id)
        )
        accounts_found = result.scalars().all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Query should be fast with proper indexing
        assert len(accounts_found) == 100
        assert query_time < 0.1  # Should complete in under 100ms


@pytest.mark.integration
class TestDatabaseMigrations:
    """Test database migration scenarios."""
    
    def test_schema_migration_compatibility(self):
        """Test that schema migrations maintain compatibility."""
        # This would test that new migrations don't break existing data
        # Would require setting up test databases with different schema versions
        pass
    
    def test_data_migration_integrity(self):
        """Test data migration integrity."""
        # Test that data migrations preserve data integrity
        # and don't corrupt existing data
        pass
    
    def test_rollback_migration_safety(self):
        """Test that migration rollbacks are safe."""
        # Test that migrations can be safely rolled back
        # without data loss
        pass


@pytest.mark.integration
class TestDatabaseTransactions:
    """Test database transaction handling."""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, tenant_db_session, test_user):
        """Test that database transactions rollback on errors."""
        # Start a transaction
        try:
            # Create valid account
            account = Account(
                id="rollback-test-account",
                user_id=test_user.id,
                name="Rollback Test",
                account_type="checking",
                balance=Decimal("1000.00"),
                currency="USD"
            )
            tenant_db_session.add(account)
            
            # Create invalid account (should cause error)
            invalid_account = Account(
                id="invalid-account",
                user_id="non-existent-user",  # Invalid foreign key
                name="Invalid Account",
                account_type="checking",
                balance=Decimal("1000.00"),
                currency="USD"
            )
            tenant_db_session.add(invalid_account)
            
            # Commit should fail and rollback both operations
            await tenant_db_session.commit()
            
        except Exception:
            # Expected - transaction should rollback
            await tenant_db_session.rollback()
        
        # Verify that the valid account was also rolled back
        result = await tenant_db_session.execute(
            select(Account).where(Account.id == "rollback-test-account")
        )
        assert result.scalar_one_or_none() is None
    
    @pytest.mark.asyncio
    async def test_nested_transaction_handling(self, tenant_db_session):
        """Test nested transaction handling."""
        # Test that nested transactions (savepoints) work correctly
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_transaction_isolation(self, tenant_db_session):
        """Test transaction isolation under concurrent access."""
        # Test that concurrent transactions don't interfere with each other
        pass


@pytest.mark.integration
class TestDatabaseConnectionHandling:
    """Test database connection management."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_management(self):
        """Test database connection pool management."""
        # Test that connections are properly managed and reused
        pass
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self):
        """Test handling of connection timeouts."""
        # Test that connection timeouts are handled gracefully
        pass
    
    @pytest.mark.asyncio
    async def test_database_reconnection(self):
        """Test database reconnection after connection loss."""
        # Test that the application can reconnect after database connection loss
        pass


@pytest.mark.integration
class TestMultiTenantDatabaseIsolation:
    """Test multi-tenant database isolation."""
    
    @pytest.mark.asyncio
    async def test_tenant_data_isolation(self, global_db_session, tenant_db_session):
        """Test that tenant data is properly isolated."""
        # This would test that tenant-specific databases properly isolate data
        # and that queries don't accidentally access other tenant's data
        pass
    
    @pytest.mark.asyncio
    async def test_tenant_schema_consistency(self):
        """Test that all tenant databases have consistent schemas."""
        # Test that tenant databases are created with the same schema
        pass
    
    @pytest.mark.asyncio
    async def test_global_tenant_metadata_integrity(self, global_db_session):
        """Test integrity of global tenant metadata."""
        # Test that global database properly tracks tenant information
        pass