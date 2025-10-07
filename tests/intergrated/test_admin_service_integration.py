import pytest
import tempfile
import os


from src.services.service_layer.admins import AdminService
from src.services.service_layer.data import CreateAdminData
from src.services.service_layer.factory import ServiceFactory
from src.services.uow.uowsqlite import SqliteUnitOfWork
from src.adapters.repositorysqlite import CreateDB
from utils.db.connect import Connection
import sqlite3

from src.domain.model import Admin

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name

        yield temp_db_path

        # Cleanup
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


class TestAdminServiceIntegration:
    """Integration tests for AdminService with real database"""

    @pytest.fixture
    def db_connection(self, temp_db):
        """Create a real database connection"""
        connection = Connection.create_connection(url=temp_db, engine=sqlite3)

        # Initialize database schema
        create_db = CreateDB(connection)
        create_db.init_data()
        create_db.create_indexes()

        return connection

    @pytest.fixture
    def uow(self, db_connection):
        """Create real Unit of Work"""
        return SqliteUnitOfWork(db_connection)

    @pytest.fixture
    def service_factory(self, uow):
        """Create service factory with real UoW"""
        return ServiceFactory(uow)

    @pytest.fixture
    def admin_service(self, service_factory):
        """Create AdminService with real dependencies"""
        return service_factory.get_admin_service()

    @pytest.fixture
    def sample_admin_data(self):
        """Sample admin data for testing"""
        return CreateAdminData(
            name="integration_admin",
            password="securepassword123",
            email="integration@example.com",
            enabled=True
        )

    def test_create_admin_integration(self, admin_service, sample_admin_data):
        """Integration test: Create admin and verify persistence"""
        # Act
        created_admin = admin_service.execute('create', create_admin_data=sample_admin_data)

        # Assert
        assert isinstance(created_admin, Admin)
        assert created_admin.name == "integration_admin"
        assert created_admin.email == "integration@example.com"
        assert created_admin.enabled is True
        assert created_admin.admin_id > 0  # Should have real database ID

        # Verify we can retrieve the same admin
        retrieved_admin = admin_service.execute('get_by_name', name="integration_admin")
        assert retrieved_admin.admin_id == created_admin.admin_id
        assert retrieved_admin.name == created_admin.name
        assert retrieved_admin.email == created_admin.email

    def test_create_admin_duplicate_name(self, admin_service, sample_admin_data):
        """Integration test: Prevent duplicate admin names"""
        # Create first admin
        admin_service.execute('create', create_admin_data=sample_admin_data)

        # Try to create duplicate
        with pytest.raises(ValueError, match="Admin with name 'integration_admin' already exists"):
            admin_service.execute('create', create_admin_data=sample_admin_data)

    def test_update_admin_email_integration(self, admin_service, sample_admin_data):
        """Integration test: Update admin email"""
        # Create admin first
        admin_service.execute('create', create_admin_data=sample_admin_data)

        # Update email
        updated_admin = admin_service.execute(
            'update_email',
            name="integration_admin",
            new_email="updated@example.com"
        )

        # Verify update
        assert updated_admin.email == "updated@example.com"

        # Verify persistence
        retrieved_admin = admin_service.execute('get_by_name', name="integration_admin")
        assert retrieved_admin.email == "updated@example.com"

    def test_toggle_admin_status_integration(self, admin_service, sample_admin_data):
        """Integration test: Toggle admin status"""
        # Create admin first
        admin_service.execute('create', create_admin_data=sample_admin_data)

        # Verify initial state
        admin = admin_service.execute('get_by_name', name="integration_admin")
        assert admin.enabled is True

        # Toggle status
        toggled_admin = admin_service.execute('toggle_status', name="integration_admin")
        assert toggled_admin.enabled is False

        # Toggle back
        toggled_again_admin = admin_service.execute('toggle_status', name="integration_admin")
        assert toggled_again_admin.enabled is True

        # Verify persistence
        final_admin = admin_service.execute('get_by_name', name="integration_admin")
        assert final_admin.enabled is True

    def test_change_admin_password_integration(self, admin_service, sample_admin_data):
        """Integration test: Change admin password"""
        # Create admin first
        admin_service.execute('create', create_admin_data=sample_admin_data)

        # Change password
        updated_admin = admin_service.execute(
            'change_password',
            name="integration_admin",
            new_password="newsecurepassword456"
        )

        # Verify the admin can verify the new password
        assert updated_admin.verify_password("newsecurepassword456") is True
        assert updated_admin.verify_password("securepassword123") is False  # Old password should fail

    def test_list_admins_integration(self, admin_service, sample_admin_data):
        """Integration test: List all admins"""
        # Initially no admins
        admins = admin_service.list_all_admins()
        assert len(admins) == 0

        # Create first admin
        admin_service.execute('create', create_admin_data=sample_admin_data)

        # Create second admin
        second_admin_data = CreateAdminData(
            name="second_admin",
            password="password789",
            email="second@example.com",
            enabled=False
        )
        admin_service.execute('create', create_admin_data=second_admin_data)

        # Verify list all admins
        all_admins = admin_service.list_all_admins()
        assert len(all_admins) == 2
        admin_names = [admin.name for admin in all_admins]
        assert "integration_admin" in admin_names
        assert "second_admin" in admin_names

        # Verify list enabled admins
        enabled_admins = admin_service.list_enabled_admins()
        assert len(enabled_admins) == 1
        assert enabled_admins[0].name == "integration_admin"

        # Verify list disabled admins (via domain model)
        with admin_service.uow:
            aggregate = admin_service.uow.admins.get_list_of_admins()
            disabled_admins = aggregate.get_disabled_admins()
            assert len(disabled_admins) == 1
            assert disabled_admins[0].name == "second_admin"

    def test_admin_exists_integration(self, admin_service, sample_admin_data):
        """Integration test: Check admin existence"""
        # Initially doesn't exist
        assert admin_service.admin_exists("integration_admin") is False

        # Create admin
        admin_service.execute('create', create_admin_data=sample_admin_data)

        # Now should exist
        assert admin_service.admin_exists("integration_admin") is True
        assert admin_service.admin_exists("nonexistent_admin") is False

    def test_get_nonexistent_admin(self, admin_service):
        """Integration test: Get admin that doesn't exist"""
        with pytest.raises(ValueError, match="Admin 'nonexistent' not found"):
            admin_service.execute('get_by_name', name="nonexistent")

    def test_transaction_rollback_on_error(self, admin_service, sample_admin_data):
        """Integration test: Verify transaction rollback on error"""
        # Create first admin successfully
        admin_service.execute('create', create_admin_data=sample_admin_data)

        # Try to create duplicate (should fail and rollback)
        try:
            admin_service.execute('create', create_admin_data=sample_admin_data)
        except ValueError:
            pass  # Expected to fail

        # Verify first admin still exists and no partial state
        assert admin_service.admin_exists("integration_admin") is True

        # Count should still be 1 (not 2 from partial creation)
        admins = admin_service.list_all_admins()
        assert len(admins) == 1

    def test_password_hashing_integration(self, admin_service, sample_admin_data):
        """Integration test: Verify password hashing works correctly"""
        # Create admin
        created_admin = admin_service.execute('create', create_admin_data=sample_admin_data)

        # Verify password checking works
        assert created_admin.verify_password("securepassword123") is True
        assert created_admin.verify_password("wrongpassword") is False

        # The actual password hash should not be the plain text
        assert created_admin.password != "securepassword123"
        assert len(created_admin.password) > 20  # bcrypt hashes are long


