

import sqlite3

from src.application.services.role_admin_service import RoleService
from src.domain.rbac.permissions import AdminPermission


from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection


def main():

    # ---------------------------
    # Create DB connection
    # ---------------------------

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )
    uow=SQLiteUnitOfWork(connection=conn)
    # Admin realm roles


    role_service = RoleService(uow=uow)

    role = role_service.create_role(
        name="Support",
        permissions={
            AdminPermission.VIEW_ADMIN,
            AdminPermission.VIEW_AUDIT_LOG,
        },
        description="Support staff role",
    )

    print("Role created:", role)

    role=role_service.create_role(name="new",permissions={
            AdminPermission.VIEW_ADMIN,
            AdminPermission.VIEW_AUDIT_LOG,
        },description="description")

    print(role)
    roles = role_service.get_all_roles()

    print("All roles:")

    for r in roles:
        print(r)

    conn.close()

if __name__ == "__main__":
    main()