# ============================
# src/domain/rbac/user_rbac.py
# User realm wiring (separate permissions/roles/assignments)
# ============================
from __future__ import annotations

from src.domain.permissions.user import UserPermission
from src.domain.rbac.core import AssignmentRepo, Authorizer, Role, RoleManager, RoleRepo

UserRole = Role[UserPermission]


def build_user_rbac() -> tuple[RoleRepo[UserPermission], AssignmentRepo, Authorizer[UserPermission], RoleManager[UserPermission]]:
    roles = RoleRepo[UserPermission]()
    assignments = AssignmentRepo()
    auth = Authorizer[UserPermission](roles, assignments)
    manager = RoleManager[UserPermission](auth, roles, assignments)
    return roles, assignments, auth, manager
