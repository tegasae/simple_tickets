# ============================
# src/domain/permissions/user.py
# ============================
from src.old.permissions.base import PermissionBase


class UserPermission(PermissionBase):
    # Ticket operations (client/user realm)
    CREATE_TICKET = "ticket.create"
    VIEW_OWN_TICKET = "ticket.view.own"
    UPDATE_OWN_TICKET = "ticket.update.own"
    DELETE_OWN_TICKET = "ticket.delete.own"
