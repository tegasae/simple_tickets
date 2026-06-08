from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.exceptions import (
    OptimisticLockError,
    NotFoundError,
)

from src.adapters.repositories.gateways.client_gateway import ClientGateway
from src.adapters.repositories.mappers.client_mapper import ClientMapper

from src.domain.client import Client
from src.domain.exceptions import ItemNotFoundError
from src.domain.repositories.client_repository import ClientRepository


class ClientRepositorySQLite(BaseRepository, ClientRepository):




    VARS = [
        "client_id",
        "name",
        "address",
        "email",
        "phone",
        "admin_id",
        "enabled",
        "version",
        "date_created",
    ]

    # -------------------------
    # Reads
    # -------------------------

    def get(self, client_id: int) -> Client:

        row = self._get_one(
            ClientGateway.SELECT_BY_ID,
            var=self.VARS,
            params={"client_id": client_id},
        )

        if not row:
            raise ItemNotFoundError(f"client {client_id}")

        return ClientMapper.row_to_client(row)

    def get_all(self) -> list[Client]:

        rows = self._get_many(
            ClientGateway.SELECT_BASE,
            var=self.VARS,
        )

        return [ClientMapper.row_to_client(r) for r in rows]

    def exists(self, client_id: int) -> bool:

        return self._exists(
            ClientGateway.EXISTS,
            {"client_id": client_id},
        )

    # -------------------------
    # Writes
    # -------------------------

    def save(self, client: Client) -> Client:

        if client.client_id == 0:

            result = self._exec(
                ClientGateway.INSERT,
                ClientMapper.params(client),
            )

            client.client_id = result.last_row_id
            client.version = 0

            return client

        upd = self._exec(
            ClientGateway.UPDATE,
            ClientMapper.params(client),
        )

        if upd.rowcount == 0:

            if not self.exists(client.client_id):
                raise NotFoundError(
                    f"Client {client.client_id} no longer exists"
                )

            raise OptimisticLockError(
                f"Client {client.client_id} version mismatch"
            )

        client.version += 1

        return client

    def delete(self, client_id: int) -> None:

        if not self.exists(client_id):
            raise NotFoundError(f"Client {client_id} not found")

        self._exec(
            ClientGateway.DELETE,
            {"client_id": client_id},
        )

    def has_created_by_admin(self, *, admin_id) -> bool:
        return self._exists(ClientGateway.SELECT_BY_ADMIN,params={'admin_id': admin_id})
