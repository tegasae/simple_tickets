import pytest
from datetime import datetime
from src.domain.model import Admin, AdminEmpty, AdminsAggregate


class TestAdmin:
    def test_admin_creation_with_valid_data(self):
        """Test Admin creation with all required fields"""
        admin = Admin(
            admin_id=1,
            name="testuser",
            password="password123",
            email="test@example.com",
            enabled=True
        )

        assert admin.admin_id == 1
        assert admin.name == "testuser"
        assert admin.email == "test@example.com"
        assert admin.enabled == True
        assert isinstance(admin.date_created, datetime)

    def test_admin_creation_with_custom_date(self):
        """Test Admin creation with custom date_created"""
        custom_date = datetime(2023, 1, 1, 12, 0, 0)
        admin = Admin(
            admin_id=1,
            name="testuser",
            password="password123",
            email="test@example.com",
            enabled=True,
            date_created=custom_date
        )

        assert admin.date_created == custom_date

    def test_admin_password_hashing_on_creation(self):
        """Test that password is hashed during Admin creation"""
        admin = Admin(
            admin_id=1,
            name="testuser",
            password="password123",
            email="test@example.com",
            enabled=True
        )

        # Password should be hashed, not stored plain text
        assert admin.verify_password("password123") == True
        assert admin.verify_password("wrongpassword") == False
        assert admin._password_hash != "password123"
        assert admin.password.startswith("$2b$")  # bcrypt hash pattern

    def test_admin_password_setter_updates_hash(self):
        """Test password setter properly updates the hash"""
        admin = Admin(
            admin_id=1,
            name="testuser",
            password="oldpassword",
            email="test@example.com",
            enabled=True
        )
        old_hash = admin._password_hash

        admin.password = "newpassword"

        assert admin._password_hash != old_hash
        assert admin.verify_password("newpassword") == True
        assert admin.verify_password("oldpassword") == False

    def test_admin_password_setter_empty_password(self):
        """Test password setter with empty password raises error"""
        admin = Admin(
            admin_id=1,
            name="testuser",
            password="validpassword",
            email="test@example.com",
            enabled=True
        )

        with pytest.raises(ValueError, match="Password cannot be empty"):
            admin.password = ""

    def test_admin_property_setters(self):
        """Test all property setters work correctly"""
        admin = Admin(
            admin_id=1,
            name="original_name",
            password="password123",
            email="original@example.com",
            enabled=True
        )

        admin.admin_id = 2
        admin.name = "new_name"
        admin.email = "new@example.com"
        admin.enabled = False

        assert admin.admin_id == 2
        assert admin.name == "new_name"
        assert admin.email == "new@example.com"
        assert admin.enabled == False

    def test_admin_equality_based_on_name(self):
        """Test admin equality is based on name"""
        admin1 = Admin(1, "same_name", "pass1", "test1@example.com", True)
        admin2 = Admin(2, "same_name", "pass2", "test2@example.com", False)
        admin3 = Admin(3, "different_name", "pass3", "test3@example.com", True)

        assert admin1 == admin2  # Same name
        assert admin1 != admin3  # Different name

    def test_admin_equality_with_admin_empty(self):
        """Test admin equality with AdminEmpty"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        empty_admin = AdminEmpty()

        assert admin != empty_admin
        assert empty_admin != admin

    def test_admin_hash_based_on_name(self):
        """Test admin hash is based on name"""
        admin1 = Admin(1, "testuser", "pass1", "test1@example.com", True)
        admin2 = Admin(2, "testuser", "pass2", "test2@example.com", False)
        admin3 = Admin(3, "different", "pass3", "test3@example.com", True)

        assert hash(admin1) == hash(admin2)  # Same name, same hash
        assert hash(admin1) != hash(admin3)  # Different name, different hash

    def test_admin_boolean_returns_true(self):
        """Test boolean conversion returns True for real admin"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        assert bool(admin) == True

    def test_admin_is_empty_returns_false(self):
        """Test is_empty returns False for real admin"""
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        assert admin.is_empty() == False

    def test_admin_str_hash_static_method(self):
        """Test static str_hash method"""
        hash_result = Admin.str_hash("testpassword")
        assert isinstance(hash_result, str)
        assert hash_result.startswith("$2b$")

        # Verify the hash can be verified
        assert Admin.str_verify("testpassword", hash_result) == True
        assert Admin.str_verify("wrongpassword", hash_result) == False

    def test_admin_str_verify_static_method(self):
        """Test static str_verify method"""
        plain_password = "testpassword"
        hash_result = Admin.str_hash(plain_password)

        assert Admin.str_verify(plain_password, hash_result) == True
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
        """Test that AdminEmpty property setters raise appropriate errors"""
        empty = AdminEmpty()

        with pytest.raises(AttributeError, match="Cannot set admin_id on empty admin"):
            empty.admin_id = 1

        with pytest.raises(AttributeError, match="Cannot set name on empty admin"):
            empty.name = "test"

        with pytest.raises(AttributeError, match="Cannot set email on empty admin"):
            empty.email = "test@example.com"



        with pytest.raises(AttributeError, match="Cannot set enabled on empty admin"):
            empty.enabled = True

    def test_admin_empty_password_access_raises_error(self):
        """Test AdminEmpty password access raises error"""
        empty = AdminEmpty()
        #исключение срабатывает в __getattr__
        with pytest.raises(AttributeError, match="Cannot call 'password' on empty admin"):
            _ = empty.password



    def test_admin_empty_password_setter_raises_error(self):
        """Test AdminEmpty password setter raises error"""
        empty = AdminEmpty()

        with pytest.raises(AttributeError, match="Cannot set password on empty admin"):
            empty.password = "testpassword"

    def test_admin_empty_verify_password_always_false(self):
        """Test AdminEmpty verify_password always returns False"""
        empty = AdminEmpty()
        assert empty.verify_password("anypassword") == False
        assert empty.verify_password("") == False

    def test_admin_empty_is_empty_returns_true(self):
        """Test is_empty returns True for AdminEmpty"""
        empty = AdminEmpty()
        assert empty.is_empty() == True

    def test_admin_empty_boolean_returns_false(self):
        """Test boolean conversion returns False for AdminEmpty"""
        empty = AdminEmpty()
        assert bool(empty) == False

    def test_admin_empty_equality(self):
        """Test AdminEmpty equality"""
        empty1 = AdminEmpty()
        empty2 = AdminEmpty()
        admin = Admin(1, "test", "password", "test@example.com", True)

        assert empty1 == empty2
        assert empty1 != admin
        assert admin != empty1

    def test_admin_empty_method_access_raises_error(self):
        """Test that any method access on AdminEmpty raises appropriate error"""
        empty = AdminEmpty()

        with pytest.raises(AttributeError, match="Cannot call 'some_method' on empty admin"):
            empty.some_method()


