
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Callable

from src.domain.exceptions import ItemValidationError, ItemAlreadyExistsError, ItemNotFoundError
from src.domain.value_objects import Emails, Address, Phones, ClientName


@dataclass
class Client:
    client_id: int    # ✅ Public field
    name: ClientName         # ✅ Public field
    emails: Emails
    address: Address
    phones: Phones
    admin_id: int=0
    enabled: bool = True
    date_created: datetime = field(default_factory=datetime.now)
    _validators: list[Callable] = None
    # Business logic methods (not getters/setters!)



    @classmethod
    def empty_client(cls):
        return cls(client_id=0, name=ClientName("-"), admin_id=0,
                   phones=Phones(),address=Address(),emails=Emails(),enabled=False)




class ClientsAggregate:
    def __init__(self, clients: List[Client] = None, version: int = 0):
        self.clients: Dict[str, Client] = {}  # Index by unique name
        self.clients_by_id: Dict[int, Client] = {}  # Index by ID
        self.new_clients:List[Client]=[]
        self.version: int = version
        if clients:
            for client in clients:
                self.add_existing_client(client)




    def _validate_client_name_unique(self, name: str):
        """Validate that client name is unique"""
        if name in self.clients:
            raise ItemAlreadyExistsError(name)

    def _validate_client_id_unique(self, client_id: int):
        """Validate that client ID is unique"""
        if client_id in self.clients_by_id:
            raise ItemAlreadyExistsError(f"Client ID {client_id} already exists")

    def create_client(self, client_id: int, name: str, admin_id: int, address: str="", phones:str="", emails:str="",enabled: bool = True) -> Client:
        """Create a new client (only called by Admin domain service)"""

        try:
            client = Client(
                client_id=client_id,
                name=ClientName(name),
                phones=Phones(phones=phones),
                emails=Emails(emails=emails),
                address=Address(address=address),
                admin_id=admin_id,  # Fixed creator admin
                enabled=enabled
            )


            self._validate_client_name_unique(client.name)

            self.version += 1
            self.add_existing_client(client)

            return client

        except ItemValidationError:
            return Client.empty_client()

    def add_existing_client(self, client: Client):
        """Add an existing client to the aggregate"""
        self.clients[client.name] = client
        if client.client_id:
            self.clients_by_id[client.client_id] = client
        else:
            self.new_clients.append(client)


    def get_client_by_name(self, name: str) -> Client:
        """Get client by unique name - returns ClientEmpty if not found"""
        try:
            return self.clients.get(name)
        except KeyError:
            raise ItemNotFoundError(item_name=name)

    def get_client_by_id(self, client_id: int) -> Client:
        """Get client by ID - returns ClientEmpty if not found"""
        try:
            return self.clients_by_id.get(client_id)
        except KeyError:
            raise ItemNotFoundError(item_name=str(client_id))


    def get_new_clients(self) ->List[Client]:
        return self.new_clients

    def client_exists(self, name: str) -> bool:
        """Check if client with given name exists"""
        return name in self.clients

    def update_client_address(self, client_id: int, new_address: str):
        """Update client address (can be done by any admin)"""
        client = self.get_client_by_id(client_id)
        validated_address = self._validate_address(new_address)
        client.update_address(validated_address)
        self.version += 1

    def set_client_status(self, client_name: str, enabled: bool):
        """Enable/disable client (can be done by any admin)"""
        client = self.require_client_by_name(client_name)
        client.set_enabled(enabled)
        self.version += 1

    def toggle_client_status(self, client_name: str):
        """Toggle client enabled status"""
        client = self.require_client_by_name(client_name)
        client.set_enabled(not client.enabled)
        self.version += 1

    def remove_client(self, client_name: str):
        """Remove client by name"""
        client = self.require_client_by_name(client_name)
        del self.clients[client.name_of_client]
        del self.clients_by_id[client.client_id]
        self.version += 1

    def get_clients_by_admin(self, admin_id: int) -> List[Client]:
        """Get all clients created by a specific admin"""
        return [client for client in self.get_all_clients() if client.admin_id == admin_id]

    def get_all_clients(self) -> List[Client]:
        """Get all real clients (exclude empty ones)"""
        return [client for client in self.clients.values() if not client.is_empty()]

    def get_enabled_clients(self) -> List[Client]:
        return [client for client in self.get_all_clients() if client.enabled]

    def get_disabled_clients(self) -> List[Client]:
        return [client for client in self.get_all_clients() if not client.enabled]

    def get_client_count(self) -> int:
        return len(self.get_all_clients())

    def is_empty(self) -> bool:
        return self.get_client_count() == 0
