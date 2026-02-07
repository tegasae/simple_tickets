"""Tests for Domain Exceptions Module."""

import pytest
from src.domain.exceptions import (
    DomainError,
    ItemNotFoundError,
    ItemAlreadyExistsError,
    ItemValidationError,
    DomainOperationError,
    DomainSecurityError,
    AuthenticationError,
    AuthorizationError,
    ConcurrencyError
)


class TestDomainError:
    """Tests for base DomainError class."""

    def test_domain_error_basic(self):
        """Test basic DomainError creation."""
        error = DomainError("Test error message")

        assert error.message == "Test error message"
        assert error.admin_name is None
        assert str(error) == "Test error message"

    def test_domain_error_with_admin_name(self):
        """Test DomainError with admin_name."""
        error = DomainError("Test error", "admin123")

        assert error.message == "Test error"
        assert error.admin_name == "admin123"
        assert str(error) == "admin123: Test error"

    def test_domain_error_inheritance(self):
        """Test that DomainError is a proper Exception subclass."""
        error = DomainError("Test")

        assert isinstance(error, Exception)
        assert isinstance(error, DomainError)
        assert issubclass(DomainError, Exception)

    def test_domain_error_equality(self):
        """Test DomainError equality (based on message and admin_name)."""
        error1 = DomainError("Error", "admin1")
        error2 = DomainError("Error", "admin1")
        error3 = DomainError("Different", "admin1")
        error4 = DomainError("Error", "admin2")

        # Different instances with same values are not equal
        # (Exception doesn't implement __eq__ by default)
        assert error1 != error2
        assert error1 != error3
        assert error1 != error4

    def test_domain_error_attributes(self):
        """Test that DomainError has expected attributes."""
        error = DomainError("Message", "Admin")

        assert hasattr(error, 'message')
        assert hasattr(error, 'admin_name')
        assert error.message == "Message"
        assert error.admin_name == "Admin"


class TestItemNotFoundError:
    """Tests for ItemNotFoundError class."""

    def test_item_not_found_error_basic(self):
        """Test basic ItemNotFoundError creation."""
        error = ItemNotFoundError("user")

        assert error.message == "The 'user' not found"
        assert error.admin_name == "user"
        assert str(error) == "user: The 'user' not found"

    def test_item_not_found_error_with_spaces(self):
        """Test ItemNotFoundError with item name containing spaces."""
        error = ItemNotFoundError("user profile")

        assert error.message == "The 'user profile' not found"
        assert error.admin_name == "user profile"

    def test_item_not_found_error_special_characters(self):
        """Test ItemNotFoundError with special characters in item name."""
        error = ItemNotFoundError("user@example.com")

        assert error.message == "The 'user@example.com' not found"
        assert error.admin_name == "user@example.com"

    def test_item_not_found_error_inheritance(self):
        """Test that ItemNotFoundError inherits from DomainError."""
        error = ItemNotFoundError("item")

        assert isinstance(error, DomainError)
        assert isinstance(error, ItemNotFoundError)
        assert issubclass(ItemNotFoundError, DomainError)

    def test_item_not_found_error_usage_example(self):
        """Test typical usage scenario for ItemNotFoundError."""

        def find_user(user_id: int):
            if user_id == 999:  # Simulating not found
                raise ItemNotFoundError(f"user with ID {user_id}")
            return {"id": user_id, "name": "John"}

        # User exists
        user = find_user(123)
        assert user["id"] == 123

        # User not found
        with pytest.raises(ItemNotFoundError) as exc_info:
            find_user(999)

        assert exc_info.value.admin_name == "user with ID 999"
        assert "user with ID 999" in str(exc_info.value)


