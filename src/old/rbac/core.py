# ============================
# src/domain/rbac/core.py
# One shared RBAC engine (generic, typed)
# ============================
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, FrozenSet, Generic, Iterable, Optional, Set, TypeVar

from src.old.permissions.base import PermissionBase

P = TypeVar("P", bound=PermissionBase)


@dataclass(frozen=True)
class Role(Generic[P]):
    """
    Immutable role = named bundle of permissions.
    Permissions are realm-specific by type parameter P.
    """
    role_id: int
    name: str
    permissions: FrozenSet[P] = field(default_factory=frozenset)
    description: str = ""
    is_system_role: bool = False
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_permission(self, permission: P) -> bool:
        return permission in self.permissions


@dataclass(frozen=True)
class RoleAssignment:
    """
    Audit-friendly assignment record (realm-agnostic).
    Store role_name because it's stable for logs and DB mapping.
    """
    employee_id: int
    role_name: str
    assigned_by_employee_id: Optional[int] = None
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RoleRepo(Generic[P]):
    """In-memory role registry for a realm."""
    def __init__(self) -> None:
        self._roles_by_name: Dict[str, Role[P]] = {}

    def add(self, role: Role[P]) -> None:
        if role.name in self._roles_by_name:
            raise ValueError(f"Role already exists: {role.name}")
        self._roles_by_name[role.name] = role

    def get(self, name: str) -> Role[P]:
        try:
            return self._roles_by_name[name]
        except KeyError:
            raise LookupError(f"Unknown role: {name}") from None

    def all(self) -> Iterable[Role[P]]:
        return self._roles_by_name.values()


class AssignmentRepo:
    """
    In-memory assignment store: employee_id -> set(role_name).
    (Separate instance per realm!)
    """
    def __init__(self) -> None:
        self._by_employee: Dict[int, Set[str]] = {}
        self._history: list[RoleAssignment] = []

    def grant(self, employee_id: int, role_name: str, assigned_by: Optional[int]) -> None:
        self._by_employee.setdefault(employee_id, set()).add(role_name)
        self._history.append(
            RoleAssignment(employee_id=employee_id, role_name=role_name, assigned_by_employee_id=assigned_by)
        )

    def revoke(self, employee_id: int, role_name: str) -> None:
        self._by_employee.get(employee_id, set()).discard(role_name)

    def roles_of(self, employee_id: int) -> FrozenSet[str]:
        return frozenset(self._by_employee.get(employee_id, set()))

    def history(self) -> tuple[RoleAssignment, ...]:
        return tuple(self._history)


@dataclass(frozen=True)
class Actor:
    """Who performs actions. (Scripts can pass employee_id.)"""
    employee_id: int


class Authorizer(Generic[P]):
    """Compute permissions for an actor and enforce checks (realm-specific by P)."""
    def __init__(self, roles: RoleRepo[P], assignments: AssignmentRepo) -> None:
        self._roles = roles
        self._assignments = assignments

    def permissions_of(self, actor: Actor) -> Set[P]:
        perms: Set[P] = set()
        for role_name in self._assignments.roles_of(actor.employee_id):
            perms |= set(self._roles.get(role_name).permissions)
        return perms

    def has(self, actor: Actor, permission: P) -> bool:
        return permission in self.permissions_of(actor)

    def require(self, actor: Actor, permission: P) -> None:
        if not self.has(actor, permission):
            raise PermissionError(f"Employee {actor.employee_id} lacks permission: {permission.value}")


class RoleManager(Generic[P]):
    """
    Realm RBAC admin operations (grant/revoke).
    The permission to grant/revoke is provided by the caller,
    so this engine can be shared across realms.
    """
    def __init__(self, authorizer: Authorizer[P], roles: RoleRepo[P], assignments: AssignmentRepo) -> None:
        self._auth = authorizer
        self._roles = roles
        self._assignments = assignments

    def grant_role(self, actor: Actor, target_employee_id: int, role_name: str, required_permission: P) -> None:
        self._auth.require(actor, required_permission)
        self._roles.get(role_name)  # validate role exists
        self._assignments.grant(target_employee_id, role_name, assigned_by=actor.employee_id)

    def revoke_role(self, actor: Actor, target_employee_id: int, role_name: str, required_permission: P) -> None:
        self._auth.require(actor, required_permission)
        self._assignments.revoke(target_employee_id, role_name)





