from enum import StrEnum
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
