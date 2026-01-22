


from src.domain.clients import Client
from src.domain.exceptions import ItemNotFoundError

from src.domain.permissions.rbac import Permission
from src.domain.services.clients_admins import AdminClientManagementService
from src.services.service_layer.base import BaseService
from src.services.service_layer.data import CreateClientData


class ClientService(BaseService[Client]):
    def __init__(self, uow):
        super().__init__(uow)

        self.operation_methods = {
            'create': self._create_client,
            'get_by_name': self._get_client_by_name,
            'get_by_id': self._get_client_by_id,
            'update_email': self._update_client_email,
            #'change_status': self._change_client_status,
            #'update_phones': self._update_client_phones,
            #'update_address':self._update_client_address,
            #'update_name': self._update_client_name,
            #'change_admin': self._change_admin,
            #'remove_by_id': self._remove_admin_by_id
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

    def _get_client_by_name(self, name: str) -> list[Client]:
        return [c for c in self.uow.clients_repository.get_all_clients() if c.name == name]

    def _get_client_by_id(self, client_id: int) -> Client:
        clients=self.uow.clients_repository.get_all_clients()
        for c in clients:
            if c.client_id==client_id:
                return c
        raise ItemNotFoundError(item_name=f"{client_id}")


    def _update_client_email(self,requesting_admin_id: int, client_id: int, new_email:str):
        with self._with_admin_operation(
                requesting_admin_id=requesting_admin_id,
                permission=Permission.UPDATE_CLIENT,
                operation_name="update_client"
        ) as aggregate:
            client=self._get_client_by_id(client_id=client_id)
            s = self.service(admins_aggregate=aggregate,client=client)
            client=s.update_client(emails=new_email)

            self.uow.clients_repository.save_client(client)

            return client

    # Bulk operations
    #def list_all_clients(self) -> list[Client]:


    #def list_enabled_clients(self) -> list[Client]:


    #def client_exists(self, name: str) -> bool:


