from src.domain.services.admin import AdminService
from src.domain.services.client import ClientService
from src.domain.services.user import UserService
from src.services.uow.uowsqlite import SQLiteUnitOfWork


def main():

    with SQLiteUnitOfWork("../../db/admins.db") as uow:

        admin_service = AdminService(uow.admins)
        user_service = UserService(uow.users)
        client_service = ClientService(uow.clients)

        # ---------------------
        # Create admin
        # ---------------------

        admin = admin_service.create_admin(
            first_name="John",
            last_name="Smith",
            job_title="System Administrator",
        )

        print("Admin created:", admin)

        # ---------------------
        # Create client
        # ---------------------

        client = client_service.create_client(
            name="ACME Corporation",
            created_by_admin_id=admin.employee_id,
        )

        print("Client created:", client)

        # ---------------------
        # Create user
        # ---------------------

        user = user_service.create_user(
            client_id=client.client_id,
            first_name="Alice",
            last_name="Brown",
        )

        print("User created:", user)

        # ---------------------
        # Assign role
        # ---------------------

        admin_service.grant_role(
            admin_id=admin.employee_id,
            role_id=1
        )

        print("Role granted to admin")

        # commit happens automatically

if __name__ == "__main__":
    main()