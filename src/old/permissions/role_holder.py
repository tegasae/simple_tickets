# domain/permissions/role_holder.py
from typing import FrozenSet, TypeVar, Generic, Self
from dataclasses import dataclass, field, replace
from datetime import datetime

# Type variables for generics
PermissionType = TypeVar('PermissionType')
RoleRegistryType = TypeVar('RoleRegistryType')


@dataclass(frozen=True)
class RoleHolder(Generic[PermissionType, RoleRegistryType]):
    """Generic immutable role holder"""
    roles_ids: FrozenSet[int] = field(default_factory=frozenset)
    date_created: datetime = field(default_factory=datetime.now)
    @classmethod
    def create_empty(cls) ->Self:
        return cls(roles_ids=frozenset())

    @classmethod
    def from_ids(cls, role_ids: set[int]) ->Self:
        return cls(roles_ids=frozenset(role_ids))

    def has_role(self, role_id: int) -> bool:
        return role_id in self.roles_ids

    def add_role(self, role_id: int) -> Self:
        new_roles = set(self.roles_ids)
        new_roles.add(role_id)
        return replace(self, roles_ids=frozenset(new_roles))

    def remove_role(self, role_id: int) -> Self:
        new_roles = set(self.roles_ids)
        new_roles.discard(role_id)
        return replace(self, roles_ids=frozenset(new_roles))

    def has_permission(self, permission: PermissionType,
                       role_registry: RoleRegistryType) -> bool:
        """Type-safe permission check"""
        for role_id in self.roles_ids:
            # role_registry must have get_role_by_id method
            role = role_registry.get_role_by_id(role_id)  # type: ignore
            if role and role.has_permission(permission):  # type: ignore
                return True
        return False

    def is_empty(self) -> bool:
        return len(self.roles_ids) == 0

    def get_role_names(self, role_registry: RoleRegistryType) -> list[str]:
        """Get names of all user's roles"""
        return role_registry.get_role_names(self.roles_ids)

    def role_exists_by_name(self, role_name: str, role_registry:RoleRegistryType) -> bool:
        if role_name == self.get_role_names(role_registry):
                return True
        return False

# Type aliases for convenience
#UserRoleHolder = RoleHolder['PermissionUser', 'UserRoleRegistry']
#AdminRoleHolder = RoleHolder['Permission', 'RoleRegistry']  # Your existing Admin types