import pytest
from datetime import datetime, timedelta
from src.domain.model import Admin, AdminEmpty, AdminsAggregate, AdminAbstract
import bcrypt


class TestAdmin:
    def test_admin_creation(self):
        """Test that Admin can be created with valid data"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        assert admin.admin_id == 1
        assert admin.name == "testuser"
        assert admin.email == "test@example.com"
        assert admin.enabled == True
        assert isinstance(admin.date_created, datetime)

    def test_admin_creation_with_custom_date(self):
        """Test Admin creation with specific date_created"""
        custom_date = datetime(2023, 1, 1, 12, 0, 0)
        admin = Admin(1, "testuser", "password123", "test@example.com", True, custom_date)

        assert admin.date_created == custom_date

    def test_admin_password_hashing(self):
        """Test that password is properly hashed"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        # Password should be hashed
        assert admin.verify_password("password123") == True
        assert admin.verify_password("wrongpassword") == False
        assert admin.password.startswith("$2b$")  # bcrypt hash pattern

    def test_admin_password_setter(self):
        """Test password setter updates hash"""
        admin = Admin(1, "testuser", "oldpassword", "test@example.com", True)
        old_hash = admin.password

        admin.password = "newpassword"

        assert admin.password != old_hash
        assert admin.verify_password("newpassword") == True
        assert admin.verify_password("oldpassword") == False

    def test_admin_password_empty_validation(self):
        """Test that empty password raises error"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        with pytest.raises(ValueError, match="Password cannot be empty"):
            admin.password = ""

    def test_admin_property_setters(self):
        """Test all property setters work correctly"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        admin.admin_id = 2
        admin.name = "newname"
        admin.email = "new@example.com"
        admin.enabled = False

        assert admin.admin_id == 2
        assert admin.name == "newname"
        assert admin.email == "new@example.com"
        assert admin.enabled == False

    def test_admin_equality(self):
        """Test admin equality based on name"""
        admin1 = Admin(1, "sameuser", "pass1", "test1@example.com", True)
        admin2 = Admin(2, "sameuser", "pass2", "test2@example.com", False)
        admin3 = Admin(3, "different", "pass3", "test3@example.com", True)

        assert admin1 == admin2  # Same name
        assert admin1 != admin3  # Different name

    def test_admin_equality_with_admin_empty(self):
        """Test admin equality with AdminEmpty"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        empty_admin = AdminEmpty()

        assert admin != empty_admin
        assert empty_admin != admin

    def test_admin_hash(self):
        """Test admin hashing based on name"""
        admin1 = Admin(1, "testuser", "pass1", "test1@example.com", True)
        admin2 = Admin(2, "testuser", "pass2", "test2@example.com", False)

        assert hash(admin1) == hash(admin2)  # Same name, same hash

    def test_admin_boolean(self):
        """Test boolean conversion"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        assert bool(admin) == True

    def test_admin_is_empty(self):
        """Test is_empty method returns False for real admin"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        assert admin.is_empty() == False

    def test_admin_static_methods(self):
        """Test static hash and verify methods"""
        password = "testpassword"
        hash_result = Admin.str_hash(password)

        assert Admin.str_verify(password, hash_result) == True
        assert Admin.str_verify("wrongpassword", hash_result) == False


class TestAdminEmpty:
    def test_admin_empty_creation(self):
        """Test AdminEmpty creation with default values"""
        empty = AdminEmpty()

        assert empty.admin_id == 0
        assert empty.name == ""
        assert empty.email == ""
        assert empty.enabled == False
        assert isinstance(empty.date_created, datetime)

    def test_admin_empty_property_setters_raise_errors(self):
        """Test that AdminEmpty property setters raise errors"""
        empty = AdminEmpty()

        with pytest.raises(AttributeError, match="Cannot set admin_id on empty admin"):
            empty.admin_id = 1

        with pytest.raises(AttributeError, match="Cannot set name on empty admin"):
            empty.name = "test"

        with pytest.raises(AttributeError, match="Cannot set email on empty admin"):
            empty.email = "test@example.com"

        with pytest.raises(AttributeError, match="Cannot set enabled on empty admin"):
            empty.enabled = True

    def test_admin_empty_password_access(self):
        """Test AdminEmpty password access raises error"""
        empty = AdminEmpty()

        # FIXED: Match the actual error message from your code
        with pytest.raises(AttributeError, match="Cannot call 'password' on empty admin"):
            _ = empty.password

        with pytest.raises(AttributeError, match="Cannot set password on empty admin"):
            empty.password = "test"

    def test_admin_empty_verify_password(self):
        """Test AdminEmpty verify_password always returns False"""
        empty = AdminEmpty()
        assert empty.verify_password("anypassword") == False

    def test_admin_empty_is_empty(self):
        """Test is_empty method returns True for empty admin"""
        empty = AdminEmpty()
        assert empty.is_empty() == True

    def test_admin_empty_boolean(self):
        """Test boolean conversion returns False"""
        empty = AdminEmpty()
        assert bool(empty) == False

    def test_admin_empty_equality(self):
        """Test AdminEmpty equality"""
        empty1 = AdminEmpty()
        empty2 = AdminEmpty()
        admin = Admin(1, "test", "pass", "test@example.com", True)

        assert empty1 == empty2
        assert empty1 != admin

    def test_admin_empty_method_access(self):
        """Test that any method access raises appropriate error"""
        empty = AdminEmpty()

        with pytest.raises(AttributeError, match="Cannot call 'some_method' on empty admin"):
            empty.some_method()


class TestAdminsAggregate:
    def test_aggregate_creation_empty(self):
        """Test AdminsAggregate creation with no initial admins"""
        aggregate = AdminsAggregate()
        assert aggregate.is_empty() == True
        assert aggregate.get_admin_count() == 0
        assert aggregate.version == 0

    def test_aggregate_creation_with_admins(self):
        """Test AdminsAggregate creation with initial admins"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        # FIXED: Version DOES increment when adding admins during initialization
        aggregate = AdminsAggregate([admin])

        assert aggregate.is_empty() == False
        assert aggregate.get_admin_count() == 1
        assert aggregate.version == 1  # Version increments when adding initial admins

    def test_create_admin_success(self):
        """Test successful admin creation"""
        aggregate = AdminsAggregate()
        admin = aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        assert admin.admin_id == 1
        assert admin.name == "testuser"
        assert aggregate.get_admin_count() == 1
        assert aggregate.admin_exists("testuser") == True
        assert aggregate.version == 1  # Version increments on add

    def test_create_admin_validation_errors(self):
        """Test admin creation validation errors"""
        aggregate = AdminsAggregate()

        # Test empty name
        with pytest.raises(ValueError, match="Admin name cannot be empty"):
            aggregate.create_admin(1, "", "test@example.com", "password123", True)

        # Test invalid email
        with pytest.raises(ValueError, match="Invalid email format"):
            aggregate.create_admin(1, "testuser", "invalid-email", "password123", True)

        # Test short password
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            aggregate.create_admin(1, "testuser", "test@example.com", "short", True)

    def test_create_admin_duplicate_name(self):
        """Test duplicate name validation"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test1@example.com", "password123", True)

        with pytest.raises(ValueError, match="Admin with name 'testuser' already exists"):
            aggregate.create_admin(2, "testuser", "test2@example.com", "password456", True)

    def test_create_admin_duplicate_id(self):
        """Test duplicate ID validation"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "user1", "test1@example.com", "password123", True)

        with pytest.raises(ValueError, match="Admin with ID 1 already exists"):
            aggregate.create_admin(1, "user2", "test2@example.com", "password456", True)

    def test_add_admin_validation(self):
        """Test adding existing admin raises error"""
        aggregate = AdminsAggregate()
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        aggregate.add_admin(admin)

        # FIXED: Your code checks ID uniqueness first, then name uniqueness
        # The error message will be about ID, not name
        with pytest.raises(ValueError, match="Admin with ID 1 already exists"):
            aggregate.add_admin(admin)

    def test_add_admin_duplicate_name_different_id(self):
        """Test adding admin with duplicate name but different ID"""
        aggregate = AdminsAggregate()
        admin1 = Admin(1, "testuser", "password123", "test1@example.com", True)
        admin2 = Admin(2, "testuser", "password456", "test2@example.com", True)  # Same name, different ID

        aggregate.add_admin(admin1)

        # This should fail on name uniqueness check (after ID passes)
        with pytest.raises(ValueError, match="Admin with name 'testuser' already exists"):
            aggregate.add_admin(admin2)

    def test_get_admin_by_name(self):
        """Test get_admin_by_name returns correct admin"""
        aggregate = AdminsAggregate()
        admin = aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        # Test existing admin
        found_admin = aggregate.get_admin_by_name("testuser")
        assert found_admin == admin

        # Test non-existing admin returns AdminEmpty
        empty_admin = aggregate.get_admin_by_name("nonexistent")
        assert isinstance(empty_admin, AdminEmpty)
        assert empty_admin.is_empty() == True

    def test_require_admin_by_name(self):
        """Test require_admin_by_name raises error for non-existent admin"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        # Test existing admin
        admin = aggregate.require_admin_by_name("testuser")
        assert admin.name == "testuser"

        # Test non-existing admin raises error
        with pytest.raises(ValueError, match="Admin 'nonexistent' not found"):
            aggregate.require_admin_by_name("nonexistent")

    def test_admin_exists(self):
        """Test admin_exists method"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        assert aggregate.admin_exists("testuser") == True
        assert aggregate.admin_exists("nonexistent") == False

    def test_change_admin_email(self):
        """Test changing admin email"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "old@example.com", "password123", True)

        aggregate.change_admin_email("testuser", "new@example.com")

        admin = aggregate.require_admin_by_name("testuser")
        assert admin.email == "new@example.com"
        assert aggregate.version == 2  # Initial create + email change

        # Test invalid email format
        with pytest.raises(ValueError, match="Invalid email format"):
            aggregate.change_admin_email("testuser", "invalid-email")

    def test_change_admin_password(self):
        """Test changing admin password"""
        aggregate = AdminsAggregate()
        admin = aggregate.create_admin(1, "testuser", "test@example.com", "oldpassword", True)

        # Verify old password works
        assert admin.verify_password("oldpassword") == True

        aggregate.change_admin_password("testuser", "newpassword")

        # Verify new password works and old doesn't
        updated_admin = aggregate.require_admin_by_name("testuser")
        assert updated_admin.verify_password("newpassword") == True
        assert updated_admin.verify_password("oldpassword") == False
        assert aggregate.version == 2

        # Test short password
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            aggregate.change_admin_password("testuser", "short")

    def test_toggle_admin_status(self):
        """Test toggling admin status"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        # Toggle from True to False
        aggregate.toggle_admin_status("testuser")
        admin = aggregate.require_admin_by_name("testuser")
        assert admin.enabled == False
        assert aggregate.version == 2

        # Toggle from False to True
        aggregate.toggle_admin_status("testuser")
        admin = aggregate.require_admin_by_name("testuser")
        assert admin.enabled == True
        assert aggregate.version == 3

    def test_set_admin_status(self):
        """Test setting specific admin status"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        # Set to False
        aggregate.set_admin_status("testuser", False)
        admin = aggregate.require_admin_by_name("testuser")
        assert admin.enabled == False
        assert aggregate.version == 2

        # Set to True
        aggregate.set_admin_status("testuser", True)
        admin = aggregate.require_admin_by_name("testuser")
        assert admin.enabled == True
        assert aggregate.version == 3

    def test_remove_admin(self):
        """Test removing admin"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        assert aggregate.get_admin_count() == 1
        aggregate.remove_admin("testuser")
        assert aggregate.get_admin_count() == 0
        assert aggregate.admin_exists("testuser") == False
        assert aggregate.version == 2

        # Test removing non-existent admin
        with pytest.raises(ValueError, match="Admin 'nonexistent' not found"):
            aggregate.remove_admin("nonexistent")

    def test_get_enabled_disabled_admins(self):
        """Test getting enabled and disabled admins"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "enabled_user", "test1@example.com", "password123", True)
        aggregate.create_admin(2, "disabled_user", "test2@example.com", "password123", False)

        enabled = aggregate.get_enabled_admins()
        disabled = aggregate.get_disabled_admins()

        assert len(enabled) == 1
        assert len(disabled) == 1
        assert enabled[0].name == "enabled_user"
        assert disabled[0].name == "disabled_user"

    def test_get_all_admins_excludes_empty(self):
        """Test get_all_admins excludes empty admins"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        # This should not include the empty admin returned by get_admin_by_name
        empty_admin = aggregate.get_admin_by_name("nonexistent")
        all_admins = aggregate.get_all_admins()

        assert len(all_admins) == 1
        assert empty_admin not in all_admins

    def test_static_validation_methods(self):
        """Test static validation methods"""
        # Test valid inputs
        assert AdminsAggregate._validate_name(" testuser ") == "testuser"
        assert AdminsAggregate._validate_email("test@example.com") == "test@example.com"
        assert AdminsAggregate._validate_password("password123") == "password123"

        # Test invalid inputs
        with pytest.raises(ValueError, match="Admin name cannot be empty"):
            AdminsAggregate._validate_name("")

        with pytest.raises(ValueError, match="Invalid email format"):
            AdminsAggregate._validate_email("invalid-email")

        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            AdminsAggregate._validate_password("short")
