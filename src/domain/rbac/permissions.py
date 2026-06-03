#src/domain/rbac/permissions.py

from enum import StrEnum
# ---------------------------
# Permissions (separate forever)
# ---------------------------


class PermissionBase(StrEnum):
    """Stable string identifiers (DB-friendly)."""
    pass


class AdminPermission(PermissionBase):
    CLIENT_OPERATION = "client.operation"
    CLIENT_VIEW = "client.view"
    ADMIN_OPERATION="admin.operation"
    ADMIN_VIEW="admin.view"
    USER_OPERATION="user.operation"
    USER_VIEW="user.view"
    TICKET_OPERATION="ticket.operation"
    TICKET_VIEW = "ticket.view"
    ROLE_ASSIGN="role.assign"
    ROLE_REVOKE="role.revoke"

class UserPermission(PermissionBase):
    TICKET_OPERATION = "ticket.operation"
    TICKET_OPERATION_ALL="ticket.operation.all"
    TICKET_VIEW = "ticket.view"
    TICKET_VIEW_ALL = "ticket.view.all"


