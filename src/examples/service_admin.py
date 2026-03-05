# src/examples/admin_service_example.py

import sqlite3

from src.adapters.repositories.admin import AdminRepositorySQLite
from src.domain.services.admin import AdminService
from utils.db.connect import Connection


def main():

    # ---------------------------
    # Create DB connection
    # ---------------------------

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    admin_repo = AdminRepositorySQLite(conn)

    admin_service = AdminService(admin_repository=admin_repo)

    conn.begin_transaction()

    try:

        # ---------------------------
        # 1️⃣ Create admin WITHOUT account
        # ---------------------------

        admin = admin_service.create_admin(
            first_name="John",
            last_name="Smith",
            job_title="System Administrator",
        )

        print("Created admin:", admin)

        # ---------------------------
        # 2️⃣ Attach account
        # ---------------------------

        admin = admin_service.attach_account(
            admin_id=admin.employee_id,
            login="john_admin",
            password="secure_password_123S@",
        )

        print("Account attached:", admin.account)

        # ---------------------------
        # 3️⃣ Update admin data
        # ---------------------------

        admin = admin_service.update_admin(
            admin_id=admin.employee_id,
            job_title="Senior Administrator",
            email="john.smith@company.com",
        )

        print("Admin updated:", admin)

        # ---------------------------
        # 4️⃣ Grant roles
        # ---------------------------

        admin_service.grant_role(
            admin_id=admin.employee_id,
            role_id=1,
        )

        admin_service.grant_role(
            admin_id=admin.employee_id,
            role_id=2,
        )

        roles = admin_service.get_roles(
            admin_id=admin.employee_id
        )

        print("Roles granted:", roles)

        # ---------------------------
        # 5️⃣ Revoke one role
        # ---------------------------

        admin_service.revoke_role(
            admin_id=admin.employee_id,
            role_id=2,
        )

        roles = admin_service.get_roles(
            admin_id=admin.employee_id
        )

        print("Roles after revoke:", roles)

        # ---------------------------
        # 6️⃣ Disable admin account
        # ---------------------------

        admin = admin_service.disable_admin_account(
            admin_id=admin.employee_id
        )

        print("Account disabled:", admin.account)

        # ---------------------------
        # 7️⃣ Enable admin account again
        # ---------------------------

        admin = admin_service.enable_admin_account(
            admin_id=admin.employee_id
        )

        print("Account enabled:", admin.account)

        # ---------------------------
        # 8️⃣ Change password
        # ---------------------------

        admin = admin_service.update_password(
            admin_id=admin.employee_id,
            password="1234567890@Ww",
        )

        print("Password updated:", admin)

        # ---------------------------
        # 9️⃣ Read admin
        # ---------------------------

        admin_get = admin_service.get_by_id(
            admin_id=admin.employee_id
        )

        print("Admin get:", admin_get)

        admin_all = admin_service.get_all()

        print("Admin all:", admin_all)

        # ---------------------------
        # 🔟 Find admin by login
        # ---------------------------

        admin = admin_service.find_by_login("john_admin")

        print("Admin found by login:", admin)

        # ---------------------------
        # 11️⃣ Disable entire admin
        # ---------------------------

        admin = admin_service.disable_admin(
            admin_id=admin.employee_id
        )

        print("Admin disabled:", admin)

        # ---------------------------
        # 12️⃣ Detach account
        # ---------------------------

        admin = admin_service.detach_account(
            admin_id=admin.employee_id
        )

        print("Account detached:", admin)

        conn.commit()

    except Exception as e:

        conn.rollback()
        raise e
        #print("ERROR:", e)

    finally:

        conn.close()


if __name__ == "__main__":
    main()