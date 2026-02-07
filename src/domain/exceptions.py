"""Domain Exceptions Module.

This module defines custom exception classes for domain-related errors
in the application. All exceptions inherit from DomainError for consistent
error handling and reporting.
"""

from typing import Optional


class DomainError(Exception):
    """Base exception class for all domain-related errors.

    This serves as a common base class for all custom domain exceptions,
    providing consistent structure and error reporting.

    Attributes:
        message: Detailed error message
        admin_name: Optional name of the admin/user related to the error
    """

    def __init__(self, message: str, admin_name: Optional[str] = None):
        """Initialize a DomainError.

        Args:
            message: Detailed error message describing what went wrong
            admin_name: Optional name of the admin or user associated
                       with the error
        """
        self.message = message
        self.admin_name = admin_name
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of the error.

        Returns:
            Formatted string with error message and admin name if available
        """
        if self.admin_name:
            return f"{self.admin_name}: {self.message}"
        return self.message


class ItemNotFoundError(DomainError):
    """Raised when a requested item cannot be found.

    This exception should be used when attempting to retrieve, update,
    or delete an item that doesn't exist in the system.

    Example:
        >>> raise ItemNotFoundError("user")
        ItemNotFoundError: The 'user' not found
    """

    def __init__(self, item_name: str):
        """Initialize an ItemNotFoundError.

        Args:
            item_name: Name or identifier of the item that was not found
        """
        super().__init__(f"The '{item_name}' not found", item_name)


class ItemAlreadyExistsError(DomainError):
    """Raised when attempting to create a duplicate item.

    This exception should be used when trying to create an item
    that already exists (e.g., duplicate username, email, or ID).

    Example:
        >>> raise ItemAlreadyExistsError("user@example.com")
        ItemAlreadyExistsError: The item 'user@example.com' already exists
    """

    def __init__(self, item_name: str):
        """Initialize an ItemAlreadyExistsError.

        Args:
            item_name: Name or identifier of the duplicate item
        """
        super().__init__(f"The item '{item_name}' already exists", item_name)


class ItemValidationError(DomainError):
    """Raised when item data validation fails.

    This exception should be used for validation errors such as
    invalid email format, password requirements not met, or
    other business rule violations.

    Example:
        >>> raise ItemValidationError("Email format is invalid")
        ItemValidationError: Validation error: Email format is invalid
    """

    def __init__(self, message: str, item_name: Optional[str] = None):
        """Initialize an ItemValidationError.

        Args:
            message: Detailed validation error message
            item_name: Optional name of the item that failed validation
        """
        super().__init__(f"Validation error: {message}", item_name)


class DomainOperationError(DomainError):
    """Raised when domain operations fail.

    This exception should be used for operation failures that
    are not related to validation or security, such as
    database operation failures, business logic errors, or
    other operational issues.

    Example:
        >>> raise DomainOperationError("Cannot delete active user")
        DomainOperationError: Operation failed: Cannot delete active user
    """

    def __init__(self, message: str, admin_name: Optional[str] = None):
        """Initialize a DomainOperationError.

        Args:
            message: Detailed operation failure message
            admin_name: Optional name of the admin/user attempting the operation
        """
        super().__init__(f"Operation failed: {message}", admin_name)


class DomainSecurityError(DomainError):
    """Raised for security-related domain issues.

    This exception should be used for security violations such as
    unauthorized access attempts, permission denials, or
    other security-related business rule violations.

    Example:
        >>> raise DomainSecurityError("Insufficient permissions")
        DomainSecurityError: Security error: Insufficient permissions
    """

    def __init__(self, message: str, admin_name: Optional[str] = None):
        """Initialize a DomainSecurityError.

        Args:
            message: Detailed security error message
            admin_name: Optional name of the admin/user related to the security issue
        """
        super().__init__(f"Security error: {message}", admin_name)


# Optional: Additional specific exceptions for common use cases

class AuthenticationError(DomainSecurityError):
    """Raised when authentication fails.

    This is a more specific version of DomainSecurityError for
    authentication-related failures.
    """

    def __init__(self, message: str = "Authentication failed", admin_name: Optional[str] = None):
        """Initialize an AuthenticationError.

        Args:
            message: Authentication failure message
            admin_name: Optional name of the user attempting authentication
        """
        super().__init__(message, admin_name)


class AuthorizationError(DomainSecurityError):
    """Raised when authorization fails (insufficient permissions).

    This is a more specific version of DomainSecurityError for
    authorization-related failures.
    """

    def __init__(self, message: str = "Insufficient permissions", admin_name: Optional[str] = None):
        """Initialize an AuthorizationError.

        Args:
            message: Authorization failure message
            admin_name: Optional name of the user with insufficient permissions
        """
        super().__init__(message, admin_name)


class ConcurrencyError(DomainOperationError):
    """Raised when concurrent modification is detected.

    This is useful for optimistic concurrency control scenarios.
    """

    def __init__(self, message: str = "Concurrent modification detected", admin_name: Optional[str] = None):
        """Initialize a ConcurrencyError.

        Args:
            message: Concurrency error message
            admin_name: Optional name of the user causing the conflict
        """
        super().__init__(message, admin_name)