class TestAdminsAggregate:
    def test_aggregate_creation_empty(self):
        """Test AdminsAggregate creation with no admins"""
        aggregate = AdminsAggregate()

        assert aggregate.is_empty() == True
        assert aggregate.get_admin_count() == 0
        assert aggregate.version == 0
        assert aggregate.get_all_admins() == []
        assert aggregate.get_enabled_admins() == []
        assert aggregate.get_disabled_admins() == []

    def test_aggregate_creation_with_initial_admins(self):
        """Test AdminsAggregate creation with initial admins"""
        admin1 = Admin(1, "user1", "pass1", "user1@example.com", True)
        admin2 = Admin(2, "user2", "pass2", "user2@example.com", False)

        aggregate = AdminsAggregate([admin1, admin2])

        assert aggregate.get_admin_count() == 2
        assert aggregate.version == 2
        assert not aggregate.is_empty()

    def test_create_admin_success(self):
        """Test successful admin creation"""
        aggregate = AdminsAggregate()
        admin = aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        assert admin.admin_id == 1
        assert admin.name == "testuser"
        assert aggregate.get_admin_count() == 1
        assert aggregate.version == 1
        assert aggregate.admin_exists("testuser") == True

    def test_create_admin_validation_errors(self):
        """Test admin creation validation errors"""
        aggregate = AdminsAggregate()

        # Test empty name
        with pytest.raises(ValueError, match="Admin name cannot be empty"):
            aggregate.create_admin(1, "", "test@example.com", "password123", True)

        # Test whitespace name
        with pytest.raises(ValueError, match="Admin name cannot be empty"):
            aggregate.create_admin(1, "   ", "test@example.com", "password123", True)

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

    def test_add_admin_success(self):
        """Test adding existing admin"""
        aggregate = AdminsAggregate()
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        aggregate.add_admin(admin)

        assert aggregate.get_admin_count() == 1
        assert aggregate.version == 1
        assert aggregate.admin_exists("testuser") == True

    def test_add_admin_duplicate_name(self):
        """Test adding admin with duplicate name"""
        aggregate = AdminsAggregate()
        admin1 = Admin(1, "same_name", "pass1", "test1@example.com", True)
        admin2 = Admin(2, "same_name", "pass2", "test2@example.com", False)

        aggregate.add_admin(admin1)

        with pytest.raises(ValueError, match="Admin with name 'same_name' already exists"):
            aggregate.add_admin(admin2)

    def test_change_admin_success(self):
        """Test changing existing admin"""
        aggregate = AdminsAggregate()
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        aggregate.add_admin(admin)

        updated_admin = Admin(1, "testuser", "newpassword", "new@example.com", False)
        aggregate.change_admin(updated_admin)

        assert aggregate.version == 2
        changed_admin = aggregate.get_admin_by_name("testuser")
        assert changed_admin.email == "new@example.com"
        assert changed_admin.enabled == False

    def test_change_admin_nonexistent(self):
        """Test changing non-existent admin"""
        aggregate = AdminsAggregate()
        admin = Admin(1, "testuser", "password123", "test@example.com", True)

        # Should not raise error, but also not change anything
        aggregate.change_admin(admin)
        assert aggregate.get_admin_count() == 0
        assert aggregate.version == 0

    def test_change_admin_wrong_id(self):
        """Test changing admin with wrong ID"""
        aggregate = AdminsAggregate()
        admin1 = Admin(1, "testuser", "password123", "test@example.com", True)
        aggregate.add_admin(admin1)

        admin_wrong_id = Admin(2, "testuser", "newpassword", "new@example.com", False)
        aggregate.change_admin(admin_wrong_id)

        # Should not change because ID doesn't match
        existing_admin = aggregate.get_admin_by_name("testuser")
        assert existing_admin.admin_id == 1
        assert existing_admin.email == "test@example.com"

    def test_get_admin_by_name_existing(self):
        """Test getting existing admin by name"""
        aggregate = AdminsAggregate()
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        aggregate.add_admin(admin)

        found_admin = aggregate.get_admin_by_name("testuser")
        assert found_admin == admin
        assert not found_admin.is_empty()

    def test_get_admin_by_name_nonexistent(self):
        """Test getting non-existent admin returns AdminEmpty"""
        aggregate = AdminsAggregate()

        found_admin = aggregate.get_admin_by_name("nonexistent")
        assert isinstance(found_admin, AdminEmpty)
        assert found_admin.is_empty()

    def test_require_admin_by_name_existing(self):
        """Test requiring existing admin by name"""
        aggregate = AdminsAggregate()
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        aggregate.add_admin(admin)

        found_admin = aggregate.require_admin_by_name("testuser")
        assert found_admin == admin

    def test_require_admin_by_name_nonexistent(self):
        """Test requiring non-existent admin raises error"""
        aggregate = AdminsAggregate()

        with pytest.raises(ValueError, match="Admin 'nonexistent' not found"):
            aggregate.require_admin_by_name("nonexistent")

    def test_admin_exists(self):
        """Test admin_exists method"""
        aggregate = AdminsAggregate()
        admin = Admin(1, "testuser", "password123", "test@example.com", True)
        aggregate.add_admin(admin)

        assert aggregate.admin_exists("testuser") == True
        assert aggregate.admin_exists("nonexistent") == False

    def test_change_admin_email_success(self):
        """Test changing admin email"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "old@example.com", "password123", True)

        aggregate.change_admin_email("testuser", "new@example.com")

        admin = aggregate.require_admin_by_name("testuser")
        assert admin.email == "new@example.com"
        assert aggregate.version == 2

    def test_change_admin_email_invalid_format(self):
        """Test changing admin email with invalid format"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        with pytest.raises(ValueError, match="Invalid email format"):
            aggregate.change_admin_email("testuser", "invalid-email")

    def test_change_admin_password_success(self):
        """Test changing admin password"""
        aggregate = AdminsAggregate()
        admin = aggregate.create_admin(1, "testuser", "test@example.com", "oldpassword", True)

        # Verify old password works
        assert admin.verify_password("oldpassword") == True

        aggregate.change_admin_password("testuser", "newpassword")

        # Verify new password works
        updated_admin = aggregate.require_admin_by_name("testuser")
        assert updated_admin.verify_password("newpassword") == True
        assert updated_admin.verify_password("oldpassword") == False
        assert aggregate.version == 2

    def test_change_admin_password_short(self):
        """Test changing admin password with short password"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

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

    def test_remove_admin_success(self):
        """Test removing existing admin"""
        aggregate = AdminsAggregate()
        aggregate.create_admin(1, "testuser", "test@example.com", "password123", True)

        assert aggregate.get_admin_count() == 1
        aggregate.remove_admin("testuser")
        assert aggregate.get_admin_count() == 0
        assert aggregate.version == 2
        assert not aggregate.admin_exists("testuser")

    def test_remove_admin_nonexistent(self):
        """Test removing non-existent admin raises error"""
        aggregate = AdminsAggregate()

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

    def test_validation_methods_static(self):
        """Test static validation methods"""
        # Valid cases
        assert AdminsAggregate._validate_name("testuser") == "testuser"
        assert AdminsAggregate._validate_name("  testuser  ") == "testuser"  # Trims whitespace
        assert AdminsAggregate._validate_email("test@example.com") == "test@example.com"
        assert AdminsAggregate._validate_password("password123") == "password123"

        # Invalid cases
        with pytest.raises(ValueError, match="Admin name cannot be empty"):
            AdminsAggregate._validate_name("")

        with pytest.raises(ValueError, match="Invalid email format"):
            AdminsAggregate._validate_email("invalid-email")

        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            AdminsAggregate._validate_password("short")
