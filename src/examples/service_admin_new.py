import sqlite3
import time

from src.application.dto.employee_dto import AdminDTO
from src.application.services.admin_service import AdminApplicationService
from src.domain.exceptions import DomainOperationError


from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection


def main() -> None:



    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    uow = SQLiteUnitOfWork(conn)
    service = AdminApplicationService(uow)
    try:
        # -----------------------------
        # Create admin
        # -----------------------------
        create_dto = AdminDTO(
            employee_id=0,
            actor_admin_id=4,
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            phone="+1 555 123 4567",
            login="john.smith"+str(time.time()),
            password="StrongPass123!",
            enable_account=True,
            roles=frozenset({60, 62}),
            job_title="System Administrator",
        )

        created_admin = service.create_admin(admin_dto=create_dto)
        print("Created admin:")
        print(created_admin)

        # -----------------------------
        # Get admin by id
        # -----------------------------
        get_by_id_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=1,
        )

        loaded_admin = service.get_by_id(admin_dto=get_by_id_dto)
        print("Loaded admin:")
        print(loaded_admin)

        # -----------------------------
        # Update admin
        # -----------------------------
        update_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=1,
            first_name="John",
            last_name="Johnson",
            email="john.johnson@example.com",
            phone="+1 555 999 0000",
            job_title="Senior System Administrator",
        )

        updated_admin = service.update_admin(admin_dto=update_dto)
        print("Updated admin:")
        print(updated_admin)

        # -----------------------------
        # Change password
        # -----------------------------
        change_password_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=1,
            password="NewStrongPass456!",
        )

        admin_after_password_change = service.change_password(
            admin_dto=change_password_dto
        )
        print("Password changed:")
        print(admin_after_password_change)

        # -----------------------------
        # Grant role
        # -----------------------------
        grant_role_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=1,
            roles=frozenset({66}),
        )

        admin_after_grant = service.grant_role(admin_dto=grant_role_dto)
        print("Role granted:")
        print(admin_after_grant)

        # -----------------------------
        # Revoke role
        # -----------------------------
        revoke_role_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=1,
            roles=frozenset({60}),
        )

        admin_after_revoke = service.revoke_role(admin_dto=revoke_role_dto)
        print("Role revoked:")
        print(admin_after_revoke)

        # -----------------------------
        # Find by login
        # -----------------------------
        find_by_login_dto = AdminDTO(
            employee_id=0,
            actor_admin_id=1,
            login="john.smith",
        )

        found_admin = service.find_by_login(find_by_login_dto)
        print("Found by login:")
        print(found_admin)

        # -----------------------------
        # Disable admin
        # -----------------------------
        disable_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=1,
        )

        disabled_admin = service.disable(admin_dto=disable_dto)
        print("Disabled admin:")
        print(disabled_admin)

        # -----------------------------
        # Enable admin
        # -----------------------------
        enable_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=1,
        )

        enabled_admin = service.enable(admin_dto=enable_dto)
        print("Enabled admin:")
        print(enabled_admin)

        # -----------------------------
        # Get all admins
        # -----------------------------
        get_all_dto = AdminDTO(
            employee_id=0,
            actor_admin_id=1,
        )

        all_admins = service.get_all(admin_dto=get_all_dto)
        print("All admins:")
        for admin in all_admins:
            print(admin)

    except DomainOperationError as exc:
        print(f"Domain error: {exc}")

    except Exception as exc:
        print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()