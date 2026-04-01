# src/examples/admin_service_example.py

import sqlite3
import time

from src.application.dto.user_dto import UserDTO
from src.application.services.user_service import UserApplicationService
from src.services.uow.uowsqlite import SQLiteUnitOfWork
from utils.db.connect import Connection


def main() -> None:
    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    uow = SQLiteUnitOfWork(conn)

    service = UserApplicationService(uow)

    # --------------------------------
    # Create user
    # --------------------------------
    create_dto = UserDTO(
        actor_admin_id=4,
        client_id=4,
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        phone="+1 555 123 4567",
        login="john.smith"+str(time.time()),
        password="StrongPass123!",
        roles=frozenset({6}),
        enabled=True,
        enabled_account=True,
    )

    created_user = service.create_user(user_dto=create_dto)
    print("Created user:")
    print(created_user)

    # --------------------------------
    # Update user
    # --------------------------------
    update_dto = UserDTO(
        actor_admin_id=4,
        user_id=created_user.user_id,
        client_id=created_user.client_id,
        first_name="John",
        last_name="Johnson",
        email="john.johnson@example.com",
        phone="+1 555 999 0000",
    )

    updated_user = service.update_user(user_dto=update_dto)
    print("Updated user:")
    print(updated_user)

    # --------------------------------
    # Change password
    # --------------------------------
    change_password_dto = UserDTO(
        actor_admin_id=4,
        user_id=created_user.user_id,
        client_id=created_user.client_id,
        password="NewStrongPass456!",
    )

    user_after_password_change = service.change_password(
        user_dto=change_password_dto
    )
    print("Password changed for user:")
    print(user_after_password_change)

    # --------------------------------
    # Disable user
    # --------------------------------
    disabled_user = service.disable(
        actor_admin_id=4,
        user_id=created_user.user_id,
    )
    print("Disabled user:")
    print(disabled_user)

    # --------------------------------
    # Enable user
    # --------------------------------
    enabled_user = service.enable(
        actor_admin_id=4,
        user_id=created_user.user_id,
    )
    print("Enabled user:")
    print(enabled_user)

    # --------------------------------
    # Get by id
    # --------------------------------
    found_user = service.get_by_id(
        actor_admin_id=4,
        user_id=created_user.user_id,
    )
    print("Found user by id:")
    print(found_user)

    # --------------------------------
    # Get all users
    # --------------------------------
    users = service.get_all(actor_admin_id=4)
    print("All users:")
    for user in users:
        print(user)



if __name__ == "__main__":
    main()