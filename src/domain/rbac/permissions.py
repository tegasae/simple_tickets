#src/domain/rbac/permissions.py

from enum import StrEnum
# ---------------------------
# Permissions (separate forever)
# ---------------------------


class PermissionBase(StrEnum):
    """Stable string identifiers (DB-friendly)."""
    pass


class AdminPermission(PermissionBase):
    VIEW_ADMIN = "admin.view"
    VIEW_USER = "view.user"
    UPDATE_ADMIN = "admin.update"
    ASSIGN_ROLE = "role.assign"
    REVOKE_ROLE = "role.revoke"
    VIEW_AUDIT_LOG = "audit.view"
    CREATE_USER="create.user"
    CREATE_ADMIN="create.admin"
    UPDATE_USER = "update.user"
    DELETE_ADMIN = "delete.admin"
    DELETE_USER = "delete.user"
    OPERATION_CLIENT = "operation.client"
    VIEW_TICKET = "ticket.view"
    CREATE_TICKET = "ticket.create"
    UPDATE_TICKET = "ticket.update"
    ASSIGN_TICKET = "ticket.assign"
    DELETE_TICKET = "ticket.delete"


class UserPermission(PermissionBase):
    CREATE_TICKET = "ticket.create"
    VIEW_OWN_TICKET = "ticket.view.own"
    UPDATE_OWN_TICKET = "ticket.update.own"
    DELETE_OWN_TICKET = "ticket.delete.own"
    VIEW_ALL_TICKET = "ticket.view.all"
    UPDATE_ALL_TICKET = "ticket.update.all"
    DELETE_ALL_TICKET = "ticket.delete.all"