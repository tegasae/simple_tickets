#domain/services/clients_admin.py
from src.domain.client import Client
from src.domain.exceptions import DomainOperationError

from src.domain.value_objects import Name, Email, Address, Phone

class AdminClientManagementService:
    def __init__(self,client: Client=Client.empty_client()):

        self.client=client

    def delete_client(self):
        if not self.client.is_empty and not self.client.is_deleted:
            raise DomainOperationError(message=f"{self.client.name} already deleted")
        self.client.is_deleted = True


    def create_client(self, admin_id: int, name: str, emails: str, address: str, phones: str,
                  enabled: bool = True) -> Client:
        client = Client.create(admin_id=admin_id, name=name, emails=emails, address=address, phones=phones,
                           enabled=enabled)
        self.client=client
        return client


    def update_client(self,name: str = "", emails: str = "",
                  address: str = "", phones: str = "", enabled: bool = True, admin_id: int = 0) -> Client:
        if not self.client.is_empty and self.client.is_deleted:
            raise DomainOperationError(message=f"{self.client.name} can't be update because it is already deleted")
        if name:
            self.client.name = Name(name)
        if emails:
            self.client.email = Email(emails)
        if address:
            self.client.address = Address(address)
        if phones:
            self.client.phone = Phone(phones)
        self.client.enabled = enabled
        if admin_id:
                self.client.admin_id = admin_id
        return self.client
