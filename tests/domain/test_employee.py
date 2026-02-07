"""Tests for Employee domain model with inheritance structure."""

import pytest
from datetime import datetime
from unittest.mock import patch

from src.domain.employee import Employee, Admin, User, NoAccount
from src.domain.value_objects import Name, Email, Phone
from src.domain.account import Account


class TestEmployee:
    """Tests for Employee base class."""

    def test_employee_creation(self):
        """Test creating an Employee instance."""
        first_name = Name("John")
        last_name = Name("Doe")
        email = Email("john@example.com")
        phone = Phone("+1234567890")
        account = Account.create(100, "john_doe", "ValidPass123!")

        employee = Employee(
            employee_id=1,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            account=account,
            enabled=True,
            version=0,
            is_deleted=False
        )

        assert employee.employee_id == 1
        assert employee.first_name == first_name
        assert employee.last_name == last_name
        assert employee.email == email
        assert employee.phone == phone
        assert employee.account == account
        assert employee.enabled is True
        assert employee.version == 0
        assert employee.is_deleted is False
        assert isinstance(employee.date_created, datetime)
        assert employee._role_ids == set()
        assert employee._is_empty is False

    def test_employee_with_minimal_fields(self):
        """Test creating Employee with minimal fields."""
        employee = Employee(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        assert employee.employee_id == 1
        assert employee.first_name is None
        assert employee.last_name is None
        assert employee.email is None
        assert employee.phone is None
        assert isinstance(employee.account, NoAccount)
        assert employee.enabled is True  # Default
        assert employee.version == 0  # Default
        assert employee.is_deleted is False  # Default
        assert employee._is_empty is False

    def test_create_empty_employee(self):
        """Test creating an empty employee."""
        empty_employee = Employee.create_empty()

        assert empty_employee.employee_id == 0
        assert empty_employee.first_name is None
        assert empty_employee.last_name is None
        assert empty_employee.email is None
        assert empty_employee.phone is None
        assert isinstance(empty_employee.account, NoAccount)
        assert empty_employee._is_empty is True

    def test_is_empty_method(self):
        """Test is_empty method."""
        # Empty employee
        empty_employee = Employee.create_empty()
        assert empty_employee.is_empty() is True

        # Regular employee
        regular_employee = Employee(
            employee_id=1,
            first_name=Name("John"),
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )
        assert regular_employee.is_empty() is False

    def test_role_ids_method(self):
        """Test role_ids method returns frozenset."""
        employee = Employee(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        # Initially empty
        assert employee.role_ids() == frozenset()

        # Add roles and check
        employee.grant_role(1)
        employee.grant_role(2)

        role_ids = employee.role_ids()
        assert isinstance(role_ids, frozenset)
        assert role_ids == frozenset({1, 2})

    def test_grant_role(self):
        """Test granting roles to employee."""
        employee = Employee(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        # Grant new role
        employee.grant_role(1)
        assert employee._role_ids == {1}

        # Grant another role
        employee.grant_role(2)
        assert employee._role_ids == {1, 2}

        # Grant existing role (should not duplicate)
        employee.grant_role(1)
        assert employee._role_ids == {1, 2}

    def test_revoke_role(self):
        """Test revoking roles from employee."""
        employee = Employee(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        # Add some roles
        employee.grant_role(1)
        employee.grant_role(2)
        employee.grant_role(3)
        assert employee._role_ids == {1, 2, 3}

        # Revoke existing role
        employee.revoke_role(2)
        assert employee._role_ids == {1, 3}

        # Revoke non-existent role (should not error)
        employee.revoke_role(99)
        assert employee._role_ids == {1, 3}

        # Revoke last role
        employee.revoke_role(1)
        employee.revoke_role(3)
        assert employee._role_ids == set()

    def test_employee_immutable_fields(self):
        """Test that dataclass fields work as expected."""
        employee = Employee(
            employee_id=1,
            first_name=Name("John"),
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        # Can modify mutable fields
        employee.enabled = False
        assert employee.enabled is False

        employee.version = 5
        assert employee.version == 5

        employee.is_deleted = True
        assert employee.is_deleted is True

    def test_employee_with_account_verification(self):
        """Test employee with real account can verify password."""
        account = Account.create(100, "john_doe", "ValidPass123!")
        employee = Employee(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=account
        )

        assert employee.account.verify_password("ValidPass123!") is True
        assert employee.account.verify_password("wrong") is False


    def test_employee_repr(self):
        """Test employee representation."""
        employee = Employee(
            employee_id=1,
            first_name=Name("John"),
            last_name=Name("Doe"),
            email=Email("john@example.com"),
            phone=None,
            account=NoAccount()
        )

        repr_str = repr(employee)
        assert "Employee(" in repr_str
        assert "employee_id=1" in repr_str
        assert "first_name=Name(value='John')" in repr_str or "first_name=Name" in repr_str
        assert "_is_empty" not in repr_str  # repr=False
        assert "_role_ids" not in repr_str  # repr=False


class TestAdmin:
    """Tests for Admin subclass."""

    def test_admin_creation(self):
        """Test creating an Admin instance."""
        admin = Admin(
            employee_id=1,
            first_name=Name("Jane"),
            last_name=Name("Smith"),
            email=Email("jane@company.com"),
            phone=Phone("+9876543210"),
            account=NoAccount(),
            job_title="System Administrator"
        )

        assert admin.employee_id == 1
        assert admin.first_name == Name("Jane")
        assert admin.last_name == Name("Smith")
        assert admin.email == Email("jane@company.com")
        assert admin.phone == Phone("+9876543210")
        assert isinstance(admin.account, NoAccount)
        assert admin.job_title == "System Administrator"

        # Inherited fields with defaults
        assert admin.enabled is True
        assert admin.version == 0
        assert admin.is_deleted is False

    def test_admin_with_default_job_title(self):
        """Test Admin with default job_title."""
        admin = Admin(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
            # job_title uses default=""
        )

        assert admin.job_title == ""

    def test_admin_inherits_employee_methods(self):
        """Test that Admin inherits all Employee methods."""
        admin = Admin(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        # Test inherited methods work
        assert admin.is_empty() is False

        admin.grant_role(1)
        assert admin.role_ids() == frozenset({1})

        admin.revoke_role(1)
        assert admin.role_ids() == frozenset()

    def test_admin_role_management(self):
        """Test Admin can have roles like Employee."""
        admin = Admin(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        admin.grant_role(100)  # Admin role
        admin.grant_role(200)  # Manager role

        assert admin.role_ids() == frozenset({100, 200})

    def test_admin_with_account(self):
        """Test Admin with real account."""
        account = Account.create(101, "admin_user", "AdminPass123!")
        admin = Admin(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=account,
            job_title="Lead Admin"
        )

        assert admin.account == account
        assert admin.account.verify_password("AdminPass123!") is True
        assert admin.job_title == "Lead Admin"

    def test_admin_repr(self):
        """Test Admin representation."""
        admin = Admin(
            employee_id=1,
            first_name=Name("Jane"),
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount(),
            job_title="Admin"
        )

        repr_str = repr(admin)
        assert "Admin(" in repr_str
        assert "employee_id=1" in repr_str
        assert "job_title='Admin'" in repr_str


class TestUser:
    """Tests for User subclass."""

    def test_user_creation(self):
        """Test creating a User instance."""
        # Note: User doesn't have @dataclass, so we need to handle initialization
        # Based on your code, User inherits from Employee and adds client_id
        # Since it's not a dataclass, we need to initialize properly

        # First, let's test what happens when we try to create a User
        # Since User doesn't override __init__, it should use Employee's __init__
        # But client_id needs to be handled

        # Actually, looking at your code:
        # class User(Employee):
        #     client_id: int
        # This creates a dataclass that inherits from Employee dataclass
        # So client_id should be a required field

        user = User(
            employee_id=2,
            first_name=Name("Bob"),
            last_name=Name("Wilson"),
            email=Email("bob@client.com"),
            phone=None,
            account=NoAccount(),
            client_id=100
        )

        assert user.employee_id == 2
        assert user.first_name == Name("Bob")
        assert user.last_name == Name("Wilson")
        assert user.email == Email("bob@client.com")
        assert user.phone is None
        assert isinstance(user.account, NoAccount)
        assert user.client_id == 100

        # Inherited defaults
        assert user.enabled is True
        assert user.version == 0
        assert user.is_deleted is False

    def test_user_inherits_employee_methods(self):
        """Test that User inherits all Employee methods."""
        user = User(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount(),
            client_id=100
        )

        # Test inherited methods work
        assert user.is_empty() is False

        user.grant_role(50)  # User role
        assert user.role_ids() == frozenset({50})

        user.revoke_role(50)
        assert user.role_ids() == frozenset()

    def test_user_role_management(self):
        """Test User can have roles like Employee."""
        user = User(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount(),
            client_id=100
        )

        user.grant_role(10)  # Basic user role
        user.grant_role(20)  # Client-specific role

        assert user.role_ids() == frozenset({10, 20})

    def test_user_with_account(self):
        """Test User with real account."""
        account = Account.create(102, "bob_wilson", "UserPass123!")
        user = User(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=account,
            client_id=200
        )

        assert user.account == account
        assert user.account.verify_password("UserPass123!") is True
        assert user.client_id == 200

    def test_user_repr(self):
        """Test User representation (inherited from Employee)."""
        user = User(
            employee_id=1,
            first_name=Name("Bob"),
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount(),
            client_id=300
        )

        repr_str = repr(user)
        # Since User inherits from Employee dataclass, it should show all fields
        assert "User(" in repr_str or "Employee(" in repr_str
        assert "employee_id=1" in repr_str
        assert "client_id=300" in repr_str


class TestInheritanceRelationships:
    """Tests for inheritance relationships and type checking."""

    def test_admin_is_employee(self):
        """Test that Admin is an instance of Employee."""
        admin = Admin(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        assert isinstance(admin, Employee)
        assert isinstance(admin, Admin)
        assert not isinstance(admin, User)

    def test_user_is_employee(self):
        """Test that User is an instance of Employee."""
        user = User(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount(),
            client_id=100
        )

        assert isinstance(user, Employee)
        assert isinstance(user, User)
        assert not isinstance(user, Admin)

    def test_type_hierarchy(self):
        """Test the type hierarchy."""
        admin = Admin(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        user = User(
            employee_id=2,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount(),
            client_id=100
        )

        employee = Employee(
            employee_id=3,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        # All are Employees
        employees = [admin, user, employee]
        for emp in employees:
            assert isinstance(emp, Employee)

        # Specific types
        assert type(admin) == Admin
        assert type(user) == User
        assert type(employee) == Employee

    def test_empty_employee_type(self):
        """Test create_empty returns Employee type."""
        empty = Employee.create_empty()

        assert isinstance(empty, Employee)
        assert type(empty) == Employee
        assert not isinstance(empty, Admin)
        assert not isinstance(empty, User)
        assert empty.is_empty() is True


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_employee_with_all_none(self):
        """Test Employee with all optional fields as None."""
        employee = Employee(
            employee_id=999,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount(),
            enabled=False,
            version=5,
            is_deleted=True
        )

        assert employee.employee_id == 999
        assert employee.first_name is None
        assert employee.last_name is None
        assert employee.email is None
        assert employee.phone is None
        assert isinstance(employee.account, NoAccount)
        assert employee.enabled is False
        assert employee.version == 5
        assert employee.is_deleted is True
        assert employee._is_empty is False

    def test_role_ids_immutability(self):
        """Test that role_ids() returns immutable frozenset."""
        employee = Employee(
            employee_id=1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        employee.grant_role(1)
        employee.grant_role(2)

        roles = employee.role_ids()
        assert isinstance(roles, frozenset)

        # Should not be able to modify the returned frozenset
        with pytest.raises(AttributeError):
            roles.add(3)  # frozenset is immutable

        # Modifying internal set shouldn't affect returned frozenset
        employee.grant_role(3)
        # roles is a snapshot, so it shouldn't have 3
        assert roles == frozenset({1, 2})
        # New call should have 3
        assert employee.role_ids() == frozenset({1, 2, 3})

    def test_negative_employee_id(self):
        """Test Employee with negative ID."""
        employee = Employee(
            employee_id=-1,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        assert employee.employee_id == -1

    def test_zero_employee_id(self):
        """Test Employee with ID 0."""
        employee = Employee(
            employee_id=0,
            first_name=None,
            last_name=None,
            email=None,
            phone=None,
            account=NoAccount()
        )

        assert employee.employee_id == 0
        # This is different from create_empty() which also sets _is_empty=True
        assert employee.is_empty() is False


def test_dataclass_features():
    """Test dataclass-specific features."""
    # Test that dataclass generates __eq__ method
    emp1 = Employee(
        employee_id=1,
        first_name=Name("John"),
        last_name=None,
        email=None,
        phone=None,
        account=NoAccount()
    )

    emp2 = Employee(
        employee_id=1,
        first_name=Name("John"),
        last_name=None,
        email=None,
        phone=None,
        account=NoAccount()
    )

    emp3 = Employee(
        employee_id=2,
        first_name=Name("John"),
        last_name=None,
        email=None,
        phone=None,
        account=NoAccount()
    )

    # Same ID and field values should be equal
    assert emp1 == emp2
    assert emp1 != emp3

    # Test Admin equality
    admin1 = Admin(
        employee_id=1,
        first_name=None,
        last_name=None,
        email=None,
        phone=None,
        account=NoAccount(),
        job_title="Admin"
    )

    admin2 = Admin(
        employee_id=1,
        first_name=None,
        last_name=None,
        email=None,
        phone=None,
        account=NoAccount(),
        job_title="Admin"
    )

    admin3 = Admin(
        employee_id=1,
        first_name=None,
        last_name=None,
        email=None,
        phone=None,
        account=NoAccount(),
        job_title="Different"
    )

    assert admin1 == admin2



