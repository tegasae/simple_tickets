from datetime import datetime

from src.domain.client import Client


class ClientMapper:
    VARS = [
        "client_id",
        "name",
        "address",
        "email",
        "phone",
        "description",
        "admin_id",
        "enabled",
        "version",
        "date_created",
    ]
    @staticmethod
    def row_to_client(row: dict) -> Client:

        client = Client.create(
            client_id=row["client_id"],
            name=row["name"],
            email=row["email"],
            address=row["address"],
            phone=row["phone"],
            description=row["description"],
            created_by_admin_id=row["admin_id"],
            enabled=bool(row["enabled"]),
        )
        try:
            client.version = int(row["version"])
        except TypeError:
            client.version=0

        if row["date_created"]:
            try:
                client.date_created = datetime.fromisoformat(row["date_created"])
            except ValueError:
                client.date_created = datetime.now()

        return client

    @staticmethod
    def params(client: Client) -> dict:

        return {
            "client_id": client.client_id,
            "name": str(client.name),
            "address": str(client.address) if client.address else None,
            "email": str(client.email) if client.email else None,
            "phone": str(client.phone) if client.phone else None,
            "description":str(client.description) if client.description else None,
            "admin_id": client.created_by_admin_id,
            "enabled": int(client.enabled),
            "version": client.version,
            "date_created": client.date_created.isoformat(),
        }