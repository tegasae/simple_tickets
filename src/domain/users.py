#users.py
from dataclasses import field, dataclass

from datetime import datetime
from typing import FrozenSet, Self

from src.domain.account import Account, NoAccount
from src.domain.permissions.role_registry import NewRoleRegistry
from src.domain.permissions.permission import PermissionBase
from src.domain.permissions.role_holder import RoleHolder
from src.domain.value_objects import Emails, Address, Phones, Name

@dataclass
class Employee:
    employee_id: int
    first_name: str
    last_name: str
    email: Emails
    phones: Phones
    date_created: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    version: int = 0
    _is_empty: bool = field(default=False, init=False, repr=False)
    is_deleted: bool = False

@dataclass(kw_only=True)
class User(Employee):
    user_id: int    # ✅ Public field
    account:Account|NoAccount
    client_id: int
    roles: set[int] = field(default_factory=set)
    _role_holder: RoleHolder = field(default_factory=RoleHolder.create_empty)

    def __post_init__(self):
        """Ensure role_holder is properly initialized"""
        if not hasattr(self, '_role_holder') or self._role_holder is None:
            object.__setattr__(self, '_role_holder', RoleHolder.create_empty())

#

    # ========== ROLE METHODS ==========

    def has_role(self, role_id: int) -> bool:
        """Check if user has specific role"""
        return self._role_holder.has_role(role_id)


    def get_roles(self) -> FrozenSet[int]:
        """Get all role IDs"""
        return self._role_holder.roles_ids

    def get_role_names(self, role_registry: NewRoleRegistry) -> list[str]:
        """Get names of all user's roles"""
        return self._role_holder.get_role_names(role_registry)

    def grant(self, role_id: int, role_registry: NewRoleRegistry) -> None:
        """Assign a role to user"""
        role = role_registry.require_role_by_id(role_id)
        object.__setattr__(
            self,
            '_role_holder',
            self._role_holder.add_role(role.role_id)
        )

    def revoke(self, role_id: int) -> None:
        """Remove a role from user"""
        object.__setattr__(
            self,
            '_role_holder',
            self._role_holder.remove_role(role_id)
        )

    # ========== PERMISSION METHODS ==========

    def has_permission(self, permission: PermissionBase,
                       role_registry: NewRoleRegistry) -> bool:
        """Check if user has permission"""
        # User must be active
        if not self.enabled:
            return False

        # Delegate to RoleHolder
        return self._role_holder.has_permission(permission, role_registry)


    # ========== BUSINESS METHODS ==========

    def disable(self) -> None:
        """Disable user account"""
        self.enabled = False

    def enable(self) -> None:
        """Enable user account"""
        self.enabled = True

    def update_email(self, new_email: str) -> None:
        """Update user email"""
        # Add validation if needed
        self.email = Emails(new_email)



    @classmethod
    def create_with_roles(cls, user_id: int, username: str, login: str, password: str, emails: str, phone: str,
                             address: str, client_id: int,
                          role_ids: set[int],enabled: bool = True,) -> Self:
        """Create user with specific roles"""
        role_holder = RoleHolder.from_ids(role_ids)

        return cls(
            user_id=user_id,
            name=Name(username),
            login=Name(login),
            password=password,
            client_id=client_id,
            emails=Emails(emails),
            enabled=enabled,
            phones=Phones(phone),
            address=Address(address),
            _role_holder=role_holder
        )
