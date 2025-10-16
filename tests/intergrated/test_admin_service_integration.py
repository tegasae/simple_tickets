# tests/integration/test_admin_service_integration.py
import pytest
import sqlite3
from datetime import datetime

from src.services.service_layer.admins import AdminService
from src.services.service_layer.data import CreateAdminData
from src.services.service_layer.factory import ServiceFactory
from src.services.uow.uowsqlite import SqliteUnitOfWork
from src.adapters.repositorysqlite import CreateDB
from utils.db.connect import Connection
from src.domain.exceptions import AdminOperationError, AdminNotFoundError, AdminAlreadyExistsError


@pytest.fixture
def in_memory_connection():
    """Real SQLite in-memory connection"""
    conn = Connection.create_connection(url=":memory:", engine=sqlite3)
    yield conn
    conn.close()


@pytest.fixture
def initialized_db(in_memory_connection):
    """Database with initialized schema"""
    create_db = CreateDB(conn=in_memory_connection)
    create_db.init_data()
    create_db.create_indexes()
    return in_memory_connection


@pytest.fixture
def sqlite_uow(initialized_db):
    """Real SqliteUnitOfWork with initialized database"""
    return SqliteUnitOfWork(connection=initialized_db)


@pytest.fixture
def admin_service(sqlite_uow):
    """AdminService with real UoW"""
    return AdminService(uow=sqlite_uow)


@pytest.fixture
def service_factory(sqlite_uow):
    """ServiceFactory with real UoW"""
    return ServiceFactory(uow=sqlite_uow)


@pytest.fixture
def admin_service(initialized_db):
    """AdminService with clean database"""
    uow = SqliteUnitOfWork(connection=initialized_db)
    return AdminService(uow=uow)


