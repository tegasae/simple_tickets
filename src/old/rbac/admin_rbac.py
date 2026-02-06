# ============================
# src/domain/rbac/admin_rbac.py
# Admin realm wiring (separate permissions/roles/assignments)
# ============================
from __future__ import annotations

from src.old.permissions.admin import AdminPermission
from src.old.rbac.core import AssignmentRepo, Authorizer, Role, RoleManager, RoleRepo

AdminRole = Role[AdminPermission]


def build_admin_rbac() -> tuple[RoleRepo[AdminPermission], AssignmentRepo, Authorizer[AdminPermission], RoleManager[AdminPermission]]:
    roles = RoleRepo[AdminPermission]()
    assignments = AssignmentRepo()
    auth = Authorizer[AdminPermission](roles, assignments)
    manager = RoleManager[AdminPermission](auth, roles, assignments)
    return roles, assignments, auth, manager
