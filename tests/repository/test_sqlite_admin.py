import pytest
import sqlite3
from datetime import datetime
from unittest.mock import Mock, patch
from src.adapters.repository import AdminRepositoryAbstract
from src.domain.model import Admin, AdminEmpty, AdminsAggregate
from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError
from src.adapters.repositorysqlite import SQLiteAdminRepository, CreateDB  # Replace with actual module path


class TestCreateDB:
    def test_create_db_initialization(self):
        """Test CreateDB initialization"""
        mock_conn = Mock(spec=Connection)
        db_creator = CreateDB(mock_conn)

        assert db_creator.conn == mock_conn

    def test_init_data_success(self):
        """Test successful database initialization"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()

        # Mock the query methods
        mock_conn.create_query.return_value = mock_query
        mock_query.get_one_result.return_value = [0]  # Table is empty

        db_creator = CreateDB(mock_conn)
        db_creator.init_data()

        # Verify tables were created
        assert mock_conn.begin_transaction.called
        assert mock_conn.commit.called
        assert mock_conn.create_query.call_count >= 3

    def test_init_data_rollback_on_error(self):
        """Test rollback on initialization error"""
        mock_conn = Mock(spec=Connection)
        mock_conn.create_query.side_effect = Exception("DB error")

        db_creator = CreateDB(mock_conn)

        with pytest.raises(Exception, match="DB error"):
            db_creator.init_data()

        assert mock_conn.rollback.called
        assert not mock_conn.commit.called

    def test_create_indexes_success(self):
        """Test successful index creation"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()
        mock_conn.create_query.return_value = mock_query

        db_creator = CreateDB(mock_conn)
        db_creator.create_indexes()

        assert mock_conn.begin_transaction.called
        assert mock_conn.commit.called
        assert mock_conn.create_query.call_count == 3


