import sqlite3

from src.adapters.repositories.client_repository import ClientRepositorySQLite
from src.domain.services.client import ClientService
from utils.db.connect import Connection


def main():

    # ---------------------------
    # Create DB connection
    # ---------------------------

    conn = Connection.create_connection(
        url="../../db/admins.db",
        engine=sqlite3,
    )

    client_repo = ClientRepositorySQLite(conn)

    client_service = ClientService(client_repository=client_repo)

    conn.begin_transaction()

    try:

        # ---------------------------
        # 1️⃣ Create client
        # ---------------------------

        client = client_service.create_client(
            name="ACME Corporation",
            email="info@acme.com",
            address="New York",
            phone="+1 555 123456",
            created_by_admin_id=1,
        )

        print("Client created:", client)

        # ---------------------------
        # 2️⃣ Update contact info
        # ---------------------------

        client = client_service.update_contact_info(
            client_id=client.client_id,
            email="support@acme.com",
            phone="+1 555 999999",
        )

        print("Client updated:", client)

        # ---------------------------
        # 3️⃣ Get client by ID
        # ---------------------------

        client_get = client_service.get_by_id(
            client_id=client.client_id
        )

        print("Client fetched:", client_get)

        # ---------------------------
        # 4️⃣ Disable client
        # ---------------------------

        client = client_service.disable_client(
            client_id=client.client_id
        )

        print("Client disabled:", client)

        # ---------------------------
        # 5️⃣ Enable client again
        # ---------------------------

        client = client_service.enable_client(
            client_id=client.client_id
        )

        print("Client enabled:", client)

        # ---------------------------
        # 6️⃣ Get all clients
        # ---------------------------

        clients = client_service.get_all()

        print("All clients:", clients)

        # ---------------------------
        # 7️⃣ Delete client
        # ---------------------------
        # Domain rules require that client
        # has no users and no tickets

        client_service.delete_client(
            client_id=client.client_id,
            number_of_users=0,
            number_of_tickets=0,
        )

        print("Client deleted:", client.client_id)

        conn.commit()

    except Exception as e:

        conn.rollback()

        print("ERROR:", e)

    finally:

        conn.close()


if __name__ == "__main__":
    main()