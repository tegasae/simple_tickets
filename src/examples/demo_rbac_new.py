from src.domain.account import NoAccount
from src.domain.employee import Admin, User
from src.domain.rbac.admin_rbac import build_admin_rbac, AdminRole
from src.domain.rbac.permissions import AdminPermission, UserPermission

from src.domain.rbac.user_rbac import build_user_rbac, UserRole
from src.domain.value_objects import Name, Email


# ---------------------------
# Demo
# ---------------------------

def demo() -> None:
    admin_roles, admin_auth, admin_mgr = build_admin_rbac()
    user_roles, user_auth, _user_mgr = build_user_rbac()

    # Define roles per realm using role_id as identity (DB-ready)
    admin_roles.add(
        AdminRole(
            role_id=1,
            name="SuperAdmin",
            permissions=frozenset({
                AdminPermission.VIEW_ADMIN,
                AdminPermission.UPDATE_ADMIN,
                AdminPermission.ASSIGN_ROLE,
                AdminPermission.REVOKE_ROLE,
                AdminPermission.VIEW_AUDIT_LOG,
            }),
            is_system_role=True,
        )
    )

    user_roles.add(
        UserRole(
            role_id=10,
            name="TicketUser",
            permissions=frozenset({
                UserPermission.CREATE_TICKET,
                UserPermission.VIEW_OWN_TICKET,
                UserPermission.UPDATE_OWN_TICKET,
            }),
            is_system_role=True,
        )
    )

    # Create entities and give initial roles (bootstrap)
    super_admin = Admin(
        employee_id=100,
        first_name=Name("Alice"),
        last_name=Name("Admin"),
        email=Email("alice@example.com"),
        account=NoAccount()

    )
    super_admin.grant_role(1)  # SuperAdmin role_id

    another_admin = Admin(
        employee_id=101,
        first_name=Name("Bob"),
        last_name=Name("Admin"),
        email=Email("bob@example.com")

    )

    user = User(
        employee_id=200,
        first_name=Name("Carol"),
        last_name=Name("User"),
        email=Email("carol@example.com"),
        client_id=1,
    )
    user.grant_role(10)  # TicketUser role_id

    # Permission checks
    admin_auth.require(super_admin, AdminPermission.VIEW_AUDIT_LOG)
    user_auth.require(user, UserPermission.CREATE_TICKET)

    # Grant admin role to another admin (guarded by assign permission)
    admin_mgr.grant_role(
        actor=super_admin,
        target=another_admin,
        role_id=1,
        required_permission=AdminPermission.ASSIGN_ROLE,
    )

    print("OK")


if __name__ == "__main__":
    demo()
