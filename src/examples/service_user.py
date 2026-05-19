import sqlite3

from src.adapters.repositories.user_repository import UserRepositorySQLite
from src.application.services.user_service import UserApplicationService

from utils.db.connect import Connection


def main():

    # ---------------------------
    # Create DB connection
    # ---------------------------

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    user_repo = UserRepositorySQLite(conn)

    user_service = UserApplicationService(
        uow=user_repo
    )

    conn.begin_transaction()

    try:

        # ---------------------------
        # 1️⃣ Create user WITHOUT account
        # ---------------------------

        user = user_service.create_user(
            client_id=1,
            first_name="John",
            last_name="Smith",
        )

        print("Created user:", user)

        # ---------------------------
        # 2️⃣ Attach account
        # ---------------------------

        user = user_service.attach_account(
            user_id=user.employee_id,
            login="john_user",
            password="secure_password_123S@",
        )

        print("Account attached:", user.account)

        # ---------------------------
        # 3️⃣ Update user data
        # ---------------------------

        user = user_service.update_user(
            user_id=user.employee_id,
            email="john.smith@company.com",
        )

        print("User updated:", user)


        # ---------------------------
        # 4️⃣ Disable user account
        # ---------------------------

        user = user_service.disable_user_account(
            user_id=user.employee_id
        )

        print("Account disabled:", user.account)

        # ---------------------------
        # 5️⃣ Enable user account again
        # ---------------------------

        user = user_service.enable_user_account(
            user_id=user.employee_id
        )

        print("Account enabled:", user.account)

        # ---------------------------
        # 6️⃣ Update password
        # ---------------------------

        user = user_service.update_password(
            user_id=user.employee_id,
            password="1234567890@Ww"
        )

        print("Password updated:", user)

        # ---------------------------
        # 7️⃣ Get user by id
        # ---------------------------

        user_get = user_service.get_by_id(
            user_id=user.employee_id
        )

        print("User get:", user_get)

        # ---------------------------
        # 8️⃣ Get all users
        # ---------------------------

        user_all = user_service.get_all()

        print("User all:", user_all)

        # ---------------------------
        # 9️⃣ Find user by login
        # ---------------------------

        user = user_service.find_by_login("john_user")

        print("User found by login:", user)

        # ---------------------------
        # 🔟 Disable entire user
        # ---------------------------

        user = user_service.disable_user(
            user_id=user.employee_id
        )

        print("User disabled:", user)

        # ---------------------------
        # 1️⃣1️⃣ Detach account
        # ---------------------------

        user = user_service.detach_account(
            user_id=user.employee_id
        )

        print("Account detached:", user)

        conn.commit()

    except Exception as e:

        conn.rollback()

        print("ERROR:", e)
        raise e
    finally:

        conn.close()


if __name__ == "__main__":
    main()