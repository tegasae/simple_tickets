# exceptions.py
from typing import Optional


class AdminError(Exception):
    """Base exception for all admin-related errors"""

    def __init__(self, message: str, admin_name: Optional[str] = None):
        self.message = message
        self.admin_name = admin_name
        super().__init__(self.message)


class AdminNotFoundError(AdminError):
    """Raised when an admin is not found"""

    def __init__(self, admin_name: str):
        super().__init__(f"Admin '{admin_name}' not found", admin_name)


class AdminAlreadyExistsError(AdminError):
    """Raised when trying to create a duplicate admin"""

    def __init__(self, admin_name: str):
        super().__init__(f"Admin '{admin_name}' already exists", admin_name)


class AdminValidationError(AdminError):
    """Raised when admin data validation fails"""

    def __init__(self, message: str, admin_name: Optional[str] = None):
        super().__init__(f"Validation error: {message}", admin_name)


class AdminOperationError(AdminError):
    """Raised when admin operations fail"""

    def __init__(self, message: str, admin_name: Optional[str] = None):
        super().__init__(f"Operation failed: {message}", admin_name)


class AdminSecurityError(AdminError):
    """Raised for security-related admin issues"""

    def __init__(self, message: str, admin_name: Optional[str] = None):
        super().__init__(f"Security error: {message}", admin_name)