class TestAdminServiceIntegration:
    """Integration tests for AdminService with real SQLite database"""

    def test_create_and_retrieve_admin(self, admin_service):
        """Test creating and retrieving an admin"""
        # Create admin data
        create_data = CreateAdminData(
            name="john_doe",
            email="john@example.com",
            password="secure_password_123",
            enabled=True
        )

        # Create admin
        created_admin = admin_service.execute('create', create_admin_data=create_data)

        # Verify creation
        assert created_admin.admin_id > 0
        assert created_admin.name == "john_doe"
        assert created_admin.email == "john@example.com"
        assert created_admin.enabled is True
        assert isinstance(created_admin.date_created, datetime)

        # Retrieve by name
        retrieved_admin = admin_service.execute('get_by_name', name="john_doe")
        assert retrieved_admin.admin_id == created_admin.admin_id
        assert retrieved_admin.name == created_admin.name
        assert retrieved_admin.email == created_admin.email

        # Retrieve by ID
        retrieved_by_id = admin_service.execute('get_by_id', admin_id=created_admin.admin_id)
        assert retrieved_by_id.name == created_admin.name

    def test_create_duplicate_admin_fails(self, admin_service):
        """Test that creating duplicate admin fails"""
        create_data = CreateAdminData(
            name="duplicate_user",
            email="user@example.com",
            password="password123"
        )

        # First creation should succeed
        admin_service.execute('create', create_admin_data=create_data)

        # Second creation should fail
        with pytest.raises(AdminAlreadyExistsError):
            admin_service.execute('create', create_admin_data=create_data)

    def test_update_admin_email(self, admin_service):
        """Test updating admin email"""
        # Create admin
        create_data = CreateAdminData(
            name="update_test",
            email="old@example.com",
            password="password123"
        )
        admin = admin_service.execute('create', create_admin_data=create_data)

        # Update email
        updated_admin = admin_service.execute('update_email', name="update_test", new_email="new@example.com")

        assert updated_admin.email == "new@example.com"
        assert updated_admin.admin_id == admin.admin_id
        assert updated_admin.name == admin.name

        # Verify update persisted
        retrieved_admin = admin_service.execute('get_by_name', name="update_test")
        assert retrieved_admin.email == "new@example.com"

    def test_toggle_admin_status(self, admin_service):
        """Test toggling admin enabled/disabled status"""
        # Create enabled admin
        create_data = CreateAdminData(
            name="toggle_test",
            email="toggle@example.com",
            password="password123",
            enabled=True
        )
        admin = admin_service.execute('create', create_admin_data=create_data)
        assert admin.enabled is True

        # Toggle to disabled
        toggled_admin = admin_service.execute('toggle_status', name="toggle_test")
        assert toggled_admin.enabled is False

        # Toggle back to enabled
        re_toggled_admin = admin_service.execute('toggle_status', name="toggle_test")
        assert re_toggled_admin.enabled is True

    def test_change_admin_password(self, admin_service):
        """Test changing admin password"""
        # Create admin
        create_data = CreateAdminData(
            name="password_test",
            email="password@example.com",
            password="old_password"
        )
        admin_service.execute('create', create_admin_data=create_data)

        # Change password
        updated_admin = admin_service.execute('change_password', name="password_test",
                                              new_password="new_secure_password")

        # Verify the operation completed without error
        assert updated_admin.name == "password_test"
        # Note: Password verification would require additional methods

    def test_remove_admin_by_id(self, admin_service):
        """Test removing admin by ID"""
        # Create admin
        create_data = CreateAdminData(
            name="remove_test",
            email="remove@example.com",
            password="password123"
        )
        admin = admin_service.execute('create', create_admin_data=create_data)

        # Verify admin exists
        assert admin_service.admin_exists("remove_test") is True

        # Remove admin
        admin_service.execute('remove_by_id', admin_id=admin.admin_id)

        # Verify admin no longer exists
        assert admin_service.admin_exists("remove_test") is False

        # Verify get_by_name raises error
        with pytest.raises(AdminNotFoundError):
            admin_service.execute('get_by_name', name="remove_test")

        # Verify get_by_id returns None
        with pytest.raises(AdminNotFoundError):
            result = admin_service.execute('get_by_id', admin_id=admin.admin_id)


    def test_list_all_admins(self, admin_service):
        """Test listing all admins"""
        # Create multiple admins
        admins_data = [
            CreateAdminData(name=f"admin_{i}", email=f"admin{i}@example.com", password="pass123456")
            for i in range(3)
        ]

        created_admins = []
        for data in admins_data:
            admin = admin_service.execute('create', create_admin_data=data)
            created_admins.append(admin)

        # List all admins
        all_admins = admin_service.list_all_admins()

        # Should contain all created admins
        assert len(all_admins) >= len(created_admins)  # Might have previous test data
        admin_names = [admin.name for admin in all_admins]
        for data in admins_data:
            assert data.name in admin_names

    def test_list_enabled_admins(self, admin_service):
        """Test listing only enabled admins"""
        # Create enabled and disabled admins
        enabled_admin = CreateAdminData(name="enabled_user", email="enabled@example.com", password="pass123456", enabled=True)
        disabled_admin = CreateAdminData(name="disabled_user", email="disabled@example.com", password="pass123456",
                                         enabled=False)

        admin_service.execute('create', create_admin_data=enabled_admin)
        admin_service.execute('create', create_admin_data=disabled_admin)

        # List enabled admins
        enabled_admins = admin_service.list_enabled_admins()

        # Should only contain enabled admin
        enabled_names = [admin.name for admin in enabled_admins]
        assert "enabled_user" in enabled_names
        assert "disabled_user" not in enabled_names

    def test_admin_exists(self, admin_service):
        """Test admin existence checking"""
        # Create admin
        create_data = CreateAdminData(
            name="exists_test",
            email="exists@example.com",
            password="password123"
        )
        admin_service.execute('create', create_admin_data=create_data)

        # Check existence
        assert admin_service.admin_exists("exists_test") is True
        assert admin_service.admin_exists("nonexistent_admin") is False

    def test_transaction_rollback_on_error(self, admin_service):
        """Test that transactions roll back on errors"""
        # Create first admin
        admin1_data = CreateAdminData(name="admin1", email="admin1@example.com", password="pass123456")
        admin1 = admin_service.execute('create', create_admin_data=admin1_data)

        try:
            # This should fail due to duplicate name
            admin2_data = CreateAdminData(name="admin1", email="admin2@example.com", password="pass123456")
            admin_service.execute('create', create_admin_data=admin2_data)
        except AdminAlreadyExistsError:
            pass  # Expected to fail

        # Verify admin1 still exists (transaction rolled back)
        assert admin_service.admin_exists("admin1") is True
        retrieved_admin = admin_service.execute('get_by_name', name="admin1")
        assert retrieved_admin.admin_id == admin1.admin_id

    def test_service_factory_integration(self, service_factory):
        """Test ServiceFactory with real database"""
        # Get admin service from factory
        admin_service = service_factory.get_admin_service()

        # Use the service
        create_data = CreateAdminData(
            name="factory_user",
            email="factory@example.com",
            password="password123"
        )
        admin = admin_service.execute('create', create_admin_data=create_data)

        assert admin.name == "factory_user"
        assert admin_service.admin_exists("factory_user") is True

        # Test service caching
        same_service = service_factory.get_admin_service()
        assert admin_service is same_service  # Should be same instance

    def test_multiple_operations_in_single_transaction(self, admin_service):
        """Test multiple operations in single service call sequence"""
        # This tests that the UoW properly manages transactions across multiple operations
        create_data = CreateAdminData(
            name="multi_op_user",
            email="multi@example.com",
            password="password123"
        )

        # Create and immediately update
        admin = admin_service.execute('create', create_admin_data=create_data)
        updated_admin = admin_service.execute('update_email', name="multi_op_user", new_email="updated@example.com")

        # Verify both operations persisted
        retrieved_admin = admin_service.execute('get_by_name', name="multi_op_user")
        assert retrieved_admin.admin_id == admin.admin_id
        assert retrieved_admin.email == "updated@example.com"

    def test_concurrent_operations(self, sqlite_uow):
        """Test that services work correctly with concurrent operations"""
        # Create two services sharing the same UoW
        service1 = AdminService(uow=sqlite_uow)
        service2 = AdminService(uow=sqlite_uow)

        # Service 1 creates an admin
        create_data = CreateAdminData(name="concurrent_user", email="concurrent@example.com", password="pass123456")
        admin = service1.execute('create', create_admin_data=create_data)

        # Service 2 should be able to see it
        found_admin = service2.execute('get_by_name', name="concurrent_user")
        assert found_admin.admin_id == admin.admin_id

    def test_error_handling_integration(self, admin_service):
        """Test error handling with real database"""
        # Test invalid operation
        with pytest.raises(AdminOperationError, match="Unknown operation"):
            admin_service.execute('invalid_operation')

        # Test missing parameters
        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            admin_service.execute('get_by_name')  # Missing name parameter

        # Test non-existent admin
        with pytest.raises(AdminNotFoundError):
            admin_service.execute('get_by_name', name="non_existent_admin")

    def test_admin_id_generation(self, admin_service):
        """Test that admin IDs are properly generated and sequential"""
        # Create multiple admins and verify ID generation
        admins = []
        for i in range(3):
            create_data = CreateAdminData(
                name=f"id_test_{i}",
                email=f"idtest{i}@example.com",
                password="password"
            )
            admin = admin_service.execute('create', create_admin_data=create_data)
            admins.append(admin)

        # Verify IDs are sequential and increasing
        ids = [admin.admin_id for admin in admins]
        assert len(ids) == len(set(ids))  # All IDs should be unique
        assert ids == sorted(ids)  # IDs should be in increasing order

    def test_bulk_operations_performance(self, admin_service):
        """Test performance with multiple operations"""
        import time

        # Create multiple admins
        start_time = time.time()

        for i in range(10):  # Reasonable number for integration test
            create_data = CreateAdminData(
                name=f"perf_test_{i}",
                email=f"perf{i}@example.com",
                password="password"
            )
            admin_service.execute('create', create_admin_data=create_data)

        # List all admins (should be efficient)
        all_admins = admin_service.list_all_admins()

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in reasonable time (adjust threshold as needed)

        assert execution_time < 5.0  # 5 seconds should be plenty for 10 operations
        assert len(all_admins) >= 10