class TestItemAlreadyExistsError:
    """Tests for ItemAlreadyExistsError class."""

    def test_item_already_exists_error_basic(self):
        """Test basic ItemAlreadyExistsError creation."""
        error = ItemAlreadyExistsError("user@example.com")

        assert error.message == "The item 'user@example.com' already exists"
        assert error.admin_name == "user@example.com"
        assert str(error) == "user@example.com: The item 'user@example.com' already exists"

    def test_item_already_exists_error_different_item_types(self):
        """Test ItemAlreadyExistsError with different item types."""
        # Test with email
        email_error = ItemAlreadyExistsError("test@example.com")
        assert "test@example.com" in email_error.message

        # Test with username
        user_error = ItemAlreadyExistsError("john_doe")
        assert "john_doe" in user_error.message

        # Test with numeric ID
        id_error = ItemAlreadyExistsError("user_123")
        assert "user_123" in id_error.message

    def test_item_already_exists_error_inheritance(self):
        """Test that ItemAlreadyExistsError inherits from DomainError."""
        error = ItemAlreadyExistsError("item")

        assert isinstance(error, DomainError)
        assert isinstance(error, ItemAlreadyExistsError)
        assert issubclass(ItemAlreadyExistsError, DomainError)

    def test_item_already_exists_error_usage_example(self):
        """Test typical usage scenario for ItemAlreadyExistsError."""

        def create_user(email: str, username: str):
            # Simulating duplicate check
            existing_emails = {"john@example.com", "jane@example.com"}
            existing_usernames = {"john_doe", "jane_smith"}

            if email in existing_emails:
                raise ItemAlreadyExistsError(f"email '{email}'")
            if username in existing_usernames:
                raise ItemAlreadyExistsError(f"username '{username}'")

            return {"email": email, "username": username}

        # Create new user (success)
        user = create_user("new@example.com", "new_user")
        assert user["email"] == "new@example.com"

        # Try duplicate email
        with pytest.raises(ItemAlreadyExistsError) as exc_info:
            create_user("john@example.com", "different_user")

        assert "email 'john@example.com'" in str(exc_info.value)

        # Try duplicate username
        with pytest.raises(ItemAlreadyExistsError) as exc_info:
            create_user("different@example.com", "john_doe")

        assert "username 'john_doe'" in str(exc_info.value)


class TestItemValidationError:
    """Tests for ItemValidationError class."""

    def test_item_validation_error_basic(self):
        """Test basic ItemValidationError creation."""
        error = ItemValidationError("Email format is invalid")

        assert error.message == "Validation error: Email format is invalid"
        assert error.admin_name is None
        assert str(error) == "Validation error: Email format is invalid"

    def test_item_validation_error_with_item_name(self):
        """Test ItemValidationError with item_name parameter."""
        error = ItemValidationError("Password must be at least 8 characters", "user_password")

        assert error.message == "Validation error: Password must be at least 8 characters"
        assert error.admin_name == "user_password"
        assert str(error) == "user_password: Validation error: Password must be at least 8 characters"

    def test_item_validation_error_different_validation_types(self):
        """Test ItemValidationError with different validation messages."""
        # Email validation
        email_error = ItemValidationError("Invalid email format", "user_email")
        assert "Validation error: Invalid email format" in email_error.message

        # Password validation
        password_error = ItemValidationError("Password too weak", "user_password")
        assert "Validation error: Password too weak" in password_error.message

        # Business rule validation
        business_error = ItemValidationError("Minimum age requirement not met", "user_profile")
        assert "Validation error: Minimum age requirement not met" in business_error.message

    def test_item_validation_error_inheritance(self):
        """Test that ItemValidationError inherits from DomainError."""
        error = ItemValidationError("Test")

        assert isinstance(error, DomainError)
        assert isinstance(error, ItemValidationError)
        assert issubclass(ItemValidationError, DomainError)

    def test_item_validation_error_usage_example(self):
        """Test typical usage scenario for ItemValidationError."""

        def validate_user_data(email: str, age: int):
            if "@" not in email:
                raise ItemValidationError("Email must contain '@' symbol", "email")
            if age < 18:
                raise ItemValidationError("User must be at least 18 years old", "age")
            return True

        # Valid data
        assert validate_user_data("user@example.com", 25) is True

        # Invalid email
        with pytest.raises(ItemValidationError) as exc_info:
            validate_user_data("invalid-email", 25)

        assert "email" == exc_info.value.admin_name
        assert "Email must contain '@' symbol" in str(exc_info.value)

        # Invalid age
        with pytest.raises(ItemValidationError) as exc_info:
            validate_user_data("user@example.com", 16)

        assert "age" == exc_info.value.admin_name
        assert "User must be at least 18 years old" in str(exc_info.value)


