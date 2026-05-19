import sqlite3
import time

from src.application.dto.employee_dto import UserDTO
from src.application.services.user_service import UserApplicationService
from src.domain.exceptions import DomainOperationError
from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection


def user_example() -> None:
    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    uow = SQLiteUnitOfWork(conn)
    service = UserApplicationService(uow)

    try:
        # --------------------------------
        # Create a new user
        # --------------------------------
        time_login = "bob.smith" + time.strftime("%Y%m%d%H%M%S")
        create_dto = UserDTO(
            employee_id=0,
            actor_admin_id=4,   # existing admin who performs the action
            client_id=4,       # existing client
            first_name="Bob",
            last_name="Smith",
            email="bob.smith@example.com",
            phone="+1 555 222 3333",
            login=time_login,
            password="StrongPass123!",
            enable=True,
            enable_account=True,
            roles=frozenset({63}),
        )

        created_user = service.create_user(user_dto=create_dto)
        print("Created user:")
        print(created_user)

        # --------------------------------
        # Update the user
        # --------------------------------
        update_dto = UserDTO(
            employee_id=created_user.employee_id,
            actor_admin_id=4,
            client_id=created_user.client_id,
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@example.com",
            phone="+1 555 222 9999",
        )

        updated_user = service.update_user(user_dto=update_dto)
        print("Updated user:")
        print(updated_user)

        # --------------------------------
        # Grant a role
        # --------------------------------
        grant_role_dto = UserDTO(
            employee_id=created_user.employee_id,
            actor_admin_id=4,
            client_id=created_user.client_id,
            roles=frozenset({63}),
        )

        user_after_role = service.grant_role(user_dto=grant_role_dto)
        print("Granted role:")
        print(user_after_role)

        # --------------------------------
        # Disable the user
        # --------------------------------
        disable_dto = UserDTO(
            employee_id=created_user.employee_id,
            actor_admin_id=4,
            client_id=created_user.client_id,
        )

        disabled_user = service.disable(user_dto=disable_dto)
        print("Disabled user:")
        print(disabled_user)

        # --------------------------------
        # Get by id
        # --------------------------------
        get_dto = UserDTO(
            employee_id=created_user.employee_id,
            actor_admin_id=4,
            client_id=created_user.client_id,
        )

        loaded_user = service.get_by_id(user_dto=get_dto)
        print("Loaded user:")
        print(loaded_user)

    except DomainOperationError as exc:
        print(f"Domain error: {exc}")
        raise
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        raise

if __name__ == "__main__":
    user_example()