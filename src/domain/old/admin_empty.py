from dataclasses import dataclass, field
from datetime import datetime

from src.domain.exceptions import DomainOperationError
from src.domain.model import Admin, EMPTY_ADMIN_ID
from src.domain.permissions.rbac import Permission, RoleRegistry


@dataclass
class AdminEmpty(Admin):
    """Null Object implementation of AdminAbstract"""


    _admin_id: int = EMPTY_ADMIN_ID
    _name: str = ""
    _email: str = ""
    _enabled: bool = False
    _date_created: datetime = field(default_factory=datetime.now)

    # Property implementations with setters that raise errors
    @property
    def admin_id(self) -> int:
        return self._admin_id

    def has_permission(self, permission: Permission, role_registry: RoleRegistry) -> bool:
        return False

    @admin_id.setter
    def admin_id(self, value: int):
        raise AttributeError("Cannot set admin_id on empty admin")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        raise AttributeError("Cannot set name on empty admin")

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        raise AttributeError("Cannot set email on empty admin")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        raise AttributeError("Cannot set enabled on empty admin")

    @property
    def date_created(self) -> datetime:
        return self._date_created

    def __eq__(self, other) -> bool:
        return isinstance(other, AdminEmpty)

    def __bool__(self) -> bool:
        return False

    def is_empty(self) -> bool:
        return True

    def verify_password(self, password: str) -> bool:
        return False

    def assign_role(self, role_id: int, role_registry: RoleRegistry) -> None:
        pass


    def remove_role(self, role_id: int) -> None:
        pass

    @property
    def password(self):
        raise DomainOperationError(message="Cannot access password on empty admin")

    @password.setter
    def password(self, plain_password: str):
        raise AttributeError("Cannot set password on empty admin")

    def get_roles(self) -> set[int]:
        pass

    def __getattr__(self, name):
        """Catch any other method calls and raise appropriate error"""
        raise AttributeError(f"Cannot call '{name}' on empty admin")
