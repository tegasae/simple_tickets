# ============================
# src/domain/permissions/admin.py
# ============================
from src.old.permissions.base import PermissionBase


class AdminPermission(PermissionBase):
    # Client management (admin realm)
    CREATE_CLIENT = "client.create"
    VIEW_CLIENT = "client.view"
    UPDATE_CLIENT = "client.update"
    DISABLE_CLIENT = "client.disable"
    DELETE_CLIENT = "client.delete"

    # Admin management (admin realm)
    CREATE_ADMIN = "admin.create"
    VIEW_ADMIN = "admin.view"
    UPDATE_ADMIN = "admin.update"
    DISABLE_ADMIN = "admin.disable"
    DELETE_ADMIN = "admin.delete"

    # Role management (admin-only)
    ASSIGN_ROLE = "role.assign"
    REVOKE_ROLE = "role.revoke"

    # System / audit
    VIEW_AUDIT_LOG = "audit.view"
    EXPORT_DATA = "system.export"

