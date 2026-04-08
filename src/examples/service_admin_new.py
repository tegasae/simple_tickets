import sqlite3
import time



from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection



from src.application.dto.employee_dto import AdminDTO
from src.application.services.admin_service import AdminApplicationService
from src.domain.exceptions import DomainOperationError


def admin_example() -> None:
    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    uow = SQLiteUnitOfWork(conn)


    service = AdminApplicationService(uow)

    try:
        # --------------------------------
        # Create a new admin
        # --------------------------------
        time_login="alice.johnson"+time.strftime("%Y%m%d%H%M%S")
        create_dto = AdminDTO(
            employee_id=0,
            actor_admin_id=4,   # existing admin who performs the action
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@example.com",
            phone="+1 555 100 2000",
            login=time_login,
            password="StrongPass123!",
            enable=True,
            enable_account=True,
            roles=frozenset({5, 7}),
            job_title="Operations Manager",
        )

        created_admin = service.create_admin(admin_dto=create_dto)
        print("Created admin:")
        print(created_admin)

        # --------------------------------
        # Update the admin
        # --------------------------------
        update_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=4,
            first_name="Alice",
            last_name="Brown",
            email="alice.brown@example.com",
            phone="+1 555 100 9999",
            job_title="Senior Operations Manager",
        )

        updated_admin = service.update_admin(admin_dto=update_dto)
        print("Updated admin:")
        print(updated_admin)

        # --------------------------------
        # Change password
        # --------------------------------
        change_password_dto = AdminDTO(
            employee_id=created_admin.employee_id,
            actor_admin_id=4,
            password="NewStrongPass456!",
        )

        admin_after_password_change = service.change_password(
            admin_dto=change_password_dto
        )
        print("Password changed:")
        print(admin_after_password_change)

        # --------------------------------
        # Find by login
        # --------------------------------
        find_dto = AdminDTO(
            employee_id=0,
            actor_admin_id=4,
            login=time_login,
        )

        found_admin = service.find_by_login(find_dto)
        print("Found by login:")
        print(found_admin)

        # --------------------------------
        # Get all admins
        # --------------------------------
        get_all_dto = AdminDTO(
            employee_id=0,
            actor_admin_id=4,
        )

        admins = service.get_all(admin_dto=get_all_dto)
        print("All admins:")
        for admin in admins:
            print(admin)

    except DomainOperationError as exc:
        print(f"Domain error: {exc}")
        raise

    except Exception as exc:
        print(f"Unexpected error: {exc}")
        raise




if __name__ == "__main__":
    admin_example()