class TestSQLiteAdminRepository:
    def test_repository_initialization(self):
        """Test repository initialization"""
        mock_conn = Mock(spec=Connection)
        repo = SQLiteAdminRepository(mock_conn)

        assert repo.conn == mock_conn
        assert isinstance(repo._empty_admin, AdminEmpty)

    def test_get_list_of_admins_success(self):
        """Test successful retrieval of admin list with password hash fix"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()

        # Mock version query
        mock_query.get_one_result.return_value = {'version': 1}

        # Mock admins query
        test_password_hash = "$2b$12$hashedpassword123"
        mock_admins_data = [
            {
                'admin_id': 1,
                'name': 'john',
                'email': 'john@example.com',
                'password_hash': test_password_hash,
                'enabled': 1,
                'date_created': '2023-01-01T12:00:00'
            }
        ]
        mock_query.get_result.return_value = mock_admins_data

        mock_conn.create_query.return_value = mock_query

        repo = SQLiteAdminRepository(mock_conn)
        aggregate = repo._get_list_of_admins()

        assert isinstance(aggregate, AdminsAggregate)
        assert aggregate.version == 1
        assert len(aggregate.admins) == 1

        # Verify the admin was created correctly with the hash
        admin = aggregate.admins['john']
        assert admin.name == 'john'
        assert admin.password == test_password_hash  # Should be the original hash, not re-hashed

    def test_get_list_of_admins_password_hash_preserved(self):
        """Test that password hash is preserved and not re-hashed"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()

        mock_query.get_one_result.return_value = {'version': 1}

        # Create a known bcrypt hash
        original_hash = "$2b$12$E9YrQ1ZcW7a8q9w8e7r6MuV8xYz1A2B3C4D5E6F7G8H9I0J1K2L3"
        mock_admins_data = [{
            'admin_id': 1,
            'name': 'test',
            'email': 'test@example.com',
            'password_hash': original_hash,
            'enabled': 1,
            'date_created': '2023-01-01T12:00:00'
        }]
        mock_query.get_result.return_value = mock_admins_data
        mock_conn.create_query.return_value = mock_query

        repo = SQLiteAdminRepository(mock_conn)
        aggregate = repo._get_list_of_admins()

        admin = aggregate.admins['test']
        # The password should be exactly the same as the original hash
        assert admin.password == original_hash
        # Verify password verification works with the original hash
        assert admin.verify_password("wrongpassword") == False  # Should not verify with wrong password

    def test_get_admin_by_id_password_hash_preserved(self):
        """Test password hash preservation in get_admin_by_id"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()

        original_hash = "$2b$12$originalhash123456789012345678"
        mock_query.get_one_result.return_value = {
            'admin_id': 1,
            'name': 'john',
            'email': 'john@example.com',
            'password_hash': original_hash,
            'enabled': 1,
            'date_created': '2023-01-01T12:00:00'
        }
        mock_conn.create_query.return_value = mock_query

        repo = SQLiteAdminRepository(mock_conn)
        admin = repo._get_admin_by_id(1)

        assert isinstance(admin, Admin)
        assert admin.password == original_hash  # Hash should be preserved

    def test_get_admin_by_name_password_hash_preserved(self):
        """Test password hash preservation in get_admin_by_name"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()

        original_hash = "$2b$12$originalhash123456789012345678"
        mock_query.get_one_result.return_value = {
            'admin_id': 1,
            'name': 'john',
            'email': 'john@example.com',
            'password_hash': original_hash,
            'enabled': 1,
            'date_created': '2023-01-01T12:00:00'
        }
        mock_conn.create_query.return_value = mock_query

        repo = SQLiteAdminRepository(mock_conn)
        admin = repo._get_admin_by_name('john')

        assert isinstance(admin, Admin)
        assert admin.password == original_hash  # Hash should be preserved

    def test_save_admins_success(self):
        """Test successful save of admins"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()
        mock_conn.create_query.return_value = mock_query

        # Create a test admin with a known password hash
        original_hash = "$2b$12$testhash12345678901234567890"
        admin = Admin(1, "john", "password123", "john@example.com", True)
        admin._password_hash = original_hash  # Set the hash directly

        aggregate = AdminsAggregate([admin], version=2)

        repo = SQLiteAdminRepository(mock_conn)
        repo._save_admins(aggregate)

        # Verify the correct hash was saved to database
        call_args = mock_conn.create_query.call_args_list
        insert_call = None
        for call in call_args:
            if "INSERT INTO admins" in call[0][0]:
                insert_call = call
                break

        assert insert_call is not None
        # Verify the password hash in the INSERT statement is the original hash
        assert insert_call[1]['params']['password_hash'] == original_hash

    def test_add_admin_success(self):
        """Test successful admin addition with password hash"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()
        mock_conn.create_query.return_value = mock_query

        admin = Admin(1, "john", "password123", "john@example.com", True)
        original_hash = admin.password  # Get the hash that was created

        repo = SQLiteAdminRepository(mock_conn)
        repo._add_admin(admin)

        # Verify the correct hash was used in the INSERT
        call_args = mock_conn.create_query.call_args_list
        insert_call = None
        for call in call_args:
            if "INSERT INTO admins" in call[0][0]:
                insert_call = call
                break

        assert insert_call is not None
        assert insert_call[1]['params']['password_hash'] == original_hash

    def test_update_admin_preserves_password_hash(self):
        """Test admin update preserves password hash correctly"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()
        mock_query.set_result.return_value = 1
        mock_conn.create_query.return_value = mock_query

        # Create admin with specific hash
        original_hash = "$2b$12$originalhash123456789012345678"
        admin = Admin(1, "john", "newpassword", "john@example.com", False)
        admin._password_hash = original_hash  # Set specific hash

        repo = SQLiteAdminRepository(mock_conn)
        repo._update_admin(admin)

        # Verify the update used the correct hash
        call_args = mock_conn.create_query.call_args_list
        update_call = None
        for call in call_args:
            if "UPDATE admins" in call[0][0]:
                update_call = call
                break

        assert update_call is not None
        assert update_call[1]['params']['password_hash'] == original_hash

    def test_password_verification_after_load(self):
        """Test that password verification works after loading from database"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()

        # Create a known password and its hash
        test_password = "mysecretpassword123"
        test_hash = Admin.str_hash(test_password)  # Hash it properly

        mock_query.get_one_result.return_value = {
            'admin_id': 1,
            'name': 'john',
            'email': 'john@example.com',
            'password_hash': test_hash,  # Use the properly hashed password
            'enabled': 1,
            'date_created': '2023-01-01T12:00:00'
        }
        mock_conn.create_query.return_value = mock_query

        repo = SQLiteAdminRepository(mock_conn)
        admin = repo._get_admin_by_id(1)

        # Password verification should work correctly
        assert admin.verify_password(test_password) == True
        assert admin.verify_password("wrongpassword") == False

    def test_multiple_admins_different_hashes(self):
        """Test loading multiple admins with different password hashes"""
        mock_conn = Mock(spec=Connection)
        mock_query = Mock()

        mock_query.get_one_result.return_value = {'version': 1}

        # Create different hashes for different admins
        hash1 = "$2b$12$hash1123456789012345678901234"
        hash2 = "$2b$12$hash2123456789012345678901234"

        mock_admins_data = [
            {
                'admin_id': 1,
                'name': 'john',
                'email': 'john@example.com',
                'password_hash': hash1,
                'enabled': 1,
                'date_created': '2023-01-01T12:00:00'
            },
            {
                'admin_id': 2,
                'name': 'jane',
                'email': 'jane@example.com',
                'password_hash': hash2,
                'enabled': 1,
                'date_created': '2023-01-01T12:00:00'
            }
        ]
        mock_query.get_result.return_value = mock_admins_data
        mock_conn.create_query.return_value = mock_query

        repo = SQLiteAdminRepository(mock_conn)
        aggregate = repo._get_list_of_admins()

        # Verify each admin has their correct hash preserved
        assert aggregate.admins['john'].password == hash1
        assert aggregate.admins['jane'].password == hash2
        assert aggregate.admins['john'].password != aggregate.admins['jane'].password


