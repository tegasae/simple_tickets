# exceptions.py
from typing import Optional


class DomainError(Exception):
    """Base exception for all admin-related errors"""

    def __init__(self, message: str, admin_name: Optional[str] = None):
        self.message = message
        self.admin_name = admin_name
        super().__init__(self.message)


class ItemNotFoundError(DomainError):
    """Raised when an item is not found"""

    def __init__(self, item_name: str):
        super().__init__(f"The '{item_name}' not found", item_name)


class ItemAlreadyExistsError(DomainError):
    """Raised when trying to create a duplicate item"""

    def __init__(self, item_name: str):
        super().__init__(f"The item '{item_name}' already exists", item_name)


class ItemValidationError(DomainError):
    """Raised when item data validation fails"""

    def __init__(self, message: str, item_name: Optional[str] = None):
        super().__init__(f"Validation error: {message}", item_name)


class DomainOperationError(DomainError):
    """Raised when admin operations fail"""

    def __init__(self, message: str, admin_name: Optional[str] = None):
        super().__init__(f"Operation failed: {message}", admin_name)


class DomainSecurityError(DomainError):
    """Raised for security-related admin issues"""

    def __init__(self, message: str, admin_name: Optional[str] = None):
        super().__init__(f"Security error: {message}", admin_name)