class TestAdminServiceMultipleOperations:


    """Integration tests for multiple operations in sequence"""

    @pytest.fixture
    def admin_service(self, temp_db):
        """Create fresh AdminService for each test"""
        connection = Connection.create_connection(url=temp_db, engine=sqlite3)
        create_db = CreateDB(connection)
        create_db.init_data()

        uow = SqliteUnitOfWork(connection)
        return AdminService(uow)

    def test_complete_admin_lifecycle(self, admin_service):
        """Test complete admin lifecycle: create → update → toggle → verify"""
        # Create admin
        create_data = CreateAdminData(
            name="lifecycle_admin",
            password="initialpass",
            email="initial@example.com",
            enabled=True
        )
        admin = admin_service.execute('create', create_admin_data=create_data)
        assert admin.enabled is True
        assert admin.email == "initial@example.com"

        # Update email
        admin = admin_service.execute('update_email', name="lifecycle_admin", new_email="updated@example.com")
        assert admin.email == "updated@example.com"

        # Toggle status
        admin = admin_service.execute('toggle_status', name="lifecycle_admin")
        assert admin.enabled is False

        # Change password
        admin = admin_service.execute('change_password', name="lifecycle_admin", new_password="newpass123")
        assert admin.verify_password("newpass123") is True

        # Verify all changes persisted
        final_admin = admin_service.execute('get_by_name', name="lifecycle_admin")
        assert final_admin.email == "updated@example.com"
        assert final_admin.enabled is False
        assert final_admin.verify_password("newpass123") is True

    def test_multiple_admins_operations(self, admin_service):
        """Test operations with multiple admins"""
        # Create multiple admins
        admins_data = [
            CreateAdminData(name=f"admin_{i}", password=f"pass_{i}", email=f"admin{i}@example.com")
            for i in range(3)
        ]

        for admin_data in admins_data:
            admin_service.execute('create', create_admin_data=admin_data)

        # Verify all created
        all_admins = admin_service.list_all_admins()
        assert len(all_admins) == 3

        # Update each admin
        for i in range(3):
            admin_service.execute('update_email', name=f"admin_{i}", new_email=f"updated{i}@example.com")

        # Verify all updates
        for i in range(3):
            admin = admin_service.execute('get_by_name', name=f"admin_{i}")
            assert admin.email == f"updated{i}@example.com"


