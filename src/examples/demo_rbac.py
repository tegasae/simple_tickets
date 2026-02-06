# ============================
# src/examples/demo_rbac.py
# ============================
from __future__ import annotations

from src.old.permissions.admin import AdminPermission
from src.old.permissions.user import UserPermission
from src.old.rbac.core import Actor
from src.old.rbac.admin_rbac import build_admin_rbac, AdminRole
from src.old.rbac.user_rbac import build_user_rbac, UserRole


def demo() -> None:
    # Build both realms (completely separate)
    admin_roles, admin_assignments, admin_auth, admin_role_mgr = build_admin_rbac()
    user_roles, user_assignments, user_auth, user_role_mgr = build_user_rbac()

    # Define roles per realm (use realm-specific aliases to avoid Role[...](...) warnings)
    admin_roles.add(
        AdminRole(
            role_id=1,
            name="SuperAdmin",
            permissions=frozenset(
                {
                    AdminPermission.VIEW_ADMIN,
                    AdminPermission.UPDATE_ADMIN,
                    AdminPermission.ASSIGN_ROLE,
                    AdminPermission.REVOKE_ROLE,
                    AdminPermission.VIEW_AUDIT_LOG,
                }
            ),
            is_system_role=True,
        )
    )

    user_roles.add(
        UserRole(
            role_id=10,
            name="TicketUser",
            permissions=frozenset(
                {
                    UserPermission.CREATE_TICKET,
                    UserPermission.VIEW_OWN_TICKET,
                    UserPermission.UPDATE_OWN_TICKET,
                }
            ),
            is_system_role=True,
        )
    )

    # Seed assignments
    admin_assignments.grant(employee_id=100, role_name="SuperAdmin", assigned_by=None)
    user_assignments.grant(employee_id=200, role_name="TicketUser", assigned_by=None)

    # Check permissions
    admin_auth.require(Actor(100), AdminPermission.VIEW_AUDIT_LOG)   # OK
    user_auth.require(Actor(200), UserPermission.CREATE_TICKET)      # OK

    # Admin can grant ADMIN roles (guarded by admin permission)
    admin_role_mgr.grant_role(
        actor=Actor(100),
        target_employee_id=101,
        role_name="SuperAdmin",
        required_permission=AdminPermission.ASSIGN_ROLE,
    )

    print("RBAC demo OK")


if __name__ == "__main__":
    demo()