class TestDomainOperationError:
    """Tests for DomainOperationError class."""

    def test_domain_operation_error_basic(self):
        """Test basic DomainOperationError creation."""
        error = DomainOperationError("Cannot delete active user")

        assert error.message == "Operation failed: Cannot delete active user"
        assert error.admin_name is None
        assert str(error) == "Operation failed: Cannot delete active user"

    def test_domain_operation_error_with_admin_name(self):
        """Test DomainOperationError with admin_name."""
        error = DomainOperationError("Database connection failed", "admin_john")

        assert error.message == "Operation failed: Database connection failed"
        assert error.admin_name == "admin_john"
        assert str(error) == "admin_john: Operation failed: Database connection failed"

    def test_domain_operation_error_different_operations(self):
        """Test DomainOperationError for different operation types."""
        # Database operation
        db_error = DomainOperationError("Transaction rollback failed")
        assert "Operation failed: Transaction rollback failed" in db_error.message

        # File operation
        file_error = DomainOperationError("File upload failed", "upload_service")
        assert "Operation failed: File upload failed" in file_error.message

        # Business operation
        business_error = DomainOperationError("Cannot process order with zero items", "order_system")
        assert "Operation failed: Cannot process order with zero items" in business_error.message

    def test_domain_operation_error_inheritance(self):
        """Test that DomainOperationError inherits from DomainError."""
        error = DomainOperationError("Test")

        assert isinstance(error, DomainError)
        assert isinstance(error, DomainOperationError)
        assert issubclass(DomainOperationError, DomainError)

    def test_domain_operation_error_usage_example(self):
        """Test typical usage scenario for DomainOperationError."""

        def process_order(order_id: int, user_id: int):
            # Simulating business logic failure
            if order_id <= 0:
                raise DomainOperationError(f"Invalid order ID: {order_id}", f"user_{user_id}")

            # Simulating database operation failure
            if order_id == 999:
                raise DomainOperationError("Database timeout while processing order", "order_processor")

            return {"order_id": order_id, "status": "processed"}

        # Successful operation
        result = process_order(123, 456)
        assert result["order_id"] == 123

        # Business logic failure
        with pytest.raises(DomainOperationError) as exc_info:
            process_order(0, 456)

        assert "user_456" == exc_info.value.admin_name
        assert "Invalid order ID: 0" in str(exc_info.value)

        # Technical operation failure
        with pytest.raises(DomainOperationError) as exc_info:
            process_order(999, 456)

        assert "order_processor" == exc_info.value.admin_name
        assert "Database timeout" in str(exc_info.value)