class TestAdminServiceEdgeCases:
    """Integration tests for edge cases and error conditions"""



    @pytest.fixture
    def admin_service(self, temp_db):
        """Create fresh AdminService for each test"""
        connection = Connection.create_connection(url=temp_db, engine=sqlite3)
        create_db = CreateDB(connection)
        create_db.init_data()

        uow = SqliteUnitOfWork(connection)
        return AdminService(uow)

    def test_create_admin_with_special_characters(self, admin_service):
        """Test creating admin with special characters in name"""
        special_name_data = CreateAdminData(
            name="admin-with-dash",
            password="password123",
            email="special@example.com"
        )

        admin = admin_service.execute('create', create_admin_data=special_name_data)
        assert admin.name == "admin-with-dash"

        # Should be able to retrieve it
        retrieved = admin_service.execute('get_by_name', name="admin-with-dash")
        assert retrieved.admin_id == admin.admin_id

    def test_create_admin_long_values(self, admin_service):
        """Test creating admin with long but valid values"""
        long_name = "a" * 50  # Maximum reasonable length
        long_email = f"{'b' * 30}@example.com"
        long_password = "x" * 100  # Long password

        long_data = CreateAdminData(
            name=long_name,
            password=long_password,
            email=long_email
        )

        admin = admin_service.execute('create', create_admin_data=long_data)
        assert admin.name == long_name
        assert admin.email == long_email
        assert admin.verify_password(long_password) is True

    def test_case_sensitive_admin_names(self, admin_service):
        """Test that admin names are case-sensitive"""
        admin1_data = CreateAdminData(name="Admin", password="pass1", email="admin1@example.com")
        admin2_data = CreateAdminData(name="admin", password="pass2", email="admin2@example.com")

        # These should be treated as different admins
        admin1 = admin_service.execute('create', create_admin_data=admin1_data)
        admin2 = admin_service.execute('create', create_admin_data=admin2_data)

        assert admin1.name == "Admin"
        assert admin2.name == "admin"
        assert admin1.admin_id != admin2.admin_id


class TestServiceFactoryIntegration:
    """Integration tests for ServiceFactory"""


    @pytest.fixture
    def service_factory(self, temp_db):
        """Create ServiceFactory with real UoW"""
        connection = Connection.create_connection(url=temp_db, engine=sqlite3)
        create_db = CreateDB(connection)
        create_db.init_data()

        uow = SqliteUnitOfWork(connection)
        return ServiceFactory(uow)

    def test_service_factory_creates_services(self, service_factory):
        """Test that ServiceFactory properly creates services"""
        admin_service = service_factory.get_admin_service()

        assert isinstance(admin_service, AdminService)
        assert admin_service.uow is not None

    def test_service_factory_caching(self, service_factory):
        """Test ServiceFactory service caching"""
        service1 = service_factory.get_admin_service()
        service2 = service_factory.get_admin_service()

        assert service1 is service2  # Should return cached instance

        service_factory.clear_cache()
        service3 = service_factory.get_admin_service()

        assert service1 is not service3  # Should be new instance after clear


# Test configuration
pytestmark = pytest.mark.integration


def test_database_schema_initialization(temp_db):
    """Test that database schema is properly initialized"""
    connection = Connection.create_connection(url=temp_db, engine=sqlite3)
    create_db = CreateDB(connection)
    create_db.init_data()

    # Verify tables exist
    with connection.create_query("SELECT name FROM sqlite_master WHERE type='table'") as query:
        tables = query.get_result()
        table_names = [table[0] for table in tables]

        assert 'admins_aggregate' in table_names
        assert 'admins' in table_names

    # Verify indexes exist
    with connection.create_query("SELECT name FROM sqlite_master WHERE type='index'") as query:
        indexes = query.get_result()
        index_names = [index[0] for index in indexes]

        assert any('idx_admins_name' in name for name in index_names)
        assert any('idx_admins_email' in name for name in index_names)

    connection.close()