class TestIntegrationWithFixedPassword:
    #"""Integration tests verifying the password hash fix"""

   ''' def test_end_to_end_password_preservation(self):
        """Test complete workflow with password hash preservation"""
        # Create in-memory database connection
        conn = sqlite3.connect(":memory:")
        connection = Connection(conn, sqlite3)

        # Initialize database
        db_creator = CreateDB(connection)
        db_creator.init_data()

        # Create repository
        repo = SQLiteAdminRepository(connection)

        # Create and add admin
        original_password = "mysecretpassword123"
        admin = Admin(1, "john", original_password, "john@example.com", True)
        original_hash = admin.password  # Store the original hash

        repo._add_admin(admin)

        # Retrieve admin from database
        retrieved_admin = repo._get_admin_by_id(1)

        # Verify the hash was preserved exactly
        assert retrieved_admin.password == original_hash
        assert retrieved_admin.verify_password(original_password) == True
        assert retrieved_admin.verify_password("wrongpassword") == False

        # Test updating the admin
        new_password = "newpassword456"
        retrieved_admin.password = new_password
        new_hash = retrieved_admin.password

        repo._update_admin(retrieved_admin)

        # Retrieve again and verify new hash is preserved
        updated_admin = repo._get_admin_by_id(1)
        assert updated_admin.password == new_hash
        assert updated_admin.verify_password(new_password) == True
        assert updated_admin.verify_password(original_password) == False

        # Cleanup
        conn.close()
'''

'''
    def test_bulk_operations_password_preservation(self):
        """Test bulk save/load operations preserve password hashes"""
        conn = sqlite3.connect(":memory:")
        connection = Connection(conn, sqlite3)

        db_creator = CreateDB(connection)
        db_creator.init_data()
        repo = SQLiteAdminRepository(connection)

        # Create multiple admins with different passwords
        admins = []
        passwords = ["password1", "password2", "password3"]
        hashes = []

        for i, password in enumerate(passwords, 1):
            admin = Admin(i, f"user{i}", password, f"user{i}@example.com", True)
            hashes.append(admin.password)
            admins.append(admin)

        # Save all admins using the aggregate
        aggregate = AdminsAggregate(admins, version=1)
        repo._save_admins(aggregate)

        # Load them back
        loaded_aggregate = repo._get_list_of_admins()

        # Verify all password hashes are preserved correctly
        for i, expected_hash in enumerate(hashes, 1):
            loaded_admin = loaded_aggregate.admins[f"user{i}"]
            assert loaded_admin.password == expected_hash
            assert loaded_admin.verify_password(passwords[i - 1]) == True

        conn.close()

'''