class TestDomainSecurityError:
    """Tests for DomainSecurityError class."""

    def test_domain_security_error_basic(self):
        """Test basic DomainSecurityError creation."""
        error = DomainSecurityError("Unauthorized access attempt")

        assert error.message == "Security error: Unauthorized access attempt"
        assert error.admin_name is None
        assert str(error) == "Security error: Unauthorized access attempt"

    def test_domain_security_error_with_admin_name(self):
        """Test DomainSecurityError with admin_name."""
        error = DomainSecurityError("Too many failed login attempts", "user123")

        assert error.message == "Security error: Too many failed login attempts"
        assert error.admin_name == "user123"
        assert str(error) == "user123: Security error: Too many failed login attempts"

    def test_domain_security_error_different_security_issues(self):
        """Test DomainSecurityError for different security scenarios."""
        # Authentication
        auth_error = DomainSecurityError("Invalid credentials")
        assert "Security error: Invalid credentials" in auth_error.message

        # Authorization
        authz_error = DomainSecurityError("Insufficient permissions", "guest_user")
        assert "Security error: Insufficient permissions" in authz_error.message

        # Rate limiting
        rate_error = DomainSecurityError("Too many requests", "api_client_123")
        assert "Security error: Too many requests" in rate_error.message

    def test_domain_security_error_inheritance(self):
        """Test that DomainSecurityError inherits from DomainError."""
        error = DomainSecurityError("Test")

        assert isinstance(error, DomainError)
        assert isinstance(error, DomainSecurityError)
        assert issubclass(DomainSecurityError, DomainError)

    def test_domain_security_error_usage_example(self):
        """Test typical usage scenario for DomainSecurityError."""

        def access_resource(user_role: str, resource: str):
            # Simulating authorization check
            if user_role == "guest" and resource == "admin_panel":
                raise DomainSecurityError("Access denied to admin panel", f"role_{user_role}")

            # Simulating rate limiting
            if resource == "api_data" and user_role == "free_user":
                raise DomainSecurityError("API rate limit exceeded", f"user_{user_role}")

            return {"resource": resource, "access": "granted"}

        # Authorized access
        result = access_resource("admin", "admin_panel")
        assert result["access"] == "granted"

        # Unauthorized access
        with pytest.raises(DomainSecurityError) as exc_info:
            access_resource("guest", "admin_panel")

        assert "role_guest" == exc_info.value.admin_name
        assert "Access denied to admin panel" in str(exc_info.value)

        # Rate limited access
        with pytest.raises(DomainSecurityError) as exc_info:
            access_resource("free_user", "api_data")

        assert "user_free_user" == exc_info.value.admin_name
        assert "API rate limit exceeded" in str(exc_info.value)


class TestSpecificSecurityErrors:
    """Tests for specific security error classes (AuthenticationError, AuthorizationError)."""

    def test_authentication_error_basic(self):
        """Test basic AuthenticationError creation."""
        error = AuthenticationError()

        assert error.message == "Security error: Authentication failed"
        assert error.admin_name is None
        assert str(error) == "Security error: Authentication failed"

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message."""
        error = AuthenticationError("Invalid username or password", "john_doe")

        assert error.message == "Security error: Invalid username or password"
        assert error.admin_name == "john_doe"
        assert str(error) == "john_doe: Security error: Invalid username or password"

    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError inherits from DomainSecurityError."""
        error = AuthenticationError()

        assert isinstance(error, DomainSecurityError)
        assert isinstance(error, AuthenticationError)
        assert issubclass(AuthenticationError, DomainSecurityError)

    def test_authorization_error_basic(self):
        """Test basic AuthorizationError creation."""
        error = AuthorizationError()

        assert error.message == "Security error: Insufficient permissions"
        assert error.admin_name is None
        assert str(error) == "Security error: Insufficient permissions"

    def test_authorization_error_custom_message(self):
        """Test AuthorizationError with custom message."""
        error = AuthorizationError("Cannot delete other users' data", "user123")

        assert error.message == "Security error: Cannot delete other users' data"
        assert error.admin_name == "user123"
        assert str(error) == "user123: Security error: Cannot delete other users' data"

    def test_authorization_error_inheritance(self):
        """Test that AuthorizationError inherits from DomainSecurityError."""
        error = AuthorizationError()

        assert isinstance(error, DomainSecurityError)
        assert isinstance(error, AuthorizationError)
        assert issubclass(AuthorizationError, DomainSecurityError)


