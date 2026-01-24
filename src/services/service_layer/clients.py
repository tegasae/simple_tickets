#service/client.py


from src.domain.clients import Client


from src.domain.permissions.rbac import Permission
from src.domain.services.clients_admins import AdminClientManagementService
from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateClientData


class ClientService(BaseService[Client]):
    def __init__(self, uow):
        super().__init__(uow)


        self.operation_methods = {
            'create': self._create_client,
            'update_email': self._update_client_email,
            'change_status': self._change_client_status,
            'update_phones': self._update_client_phones,
            'update_address':self._update_client_address,
            'update_name': self._update_client_name,
            'change_admin': self._change_client_admin,
            'remove_by_id': self._remove_admin_by_id
        }
        self.service=AdminClientManagementService


    def _create_client(self, requesting_admin_id: int, create_client_data: CreateClientData) -> Client:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.CREATE_CLIENT,
                operation_name="create_client"
        ) as aggregate:
            # Create admin

            s=self.service(admins_aggregate=aggregate)

            if create_client_data.admin_id:
                admin_id=create_client_data.admin_id
            else:
                admin_id=requesting_admin_id
            client=s.create_client(admin_id=admin_id,name=create_client_data.name,emails=create_client_data.email,address=create_client_data.email,phones=create_client_data.phones,enabled=create_client_data.enabled)
            # Verify ID was generated
            self.uow.clients_repository.save_client(client)

            return client

    def get_client_by_name(self, name: str) -> list[Client]:
        return [c for c in self.uow.clients_repository.get_all_clients() if c.name == name]

    def get_client_by_id(self, client_id: int) -> Client:
        client=self.uow.clients_repository.get_client_by_id(client_id=client_id)
        return client


    def get_all_clients(self) -> list[Client]:
        return self.uow.clients_repository.get_all_clients()


    def _update_client_email(self,requesting_admin_id: int, client_id: int, new_email:str)->Client:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="update_client"
        ) as aggregate:
            client=self.get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate,client=client)
            client=s.update_client(emails=new_email)

            self.uow.clients_repository.save_client(client)

            return client

    def _change_client_status(self,requesting_admin_id: int, client_id: int, enabled:bool)->Client:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="change_status_client"
        ) as aggregate:
            client=self.get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate, client=client)
            client=s.update_client(enabled=enabled)
            self.uow.clients_repository.save_client(client)
            return client

    def _update_client_phones(self,requesting_admin_id: int, client_id: int, phones:str)->Client:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="change_phones_client"
        ) as aggregate:
            client=self.get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate, client=client)
            client=s.update_client(phones=phones)
            self.uow.clients_repository.save_client(client)
            return client

    def _update_client_address(self, requesting_admin_id: int, client_id: int, address: str)->Client:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="change_address_client"
        ) as aggregate:
            client = self.get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate, client=client)
            client = s.update_client(address=address)
            self.uow.clients_repository.save_client(client)
            return client

    def _update_client_name(self, requesting_admin_id: int, client_id: int, name: str)->Client:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="update_name_client"
        ) as aggregate:
            client = self.get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate, client=client)
            client = s.update_client(name=name)
            self.uow.clients_repository.save_client(client)
            return client

    def _change_client_admin(self, requesting_admin_id: int, client_id: int, admin_id:int=0)->Client:
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="update_name_client"
        ) as aggregate:
            client = self.get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate, client=client)
            if admin_id==0:
                admin_id=requesting_admin_id
            client = s.update_client(admin_id=admin_id)
            self.uow.clients_repository.save_client(client)
            return client

    def _remove_admin_by_id(self,requesting_admin_id: int, client_id: int):
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="update_name_client"
        ) as aggregate:
            client = self.get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate, client=client)
            s.delete_client()

            self.uow.clients_repository.delete_client(client_id=client_id)


    # Bulk operations
    #def list_all_clients(self) -> list[Client]:


    #def list_enabled_clients(self) -> list[Client]:


    #def client_exists(self, name: str) -> bool:


