import sqlite3

from src.adapters.repositories.role_repository import RoleRepositorySQLite
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.role import RoleService
from utils.db.connect import Connection


def main():

    # ---------------------------
    # Create DB connection
    # ---------------------------

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    # Admin realm roles
    role_repo = RoleRepositorySQLite(
        conn=conn,
        permission_cls=AdminPermission,
        is_admin=True,
    )

    role_service = RoleService(role_repository=role_repo)

    conn.begin_transaction()

    try:

        # ---------------------------
        # 1️⃣ Create role
        # ---------------------------

        role = role_service.create_role(
            name="Support",
            permissions={
                AdminPermission.VIEW_ADMIN,
                AdminPermission.VIEW_AUDIT_LOG,
            },
            description="Support staff role",
        )

        print("Role created:", role)

        # ---------------------------
        # 2️⃣ Get role by id
        # ---------------------------

        role_get = role_service.get_role(role.role_id)

        print("Role get:", role_get)

        # ---------------------------
        # 3️⃣ List all roles
        # ---------------------------

        roles = role_service.get_all_roles()

        print("All roles:")

        for r in roles:
            print(r)

        # ---------------------------
        # 4️⃣ Delete role
        # ---------------------------

        role_service.delete_role(role.role_id)

        print("Role deleted:", role.role_id)

        conn.commit()

    except Exception as e:

        conn.rollback()

        print("ERROR:", e)
        raise 

    finally:

        conn.close()


if __name__ == "__main__":
    main()