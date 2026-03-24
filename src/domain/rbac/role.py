from __future__ import annotations

from typing import Generic, Set

from src.domain.rbac.employee_protocol import HasRoleIds

from src.domain.rbac.typevar import P
from src.domain.rbac.role_repository import RoleRepository




class RoleManager(Generic[P]):
    """
    Same engine for both realms.
    - validates actor has required_permission (realm permission type P)
    - validates role exists in this realm's RoleRepo
    - mutates target.role_ids (because roles are stored in entities in this variant)
    """
    def __init__(self, authorizer: Authorizer[P], roles: RoleRepository[P]) -> None:
        self._auth = authorizer
        self._roles = roles

    def grant_role(self, actor: HasRoleIds, target: HasRoleIds, role_id: int, *, required_permission: P) -> None:
        self._auth.require(actor, required_permission)
        self._roles.get(role_id)  # validate exists
        target.grant_role(role_id)

    def revoke_role(self, actor: HasRoleIds, target: HasRoleIds, role_id: int, *, required_permission: P) -> None:
        self._auth.require(actor, required_permission)
        self._roles.get(role_id)  # validate exists
        target.revoke_role(role_id)




class Authorizer(Generic[P]):
    def __init__(self, roles: RoleRepository[P]) -> None:
        self._roles = roles

    def permissions_of(self, subject: HasRoleIds) -> Set[P]:
        perms: Set[P] = set()
        for rid in subject.role_ids():
            perms |= set(self._roles.get(rid).permissions)
        return perms

    def require(self, subject: HasRoleIds, permission: P) -> None:
        pass
        if permission not in self.permissions_of(subject):
            raise PermissionError(f"Subject lacks permission: {permission.value}")


