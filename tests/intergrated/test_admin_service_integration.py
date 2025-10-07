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

@pytest.fixture
def admin_service(temp_db):
    """Create fresh AdminService for each test"""
    connection = Connection.create_connection(url=temp_db, engine=sqlite3)
    create_db = CreateDB(connection)
    create_db.init_data()
    create_db.create_indexes()

    uow = SqliteUnitOfWork(connection)
    return AdminService(uow)

@pytest.fixture
def sample_admin_data():
    """Sample admin data for testing"""
    return CreateAdminData(
        name="integration_admin",
        password="securepassword123",
        email="integration@example.com",
        enabled=True
    )



class TestAdminServiceIntegration:
    """Integration tests for AdminService with real database"""



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

    def test_complete_admin_lifecycle(self, admin_service,sample_admin_data):
        """Test complete admin lifecycle: create → update → toggle → verify"""
        # Create admin

        admin = admin_service.execute('create', create_admin_data=sample_admin_data)
        assert admin.enabled is True
        assert admin.email == sample_admin_data.email

        # Update email
        admin = admin_service.execute('update_email', name=sample_admin_data.name, new_email="updated@example.com")
        assert admin.email == "updated@example.com"

        # Toggle status
        admin = admin_service.execute('toggle_status', name=sample_admin_data.name)
        assert admin.enabled is False

        # Change password
        admin = admin_service.execute('change_password', name=sample_admin_data.name, new_password="newpass123")
        assert admin.verify_password("newpass123") is True

        # Verify all changes persisted
        final_admin = admin_service.execute('get_by_name', name=sample_admin_data.name)
        assert final_admin.email == "updated@example.com"
        assert final_admin.enabled is False
        assert final_admin.verify_password("newpass123") is True

    def test_multiple_admins_operations(self, admin_service):
        """Test operations with multiple admins"""
        # Create multiple admins
        admins_data = [
            CreateAdminData(name=f"admin_{i}", password=f"pass01234567890_{i}", email=f"admin{i}@example.com")
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
        create_db.create_indexes()

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
        admin1_data = CreateAdminData(name="Admin", password="pass101234567890", email="admin1@example.com")
        admin2_data = CreateAdminData(name="admin", password="pass201234567890", email="admin2@example.com")

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
        create_db.create_indexes()

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



class TestAdminServiceRemoveIntegration:
    """Integration tests for remove_admin functionality"""


    @pytest.fixture
    def populated_admin_service(self, admin_service, sample_admin_data):
        """Create AdminService with pre-populated admins"""
        # Create multiple admins for testing
        admin1_data = CreateAdminData(
            name="admin1",
            password="password1",
            email="admin1@example.com",
            enabled=True
        )
        admin2_data = CreateAdminData(
            name="admin2",
            password="password2",
            email="admin2@example.com",
            enabled=False
        )
        admin3_data = CreateAdminData(
            name="admin3",
            password="password3",
            email="admin3@example.com",
            enabled=True
        )

        admin_service.execute('create', create_admin_data=admin1_data)
        admin_service.execute('create', create_admin_data=admin2_data)
        admin_service.execute('create', create_admin_data=admin3_data)

        return admin_service

    def test_remove_admin_by_id_success(self, populated_admin_service):
        """Integration test: Remove admin by ID and verify persistence"""
        # Get initial state
        admins_before = populated_admin_service.list_all_admins()
        initial_count = len(admins_before)
        admin_to_remove = admins_before[0]  # Get first admin

        # Verify admin exists before removal
        assert populated_admin_service.admin_exists(admin_to_remove.name) is True
        assert populated_admin_service.admin_exists_by_id(admin_to_remove.admin_id) is True

        # Remove admin by ID
        populated_admin_service.execute('remove_by_id', admin_id=admin_to_remove.admin_id)

        # Verify removal
        admins_after = populated_admin_service.list_all_admins()
        assert len(admins_after) == initial_count - 1

        # Verify the removed admin no longer exists
        assert populated_admin_service.admin_exists(admin_to_remove.name) is False
        assert populated_admin_service.admin_exists_by_id(admin_to_remove.admin_id) is False

        # Verify we can't get the removed admin by name
        with pytest.raises(ValueError, match=f"Admin '{admin_to_remove.name}' not found"):
            populated_admin_service.execute('get_by_name', name=admin_to_remove.name)

        # Verify we can't get the removed admin by ID
        with pytest.raises(ValueError, match=f"Admin with ID {admin_to_remove.admin_id} not found"):
            populated_admin_service.execute('get_by_id', admin_id=admin_to_remove.admin_id)

        # Verify remaining admins are intact
        remaining_names = [admin.name for admin in admins_after]
        assert admin_to_remove.name not in remaining_names

    def test_remove_admin_by_id_nonexistent(self, admin_service):
        """Integration test: Try to remove admin by non-existent ID"""
        with pytest.raises(ValueError, match="Admin with ID 9999 not found"):
            admin_service.execute('remove_by_id', admin_id=9999)

    def test_remove_multiple_admins_sequentially(self, populated_admin_service):
        """Integration test: Remove multiple admins sequentially"""
        # Get initial admins
        admins = populated_admin_service.list_all_admins()
        initial_count = len(admins)

        # Remove first admin
        admin1 = admins[0]
        populated_admin_service.execute('remove_by_id', admin_id=admin1.admin_id)

        # Verify first removal
        admins_after_first = populated_admin_service.list_all_admins()
        assert len(admins_after_first) == initial_count - 1
        assert populated_admin_service.admin_exists_by_id(admin1.admin_id) is False

        # Remove second admin
        admin2 = admins_after_first[0]
        populated_admin_service.execute('remove_by_id', admin_id=admin2.admin_id)

        # Verify second removal
        admins_after_second = populated_admin_service.list_all_admins()
        assert len(admins_after_second) == initial_count - 2
        assert populated_admin_service.admin_exists_by_id(admin2.admin_id) is False

        # Verify final state
        final_admins = populated_admin_service.list_all_admins()
        assert len(final_admins) == initial_count - 2

    def test_remove_admin_persistence(self, admin_service):
        """Integration test: Verify removal persists across service instances"""
        # Create admin
        admin_data = CreateAdminData(
            name="persistence_test",
            password="password123",
            email="persistence@example.com"
        )
        created_admin = admin_service.execute('create', create_admin_data=admin_data)
        admin_id = created_admin.admin_id

        # Verify admin exists
        assert admin_service.admin_exists("persistence_test") is True

        # Remove admin
        admin_service.execute('remove_by_id', admin_id=admin_id)

        # Create new service instance (simulating new request/transaction)
        connection = admin_service.uow.connection
        new_uow = SqliteUnitOfWork(connection)
        new_admin_service = AdminService(new_uow)

        # Verify removal persists in new service instance
        assert new_admin_service.admin_exists("persistence_test") is False
        with pytest.raises(ValueError, match=f"Admin with ID {admin_id} not found"):
            new_admin_service.execute('get_by_id', admin_id=admin_id)

    def test_remove_admin_after_other_operations(self, admin_service):
        """Integration test: Remove admin after performing other operations"""
        # Create multiple admins
        admin1_data = CreateAdminData(name="admin_a", password="pass101234567890", email="a@example.com")
        admin2_data = CreateAdminData(name="admin_b", password="pass201234567890", email="b@example.com")
        admin3_data = CreateAdminData(name="admin_c", password="pass301234567890", email="c@example.com")

        admin1 = admin_service.execute('create', create_admin_data=admin1_data)
        admin2 = admin_service.execute('create', create_admin_data=admin2_data)
        admin3 = admin_service.execute('create', create_admin_data=admin3_data)

        # Perform various operations before removal
        admin_service.execute('update_email', name="admin_b", new_email="b_updated@example.com")
        admin_service.execute('toggle_status', name="admin_c")
        admin_service.execute('change_password', name="admin_a", new_password="newpass1")

        # Remove one admin
        admin_service.execute('remove_by_id', admin_id=admin2.admin_id)

        # Verify state after removal
        remaining_admins = admin_service.list_all_admins()
        assert len(remaining_admins) == 2

        remaining_names = [admin.name for admin in remaining_admins]
        assert "admin_b" not in remaining_names
        assert "admin_a" in remaining_names
        assert "admin_c" in remaining_names

        # Verify remaining admins still have their updated data
        admin_a = admin_service.execute('get_by_name', name="admin_a")
        assert admin_a.verify_password("newpass1") is True

        admin_c = admin_service.execute('get_by_name', name="admin_c")
        assert admin_c.enabled is False  # Was toggled from default True

    def test_remove_admin_and_verify_aggregate_state(self, populated_admin_service):
        """Integration test: Verify aggregate state after removal"""
        # Get initial aggregate state
        with populated_admin_service.uow:
            initial_aggregate = populated_admin_service.uow.admins.get_list_of_admins()
            initial_version = initial_aggregate.version
            initial_admin_count = len(initial_aggregate.get_all_admins())

        # Remove an admin
        admins = populated_admin_service.list_all_admins()
        admin_to_remove = admins[0]
        populated_admin_service.execute('remove_by_id', admin_id=admin_to_remove.admin_id)

        # Verify aggregate state after removal
        with populated_admin_service.uow:
            updated_aggregate = populated_admin_service.uow.admins.get_list_of_admins()
            updated_version = updated_aggregate.version
            updated_admin_count = len(updated_aggregate.get_all_admins())

            # Version should be incremented
            assert updated_version > initial_version

            # Admin count should be reduced
            assert updated_admin_count == initial_admin_count - 1

            # Removed admin should not be in aggregate
            assert not updated_aggregate.admin_exists(admin_to_remove.name)

    def test_remove_admin_transaction_rollback(self, admin_service):
        """Integration test: Verify transaction rollback on removal failure"""
        # Create an admin
        admin_data = CreateAdminData(
            name="rollback_test",
            password="password123",
            email="rollback@example.com"
        )
        created_admin = admin_service.execute('create', create_admin_data=admin_data)

        # Try to remove non-existent admin (should fail and rollback)
        with pytest.raises(ValueError, match="Admin with ID 9999 not found"):
            admin_service.execute('remove_by_id', admin_id=9999)

        # Verify original admin still exists (transaction was rolled back)
        assert admin_service.admin_exists("rollback_test") is True
        assert admin_service.admin_exists_by_id(created_admin.admin_id) is True

        # Verify we can still retrieve the admin
        retrieved_admin = admin_service.execute('get_by_name', name="rollback_test")
        assert retrieved_admin.admin_id == created_admin.admin_id

    def test_remove_all_admins_sequentially(self, populated_admin_service):
        """Integration test: Remove all admins one by one"""
        admins = populated_admin_service.list_all_admins()
        initial_count = len(admins)

        # Remove all admins
        for admin in admins:
            populated_admin_service.execute('remove_by_id', admin_id=admin.admin_id)

        # Verify all admins are removed
        final_admins = populated_admin_service.list_all_admins()
        assert len(final_admins) == 0

        # Verify admin_exists returns False for all removed admins
        for admin in admins:
            assert populated_admin_service.admin_exists(admin.name) is False
            assert populated_admin_service.admin_exists_by_id(admin.admin_id) is False

    def test_remove_admin_and_recreate_same_name(self, admin_service):
        """Integration test: Remove admin and recreate with same name"""
        # Create and remove admin
        admin_data = CreateAdminData(
            name="recreate_test",
            password="password1",
            email="test1@example.com"
        )
        first_admin = admin_service.execute('create', create_admin_data=admin_data)
        first_id = first_admin.admin_id

        # Remove the admin
        admin_service.execute('remove_by_id', admin_id=first_id)

        # Recreate admin with same name but different data
        new_admin_data = CreateAdminData(
            name="recreate_test",  # Same name
            password="different_password",  # Different password
            email="test2@example.com",  # Different email
            enabled=False  # Different status
        )
        new_admin = admin_service.execute('create', create_admin_data=new_admin_data)



        # Verify new admin has the new data
        assert new_admin.name == "recreate_test"
        assert new_admin.email == "test2@example.com"
        assert new_admin.enabled is False
        assert new_admin.verify_password("different_password") is True

        # Verify old password doesn't work
        assert new_admin.verify_password("password1") is False


class TestAdminServiceRemoveEdgeCases:
    """Integration tests for edge cases in remove_admin functionality"""

    @pytest.fixture
    def admin_service(self, temp_db):
        """Create fresh AdminService for each test"""
        connection = Connection.create_connection(url=temp_db, engine=sqlite3)
        create_db = CreateDB(connection)
        create_db.init_data()

        uow = SqliteUnitOfWork(connection)
        return AdminService(uow)

    def test_remove_admin_twice(self, admin_service):
        """Integration test: Try to remove same admin twice"""
        # Create admin
        admin_data = CreateAdminData(
            name="duplicate_remove_test",
            password="password123",
            email="duplicate@example.com"
        )
        created_admin = admin_service.execute('create', create_admin_data=admin_data)

        # Remove first time (should succeed)
        admin_service.execute('remove_by_id', admin_id=created_admin.admin_id)

        # Remove second time (should fail)
        with pytest.raises(ValueError, match=f"Admin with ID {created_admin.admin_id} not found"):
            admin_service.execute('remove_by_id', admin_id=created_admin.admin_id)

    def test_remove_admin_with_special_characters(self, admin_service):
        """Integration test: Remove admin with special characters in name"""
        special_name_data = CreateAdminData(
            name="admin-with-dash_123",
            password="password123",
            email="special@example.com"
        )

        admin = admin_service.execute('create', create_admin_data=special_name_data)

        # Remove by ID
        admin_service.execute('remove_by_id', admin_id=admin.admin_id)

        # Verify removal
        assert admin_service.admin_exists("admin-with-dash_123") is False
        with pytest.raises(ValueError, match=f"Admin with ID {admin.admin_id} not found"):
            admin_service.execute('get_by_id', admin_id=admin.admin_id)

    def test_remove_admin_and_verify_database_cleanup(self, admin_service):
        """Integration test: Verify database is properly cleaned up after removal"""
        # Create multiple admins
        admin1_data = CreateAdminData(name="db_cleanup1", password="pass101234567890", email="clean1@example.com")
        admin2_data = CreateAdminData(name="db_cleanup2", password="pass201234567890", email="clean2@example.com")

        admin1 = admin_service.execute('create', create_admin_data=admin1_data)
        admin2 = admin_service.execute('create', create_admin_data=admin2_data)

        # Verify admins exist in database
        with admin_service.uow:
            aggregate = admin_service.uow.admins.get_list_of_admins()
            assert aggregate.admin_exists("db_cleanup1") is True
            assert aggregate.admin_exists("db_cleanup2") is True

        # Remove one admin
        admin_service.execute('remove_by_id', admin_id=admin1.admin_id)

        # Verify database state
        with admin_service.uow:
            updated_aggregate = admin_service.uow.admins.get_list_of_admins()
            assert updated_aggregate.admin_exists("db_cleanup1") is False
            assert updated_aggregate.admin_exists("db_cleanup2") is True

            # Check specific admin records
            admins = updated_aggregate.get_all_admins()
            admin_names = [admin.name for admin in admins]
            assert "db_cleanup1" not in admin_names
            assert "db_cleanup2" in admin_names





# Test configuration
pytestmark = pytest.mark.integration


def test_database_schema_initialization(temp_db):
    """Test that database schema is properly initialized"""
    connection = Connection.create_connection(url=temp_db, engine=sqlite3)
    create_db = CreateDB(connection)
    create_db.init_data()
    create_db.create_indexes()

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
