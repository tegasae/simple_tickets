#src/domain/rbac/role_new.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generic, FrozenSet

from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.typevar import P


@dataclass(frozen=True)
class Role(Generic[P]):
    role_id: int                 # DB primary key
    name: str                    # human-readable (may change)
    permissions: FrozenSet[P] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 0
    def has_permission(self, permission: P) -> bool:
        return permission in self.permissions



class AdminRole(Role[AdminPermission]):
    """Role that can only contain admin permissions."""

    def __post_init__(self):
        # Validate at creation time
        for perm in self.permissions:
            if not isinstance(perm, AdminPermission):
                raise ValueError(f"AdminRole can only contain AdminPermissions, got {type(perm)}")


class UserRole(Role[UserPermission]):
    """Role that can only contain user permissions."""

    def __post_init__(self):
        for perm in self.permissions:
            if not isinstance(perm, UserPermission):
                raise ValueError(f"UserRole can only contain UserPermissions, got {type(perm)}")