class TestConcurrencyError:
    """Tests for ConcurrencyError class."""



    def test_concurrency_error_inheritance(self):
        """Test that ConcurrencyError inherits from DomainOperationError."""
        error = ConcurrencyError()

        assert isinstance(error, DomainOperationError)
        assert isinstance(error, ConcurrencyError)
        assert issubclass(ConcurrencyError, DomainOperationError)

    def test_concurrency_error_usage_example(self):
        """Test typical usage scenario for ConcurrencyError."""

        def update_user_profile(user_id: int, current_version: int, new_data: dict):
            # Simulating version check
            stored_version = 5  # Current version in database

            if current_version != stored_version:
                raise ConcurrencyError(
                    f"User profile was modified (expected version {current_version}, "
                    f"found version {stored_version})",
                    f"user_{user_id}"
                )

            return {"user_id": user_id, "version": stored_version + 1}

        # Successful update (versions match)
        result = update_user_profile(123, 5, {"name": "John"})
        assert result["version"] == 6

        # Concurrent modification (versions don't match)
        with pytest.raises(ConcurrencyError) as exc_info:
            update_user_profile(123, 4, {"name": "John"})

        assert "user_123" == exc_info.value.admin_name
        assert "User profile was modified" in str(exc_info.value)
        assert "expected version 4" in str(exc_info.value)
        assert "found version 5" in str(exc_info.value)


class TestExceptionHierarchy:
    """Tests for exception class hierarchy and relationships."""

    def test_exception_hierarchy(self):
        """Test the complete exception hierarchy."""
        # Create instances of each exception type
        domain_error = DomainError("Base error")
        not_found_error = ItemNotFoundError("item")
        exists_error = ItemAlreadyExistsError("item")
        validation_error = ItemValidationError("Invalid")
        operation_error = DomainOperationError("Failed")
        security_error = DomainSecurityError("Security issue")
        auth_error = AuthenticationError()
        authz_error = AuthorizationError()
        concurrency_error = ConcurrencyError()

        # Check DomainError is base for all
        errors = [
            not_found_error,
            exists_error,
            validation_error,
            operation_error,
            security_error,
            auth_error,
            authz_error,
            concurrency_error
        ]

        for error in errors:
            assert isinstance(error, DomainError)
            assert isinstance(error, Exception)

        # Check specific inheritance chains
        assert isinstance(auth_error, DomainSecurityError)
        assert isinstance(authz_error, DomainSecurityError)
        assert isinstance(concurrency_error, DomainOperationError)

    def test_exception_catching(self):
        """Test exception catching with different specificity levels."""
        # Test catching specific exception
        try:
            raise ItemNotFoundError("user")
        except ItemNotFoundError as e:
            assert e.admin_name == "user"

        # Test catching parent exception
        try:
            raise ItemValidationError("Invalid email", "email_field")
        except DomainError as e:
            assert "Validation error" in e.message

        # Test catching general Exception
        try:
            raise DomainOperationError("Operation failed", "admin")
        except Exception as e:
            assert isinstance(e, DomainError)
            assert e.admin_name == "admin"


class TestExceptionMessageFormatting:
    """Tests for exception message formatting and edge cases."""

    def test_empty_messages(self):
        """Test exceptions with empty or whitespace messages."""
        # Empty message
        error = DomainError("")
        assert error.message == ""

        # Whitespace message
        error = DomainError("   ")
        assert error.message == "   "

    def test_long_messages(self):
        """Test exceptions with very long messages."""
        long_message = "A" * 1000
        error = DomainError(long_message, "admin")

        assert len(error.message) == 1000
        assert error.admin_name == "admin"

    def test_special_characters_in_names(self):
        """Test exceptions with special characters in admin_name."""
        # Special characters
        error = DomainError("Error", "admin@company.com")
        assert error.admin_name == "admin@company.com"

        # Unicode characters
        error = DomainError("Error", "admin_名字")
        assert error.admin_name == "admin_名字"

        # Spaces
        error = DomainError("Error", "admin user")
        assert error.admin_name == "admin user"

    def test_none_admin_name_string_representation(self):
        """Test string representation when admin_name is None."""
        error = DomainError("Test message")
        assert str(error) == "Test message"

        # Ensure it doesn't add "None: " prefix
        assert not str(error).startswith("None")

    def test_exception_chaining(self):
        """Test that exceptions can be chained properly."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as original:
                raise ItemValidationError("Validation failed") from original
        except ItemValidationError as wrapper:
            assert wrapper.__cause__ is not None
            assert isinstance(wrapper.__cause__, ValueError)
            assert str(wrapper.__cause__) == "Original error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])