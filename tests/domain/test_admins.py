import pytest
from datetime import datetime


from src.domain.exceptions import ItemNotFoundError, ItemAlreadyExistsError, ItemValidationError, DomainOperationError
from src.domain.model import (
    Admin, AdminsAggregate,
    EMPTY_ADMIN_ID, MIN_PASSWORD_LENGTH
)
from src.domain.admin_empty import AdminEmpty


class TestAdmin:
    """Tests for Admin entity"""

    @pytest.fixture
    def sample_admin(self):
        """Create a sample Admin instance for testing"""
        return Admin(
            admin_id=1,
            name="testadmin",
            password="securepassword123",
            email="test@example.com",
            enabled=True
        )

    def test_admin_creation(self):
        """Test Admin creation with valid data"""
        admin = Admin(
            admin_id=1,
            name="testadmin",
            password="securepassword123",
            email="test@example.com",
            enabled=True
        )

        assert admin.admin_id == 1
        assert admin.name == "testadmin"
        assert admin.email == "test@example.com"
        assert admin.enabled is True
        assert isinstance(admin.date_created, datetime)
        assert admin.is_empty() is False
        assert bool(admin) is True

    def test_admin_password_hashing(self, sample_admin):
        """Test that passwords are properly hashed"""
        # Password should be hashed, not stored in plain text
        assert sample_admin.password != "securepassword123"
        assert len(sample_admin.password) > 20  # bcrypt hashes are long

        # Should be able to verify the correct password
        assert sample_admin.verify_password("securepassword123") is True
        assert sample_admin.verify_password("wrongpassword") is False

    def test_admin_password_setter(self, sample_admin):
        """Test changing admin password"""
        original_hash = sample_admin.password
        sample_admin.password = "newpassword456"

        # Hash should change
        assert sample_admin.password != original_hash
        # New password should verify correctly
        assert sample_admin.verify_password("newpassword456") is True
        # Old password should no longer work
        assert sample_admin.verify_password("securepassword123") is False

    def test_admin_password_empty_validation(self, sample_admin):
        """Test that empty passwords are rejected"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            sample_admin.password = ""

    def test_admin_property_setters(self, sample_admin):
        """Test all property setters work correctly"""
        sample_admin.name = "newname"
        sample_admin.email = "new@example.com"
        sample_admin.enabled = False
        sample_admin.admin_id = 2

        assert sample_admin.name == "newname"
        assert sample_admin.email == "new@example.com"
        assert sample_admin.enabled is False
        assert sample_admin.admin_id == 2

    def test_admin_equality(self, sample_admin):
        """Test Admin equality comparison"""
        admin1 = Admin(1, "admin1", "pass1", "email1@test.com", True)
        admin2 = Admin(2, "admin2", "pass2", "email2@test.com", False)
        admin1_copy = Admin(1, "admin1", "pass1", "email1@test.com", True)
        empty_admin = AdminEmpty()

        assert admin1 == admin1_copy
        assert admin1 != admin2
        assert admin1 != empty_admin

    def test_admin_hash(self, sample_admin):
        """Test Admin hashing"""
        admin1 = Admin(1, "admin1", "pass1", "email1@test.com", True)
        admin2 = Admin(2, "admin2", "pass2", "email2@test.com", False)

        # Different admins should have different hashes
        assert hash(admin1) != hash(admin2)
        # Same name should produce same hash
        admin_same_name = Admin(3, "admin1", "pass3", "email3@test.com", True)
        assert hash(admin1) == hash(admin_same_name)

    def test_static_password_methods(self):
        """Test static password hashing and verification methods"""
        password = "testpassword123"
        hashed = Admin.str_hash(password)

        # Should be able to verify with static method
        assert Admin.str_verify(password, hashed) is True
        assert Admin.str_verify("wrongpassword", hashed) is False

        # Hash should be different each time (due to salt)
        hashed2 = Admin.str_hash(password)
        assert hashed != hashed2
        # But both should verify correctly
        assert Admin.str_verify(password, hashed2) is True


class TestAdminEmpty:
    """Tests for AdminEmpty null object"""

    @pytest.fixture
    def empty_admin(self):
        """Create an AdminEmpty instance"""
        return AdminEmpty()

    def test_admin_empty_creation(self, empty_admin):
        """Test AdminEmpty creation and default values"""
        assert empty_admin.admin_id == EMPTY_ADMIN_ID
        assert empty_admin.name == ""
        assert empty_admin.email == ""
        assert empty_admin.enabled is False
        assert empty_admin.is_empty() is True
        assert bool(empty_admin) is False

    def test_admin_empty_setters_raise_errors(self, empty_admin):
        """Test that AdminEmpty setters raise AttributeError"""
        with pytest.raises(AttributeError, match="Cannot set admin_id on empty admin"):
            empty_admin.admin_id = 1

        with pytest.raises(AttributeError, match="Cannot set name on empty admin"):
            empty_admin.name = "test"

        with pytest.raises(AttributeError, match="Cannot set email on empty admin"):
            empty_admin.email = "test@example.com"

        with pytest.raises(AttributeError, match="Cannot set enabled on empty admin"):
            empty_admin.enabled = True

    def test_admin_empty_password_access(self, empty_admin):
        """Test that password access raises errors on AdminEmpty"""
        with pytest.raises(DomainOperationError, match="Operation failed: Cannot access password on empty admin"):
            _ = empty_admin.password

        with pytest.raises(AttributeError, match="Cannot set password on empty admin"):
            empty_admin.password = "test"

    def test_admin_empty_verify_password(self, empty_admin):
        """Test that verify_password always returns False for AdminEmpty"""
        assert empty_admin.verify_password("anypassword") is False
        assert empty_admin.verify_password("") is False

    def test_admin_empty_equality(self, empty_admin):
        """Test AdminEmpty equality"""
        empty_admin2 = AdminEmpty()
        real_admin = Admin(1, "test", "pass", "test@example.com", True)

        assert empty_admin == empty_admin2
        assert empty_admin != real_admin

    def test_admin_empty_method_access(self, empty_admin):
        """Test that any method access raises AttributeError"""
        with pytest.raises(AttributeError, match="Cannot call 'some_method' on empty admin"):
            empty_admin.some_method()


class TestAdminsAggregate:
    """Tests for AdminsAggregate"""

    @pytest.fixture
    def empty_aggregate(self):
        """Create an empty AdminsAggregate"""
        return AdminsAggregate()

    @pytest.fixture
    def sample_admin(self):
        """Create a sample Admin"""
        return Admin(1, "admin1", "password123", "admin1@example.com", True)

    @pytest.fixture
    def populated_aggregate(self, sample_admin):
        """Create AdminsAggregate with some admins"""
        admin2 = Admin(2, "admin2", "password456", "admin2@example.com", False)
        return AdminsAggregate(admins=[sample_admin, admin2])

    def test_aggregate_creation_empty(self, empty_aggregate):
        """Test empty aggregate creation"""
        assert empty_aggregate.is_empty() is True
        assert empty_aggregate.get_admin_count() == 0
        assert empty_aggregate.version == 0
        assert len(empty_aggregate.admins) == 0

    def test_aggregate_creation_with_admins(self, populated_aggregate, sample_admin):
        """Test aggregate creation with initial admins"""
        assert populated_aggregate.is_empty() is False
        assert populated_aggregate.get_admin_count() == 2
        assert "admin1" in populated_aggregate.admins
        assert "admin2" in populated_aggregate.admins

    def test_create_admin_success(self, empty_aggregate):
        """Test successful admin creation"""
        admin = empty_aggregate.create_admin(
            admin_id=1,
            name="newadmin",
            email="new@example.com",
            password="validpassword123",
            enabled=True
        )

        assert admin.admin_id == 1
        assert admin.name == "newadmin"
        assert empty_aggregate.admin_exists("newadmin") is True
        assert empty_aggregate.get_admin_count() == 1
        assert empty_aggregate.version == 1

    def test_create_admin_duplicate_name(self, populated_aggregate):
        """Test admin creation with duplicate name"""
        with pytest.raises(ItemAlreadyExistsError, match="admin1"):
            populated_aggregate.create_admin(
                admin_id=3,
                name="admin1",  # Already exists
                email="new@example.com",
                password="password123",
                enabled=True
            )

    def test_create_admin_duplicate_id(self, populated_aggregate):
        """Test admin creation with duplicate ID"""
        with pytest.raises(ItemAlreadyExistsError, match="1"):
            populated_aggregate.create_admin(
                admin_id=1,  # Already exists
                name="newadmin",
                email="new@example.com",
                password="password123",
                enabled=True
            )

    def test_create_admin_validation_errors(self, empty_aggregate):
        """Test admin creation validation errors"""
        # Empty name
        with pytest.raises(ItemValidationError, match="Admin name cannot be empty"):
            empty_aggregate.create_admin(1, "", "test@example.com", "password123", True)

        # Invalid email
        with pytest.raises(ItemValidationError, match="Invalid email format"):
            empty_aggregate.create_admin(1, "test", "invalid-email", "password123", True)

        # Short password
        with pytest.raises(ItemValidationError, match=f"Password must be at least {MIN_PASSWORD_LENGTH} characters"):
            empty_aggregate.create_admin(1, "test", "test@example.com", "short", True)

    def test_add_admin_success(self, empty_aggregate, sample_admin):
        """Test adding existing admin"""
        empty_aggregate.add_admin(sample_admin)

        assert empty_aggregate.admin_exists("admin1") is True
        assert empty_aggregate.get_admin_count() == 1
        assert empty_aggregate.version == 0

    def test_add_admin_duplicate_name(self, populated_aggregate, sample_admin):
        """Test adding admin with duplicate name"""
        with pytest.raises(ItemAlreadyExistsError, match="admin1"):
            populated_aggregate.add_admin(sample_admin)  # Already exists

    def test_get_admin_by_name_found(self, populated_aggregate, sample_admin):
        """Test getting admin by name when found"""
        admin = populated_aggregate.get_admin_by_name("admin1")
        assert admin == sample_admin
        assert not admin.is_empty()

    def test_get_admin_by_name_not_found(self, populated_aggregate):
        """Test getting admin by name when not found"""
        admin = populated_aggregate.get_admin_by_name("nonexistent")
        assert admin.is_empty()
        assert isinstance(admin, AdminEmpty)

    def test_require_admin_by_name_found(self, populated_aggregate, sample_admin):
        """Test requiring admin by name when found"""
        admin = populated_aggregate.require_admin_by_name("admin1")
        assert admin == sample_admin

    def test_require_admin_by_name_not_found(self, populated_aggregate):
        """Test requiring admin by name when not found"""
        with pytest.raises(ItemNotFoundError, match="nonexistent"):
            populated_aggregate.require_admin_by_name("nonexistent")

    def test_admin_exists(self, populated_aggregate):
        """Test admin existence checking"""
        assert populated_aggregate.admin_exists("admin1") is True
        assert populated_aggregate.admin_exists("nonexistent") is False

    def test_change_admin_email_success(self, populated_aggregate):
        """Test successful email change"""
        version=populated_aggregate.version
        populated_aggregate.change_admin_email("admin1", "new@example.com")

        admin = populated_aggregate.require_admin_by_name("admin1")
        assert admin.email == "new@example.com"
        assert populated_aggregate.version == version+1  # Version should increment

    def test_change_admin_email_invalid(self, populated_aggregate):
        """Test email change with invalid email"""
        with pytest.raises(ItemValidationError, match="Invalid email format"):
            populated_aggregate.change_admin_email("admin1", "invalid-email")

    def test_change_admin_password_success(self, populated_aggregate):
        """Test successful password change"""
        version=populated_aggregate.version
        old_password_hash = populated_aggregate.get_admin_by_name("admin1").password
        populated_aggregate.change_admin_password("admin1", "newpassword456")

        admin = populated_aggregate.require_admin_by_name("admin1")
        assert admin.password != old_password_hash
        assert admin.verify_password("newpassword456") is True
        assert populated_aggregate.version == version+1

    def test_change_admin_password_short(self, populated_aggregate):
        """Test password change with short password"""
        with pytest.raises(ItemValidationError, match=f"Password must be at least {MIN_PASSWORD_LENGTH} characters"):
            populated_aggregate.change_admin_password("admin1", "short")

    def test_toggle_admin_status(self, populated_aggregate):
        """Test toggling admin status"""
        version=populated_aggregate.version
        initial_status = populated_aggregate.require_admin_by_name("admin1").enabled
        populated_aggregate.toggle_admin_status("admin1")

        admin = populated_aggregate.require_admin_by_name("admin1")
        assert admin.enabled != initial_status
        assert populated_aggregate.version == version+1

    def test_set_admin_status(self, populated_aggregate):
        """Test setting specific admin status"""
        version=populated_aggregate.version
        populated_aggregate.set_admin_status("admin1", False)
        assert populated_aggregate.require_admin_by_name("admin1").enabled is False

        populated_aggregate.set_admin_status("admin1", True)
        assert populated_aggregate.require_admin_by_name("admin1").enabled is True
        assert populated_aggregate.version == version+2  # Two changes

    def test_remove_admin_by_id_success(self, populated_aggregate):
        """Test successful admin removal by ID"""
        version=populated_aggregate.version
        populated_aggregate.remove_admin_by_id(1)

        assert populated_aggregate.admin_exists("admin1") is False
        assert populated_aggregate.get_admin_count() == 1
        assert populated_aggregate.version == version+1

    def test_remove_admin_by_id_not_found(self, populated_aggregate):
        """Test admin removal by ID when not found"""
        with pytest.raises(ItemNotFoundError, match="Admin 999 not found"):
            populated_aggregate.remove_admin_by_id(999)

    def test_get_admin_by_id_success(self, populated_aggregate, sample_admin):
        """Test getting admin by ID when found"""
        admin = populated_aggregate.get_admin_by_id(1)
        assert admin == sample_admin

    def test_get_admin_by_id_not_found(self, populated_aggregate):
        """Test getting admin by ID when not found"""
        with pytest.raises(ItemNotFoundError, match="Admin 999 not found"):
            populated_aggregate.get_admin_by_id(999)

    def test_get_all_admins(self, populated_aggregate):
        """Test getting all admins"""
        admins = populated_aggregate.get_all_admins()
        assert len(admins) == 2
        assert all(not admin.is_empty() for admin in admins)

    def test_get_enabled_admins(self, populated_aggregate):
        """Test getting enabled admins only"""
        enabled_admins = populated_aggregate.get_enabled_admins()
        assert len(enabled_admins) == 1
        assert all(admin.enabled for admin in enabled_admins)

    def test_get_disabled_admins(self, populated_aggregate):
        """Test getting disabled admins only"""
        disabled_admins = populated_aggregate.get_disabled_admins()
        assert len(disabled_admins) == 1
        assert all(not admin.enabled for admin in disabled_admins)

    def test_aggregate_version_increments(self, empty_aggregate):
        """Test that aggregate version increments on modifications"""
        assert empty_aggregate.version == 0

        # Create admin
        empty_aggregate.create_admin(1, "admin1", "admin1@example.com", "password123", True)
        assert empty_aggregate.version == 1

        # Change email
        empty_aggregate.change_admin_email("admin1", "new@example.com")
        assert empty_aggregate.version == 2

        # Toggle status
        empty_aggregate.toggle_admin_status("admin1")
        assert empty_aggregate.version == 3

        # Remove admin
        empty_aggregate.remove_admin_by_id(1)
        assert empty_aggregate.version == 4


class TestStaticValidationMethods:
    """Tests for static validation methods"""

    def test_validate_name_success(self):
        """Test successful name validation"""
        result = AdminsAggregate._validate_name(" validname ")
        assert result == "validname"  # Should be stripped

    def test_validate_name_empty(self):
        """Test empty name validation"""
        with pytest.raises(ItemValidationError, match="Admin name cannot be empty"):
            AdminsAggregate._validate_name("")
        with pytest.raises(ItemValidationError, match="Admin name cannot be empty"):
            AdminsAggregate._validate_name("   ")

    def test_validate_email_success(self):
        """Test successful email validation"""
        result = AdminsAggregate._validate_email("test@example.com")
        assert result == "test@example.com"

    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        invalid_emails = [
            "invalid",
            "invalid@",
            "@example.com",
            "invalid@example",
            "invalid@example."
        ]
        for email in invalid_emails:
            with pytest.raises(ItemValidationError, match="Invalid email format"):
                AdminsAggregate._validate_email(email)

    def test_validate_password_success(self):
        """Test successful password validation"""
        result = AdminsAggregate._validate_password("validpassword123")
        assert result == "validpassword123"

    def test_validate_password_short(self):
        """Test short password validation"""
        with pytest.raises(ItemValidationError, match=f"Password must be at least {MIN_PASSWORD_LENGTH} characters"):
            AdminsAggregate._validate_password("short")


# Test configuration
pytestmark = pytest.mark.unit


def test_imports():
    """Test that all required imports are available"""
    from src.domain.model import Admin, AdminEmpty, AdminsAggregate
    from src.domain.exceptions import ItemNotFoundError, ItemAlreadyExistsError, ItemValidationError

    assert Admin is not None
    assert AdminEmpty is not None
    assert AdminsAggregate is not None
    assert ItemNotFoundError is not None
    assert ItemAlreadyExistsError is not None
    assert ItemValidationError is not None