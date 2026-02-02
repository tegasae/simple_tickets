from dataclasses import dataclass, field
from datetime import datetime
from typing import FrozenSet

from src.domain.permissions.permission import PermissionBase

#todo В дальнейшем хранить роли в базе.
@dataclass(frozen=True)
class Role:
    """Immutable role with permissions"""
    """Роль, включает в себя набор прав. Сейчас роли используются только для Admin. В дальнейшем у Client 
    тоже будет поведение и роли нужно будет предусмотреть для Client, но позже."""
    role_id: int
    name: str
    description: str = ""
    permissions: FrozenSet[PermissionBase] = field(default_factory=frozenset)
    is_system_role: bool = False  # Cannot be modified/deleted
    date_created: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: PermissionBase) -> bool:
        """Ииееет ли роль указанное разрешение"""
        return permission in self.permissions


@dataclass(frozen=True)
class EmptyRole(Role):
    """Immutable role with permissions"""
    """Пустая роль"""
    role_id: int=0
    name: str=""
    description: str = ""
    permissions =frozenset(),
    is_system_role: bool = False  # Cannot be modified/deleted
    date_created: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: PermissionBase) -> bool:
        return False
