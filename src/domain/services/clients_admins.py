from src.domain.clients import Client
from src.domain.exceptions import DomainOperationError
from src.domain.model import AdminsAggregate
from src.domain.value_objects import ClientName, Emails, Address, Phones

class AdminClientManagementService:
    def __init__(self,admins_aggregate: AdminsAggregate, client: Client=Client.empty_client()):
        self.admins_aggregate=admins_aggregate
        self.client=client

    def delete_client(self):
        if not self.client.is_empty and not self.client.is_deleted:
            raise DomainOperationError(message=f"{self.client.name} already deleted")
        self.admins_aggregate.decrease_client(admin_id=self.client.admin_id)
        self.client.is_deleted = True


    def create_client(self, admin_id: int, name: str, emails: str, address: str, phones: str,
                  enabled: bool = True) -> Client:
        admin = self.admins_aggregate.get_admin_by_id(admin_id=admin_id)
        client = Client.create(admin_id=admin.admin_id, name=name, emails=emails, address=address, phones=phones,
                           enabled=enabled)
        self.admins_aggregate.increase_client(admin_id=admin.admin_id)
        self.client=client
        return client


    def update_client(self,name: str = "", emails: str = "",
                  address: str = "", phones: str = "", enabled: bool = True, admin_id: int = 0) -> Client:
        if not self.client.is_empty and self.client.is_deleted:
            raise DomainOperationError(message=f"{self.client.name} can't be update because it is already deleted")
        if name:
            self.client.name = ClientName(name)
        if emails:
            self.client.emails = Emails(emails)
        if address:
            self.client.address = Address(address)
        if phones:
            self.client.phones = Phones(phones)
        self.client.enabled = enabled
        if admin_id:
            admin = self.admins_aggregate.get_admin_by_id(admin_id=self.client.admin_id)
            if admin.admin_id != self.client.admin_id:
                self.admins_aggregate.increase_client(admin_id=admin.admin_id)
                self.admins_aggregate.decrease_client(admin_id=self.client.admin_id)
                self.client.admin_id = admin.admin_id
        return self.client
