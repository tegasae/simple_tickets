from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Dict, FrozenSet, Generic, Iterable, Optional, Protocol, Set, TypeVar


# ---------------------------
# Permissions (separate forever)
# ---------------------------

class PermissionBase(StrEnum):
    """Stable string identifiers (DB-friendly)."""
    pass


class AdminPermission(PermissionBase):
    VIEW_ADMIN = "admin.view"
    UPDATE_ADMIN = "admin.update"
    ASSIGN_ROLE = "role.assign"
    REVOKE_ROLE = "role.revoke"
    VIEW_AUDIT_LOG = "audit.view"


class UserPermission(PermissionBase):
    CREATE_TICKET = "ticket.create"
    VIEW_OWN_TICKET = "ticket.view.own"
    UPDATE_OWN_TICKET = "ticket.update.own"
    DELETE_OWN_TICKET = "ticket.delete.own"


# ---------------------------
# RBAC core (generic)
# Role identity = role_id: int (DB-friendly)
# ---------------------------

P = TypeVar("P", bound=PermissionBase)


@dataclass(frozen=True)
class Role(Generic[P]):
    role_id: int                 # DB primary key
    name: str                    # human-readable (may change)
    permissions: FrozenSet[P] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_permission(self, permission: P) -> bool:
        return permission in self.permissions


class RoleRepo(Generic[P]):
    """In-memory role registry for ONE realm (Admin OR User)."""
    def __init__(self) -> None:
        self._by_id: Dict[int, Role[P]] = {}

    def add(self, role: Role[P]) -> None:
        if role.role_id in self._by_id:
            raise ValueError(f"Role already exists: id={role.role_id}")
        self._by_id[role.role_id] = role

    def get(self, role_id: int) -> Role[P]:
        try:
            return self._by_id[role_id]
        except KeyError:
            raise LookupError(f"Unknown role_id={role_id}") from None

    def all(self) -> Iterable[Role[P]]:
        return self._by_id.values()


class HasRoleIds(Protocol):
    """Entity protocol: RBAC needs role ids + mutation."""
    def role_ids(self) -> FrozenSet[int]: ...
    def grant_role(self, role_id: int) -> None: ...
    def revoke_role(self, role_id: int) -> None: ...


class Authorizer(Generic[P]):
    def __init__(self, roles: RoleRepo[P]) -> None:
        self._roles = roles

    def permissions_of(self, subject: HasRoleIds) -> Set[P]:
        perms: Set[P] = set()
        for rid in subject.role_ids():
            perms |= set(self._roles.get(rid).permissions)
        return perms

    def require(self, subject: HasRoleIds, permission: P) -> None:
        if permission not in self.permissions_of(subject):
            raise PermissionError(f"Subject lacks permission: {permission.value}")


class RoleManager(Generic[P]):
    """
    Same engine for both realms.
    - validates actor has required_permission (realm permission type P)
    - validates role exists in this realm's RoleRepo
    - mutates target.role_ids (because roles are stored in entities in this variant)
    """
    def __init__(self, authorizer: Authorizer[P], roles: RoleRepo[P]) -> None:
        self._auth = authorizer
        self._roles = roles

    def grant_role(self, actor: HasRoleIds, target: HasRoleIds, role_id: int, *, required_permission: P) -> None:
        self._auth.require(actor, required_permission)
        self._roles.get(role_id)  # validate exists
        target.grant_role(role_id)

    def revoke_role(self, actor: HasRoleIds, target: HasRoleIds, role_id: int, *, required_permission: P) -> None:
        self._auth.require(actor, required_permission)
        target.revoke_role(role_id)


# ---------------------------
# Domain entities (roles stored inside entities as role_id: int)
# Admin/User remain separate realms by using separate repos/authorizers/managers.
# ---------------------------

@dataclass
class Employee:
    employee_id: int
    first_name: str
    last_name: str
    email: str
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    enabled: bool = True
    is_deleted: bool = False


@dataclass(kw_only=True)
class Admin(Employee, HasRoleIds):
    department: str
    _role_ids: Set[int] = field(default_factory=set, repr=False)

    def role_ids(self) -> FrozenSet[int]:
        return frozenset(self._role_ids)

    def grant_role(self, role_id: int) -> None:
        self._role_ids.add(role_id)

    def revoke_role(self, role_id: int) -> None:
        self._role_ids.discard(role_id)


@dataclass(kw_only=True)
class User(Employee):
    client_id: int
    _role_ids: Set[int] = field(default_factory=set, repr=False)

    def role_ids(self) -> FrozenSet[int]:
        return frozenset(self._role_ids)

    def grant_role(self, role_id: int) -> None:
        self._role_ids.add(role_id)

    def revoke_role(self, role_id: int) -> None:
        self._role_ids.discard(role_id)


# ---------------------------
# Realm wiring (like before, but role_id-based)
# Avoids Role[AdminPermission](...) warnings by using aliases.
# ---------------------------