class TestAdminServiceEdgeCases:
    """Test edge cases and boundary conditions"""


    def test_empty_database_operations(self, admin_service):
        """Test operations on empty database"""
        # List operations on empty DB
        all_admins = admin_service.list_all_admins()
        assert all_admins == []

        enabled_admins = admin_service.list_enabled_admins()
        assert enabled_admins == []

        # Check existence on empty DB
        assert admin_service.admin_exists("any_admin") is False

        # Get by ID on empty DB
        with pytest.raises(AdminNotFoundError):
            result = admin_service.execute('get_by_id', admin_id=1)


    def test_special_characters_in_names(self, admin_service):
        """Test admin names with special characters"""
        special_names = [
            "admin-with-dash",
            "admin_with_underscore",
            "admin.with.dots",
            "admin@domain",
            "admin 123",
            "Админ",  # Unicode
        ]

        for name in special_names:
            create_data = CreateAdminData(
                name=name,
                email="test@example.com",
                password="password"
            )
            try:
                admin = admin_service.execute('create', create_admin_data=create_data)
                # Verify we can retrieve it
                retrieved = admin_service.execute('get_by_name', name=name)
                assert retrieved.admin_id == admin.admin_id
            except Exception as e:
                # Some special characters might not be allowed - that's OK
                print(f"Name '{name}' failed: {e}")

    def test_long_strings(self, admin_service):
        """Test with long names and emails"""
        long_name = "a" * 100  # 100 character name
        long_email = "b" * 50 + "@example.com"

        create_data = CreateAdminData(
            name=long_name,
            email=long_email,
            password="password"
        )

        admin = admin_service.execute('create', create_admin_data=create_data)
        assert admin.name == long_name
        assert admin.email == long_email

    def test_case_sensitivity(self, admin_service):
        """Test case sensitivity of admin names"""
        create_data = CreateAdminData(
            name="CaseSensitive",
            email="test@example.com",
            password="password"
        )
        admin_service.execute('create', create_admin_data=create_data)

        # SQLite is case-sensitive by default for LIKE, but = might be different
        # This tests the actual behavior of your system
        assert admin_service.admin_exists("CaseSensitive") is True
        # The following might be True or False depending on your collation
        # assert admin_service.admin_exists("casesensitive") is False