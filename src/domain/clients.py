#clients.py
from dataclasses import dataclass, field
from datetime import datetime


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
    _is_empty: bool = field(default=False, init=False, repr=False)


    @property
    def is_empty(self) -> bool:
        return self._is_empty

    @classmethod
    def empty_client(cls):
        c=cls(client_id=0, name=ClientName("----"), admin_id=0,
                   phones=Phones(),address=Address(),emails=Emails(),enabled=False)
        c._is_empty=True
        return c




class ClientsAggregate:
    def __init__(self, clients: list[Client] = None, version: int = 0):
        self.clients: dict[str, Client] = {}  # Index by unique name
        self.clients_by_id: dict[int, Client] = {}  # Index by ID



        self.version: int = version
        if clients:
            for client in clients:
                self._put_clients(client)


    def _put_clients(self, client: Client)->Client:
        if self._get_client_by_name(client.name.value).is_empty:
            self.clients[client.name.value.lower()] = client
            if client.client_id:
                self.clients_by_id[client.client_id] = client
            return client
        else:
            return Client.empty_client()

    def _get_client_by_id(self, client_id: int)->Client:
        return self.clients_by_id.get(client_id,Client.empty_client())

    def _get_client_by_name(self, name: str)->Client:
        return self.clients.get(name,Client.empty_client())




    def create_client(self, client_id: int, name: str, admin_id: int, address: str="", phones:str="", emails:str="",enabled: bool = True) -> Client:
        """Create a new client (only called by Admin domain service)"""
        # Check if name already exists
        if self.client_exists(name):
            raise ItemAlreadyExistsError(item_name=name)

        try:
            client = Client(
                client_id=client_id,
                name=ClientName(name),
                phones=Phones(phones),
                emails=Emails(emails),
                address=Address(address),
                admin_id=admin_id,  # Fixed creator admin
                enabled=enabled
            )
            c=self._put_clients(client)
            if not c.is_empty:
                self.version+=1
            else:
                raise ItemAlreadyExistsError(item_name=name)
            return c
        except ItemValidationError:
            raise

    def get_client_by_name(self, name: str) -> Client:
        """Get client by unique name - returns ClientEmpty if not found"""
        return self._get_client_by_name(name)

    def get_client_by_id(self, client_id: int) -> Client:
        """Get client by ID - returns ClientEmpty if not found"""
        client=self._get_client_by_id(client_id)
        if client.is_empty:
            raise ItemNotFoundError(item_name=str(client_id))
        return client

    def get_new_clients(self) ->list[Client]:
        return [client for client in self.clients.values() if client.client_id == 0]


    def client_exists(self, name: str) -> bool:
        """Check if client with given name exists"""
        return not self._get_client_by_name(name).is_empty

    def update_client_address(self, client_id: int, new_address: str,new_emails:str,new_phones:str):
        """Update client address (can be done by any admin)"""
        try:
            client = self._get_client_by_id(client_id)
            if client.is_empty:
                raise ItemNotFoundError(item_name=str(client_id))
            if new_address:
                client.address=Address(new_address)

            if new_emails:
                client.emails=Emails(new_emails)

            if new_phones:
                client.phones=Phones(new_phones)

            self.version += 1
        except ValueError:
            raise ItemValidationError(message=f"This item is wrong {new_address}")

    def set_client_status(self, client_id: int, enabled: bool):
        """Enable/disable client (can be done by any admin)"""
        client = self._get_client_by_id(client_id)
        if client.is_empty:
            raise ItemNotFoundError(item_name=str(client_id))

        client.enabled=enabled
        self.version += 1

    def toggle_client_status(self, client_id: int):
        """Toggle client enabled status"""
        client = self._get_client_by_id(client_id)
        if client.is_empty:
            raise ItemNotFoundError(item_name=str(client_id))

        client.enabled=not client.enabled
        self.version += 1


    #Надо доделать. Учитываем, что client может быть в отедльном хранилище с нулевым id, его отуда тоже надо вытщить.
    # Или просто не хранить в отедльном хранилище
    #а когда понадобится все client с нулевым id просто их вытащить из словара с поиском по id==0
    def remove_client(self, client_id: int):
        """Remove client by name"""
        client = self.get_client_by_id(client_id)
        if client.is_empty:
            raise ItemNotFoundError(item_name=str(client_id))
        try:
            del self.clients[client.name.value]
            self.version += 1
        except KeyError:
            raise ItemNotFoundError(item_name=str(client_id))

        try:
            del self.clients_by_id[client.client_id]
        except KeyError:
            pass



    def get_clients_by_admin(self, admin_id: int) -> list[Client]:
        """Get all clients created by a specific admin"""
        return [client for client in self.get_all_clients() if client.admin_id == admin_id]

    def get_all_clients(self) -> list[Client]:
        """Get all real clients (exclude empty ones)"""
        return [client for client in self.clients.values() if not client.is_empty]

    def get_enabled_clients(self) -> list[Client]:
        return [client for client in self.get_all_clients() if client.enabled]

    def get_disabled_clients(self) -> list[Client]:
        return [client for client in self.get_all_clients() if not client.enabled]

    def get_client_count(self) -> int:
        return len(self.get_all_clients())

    def is_empty(self) -> bool:
        return self.get_client_count() == 0

if __name__=="__main__":
    print("1")