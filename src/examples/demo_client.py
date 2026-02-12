from src.adapters.repository_memory import InMemoryClientRepo
from src.domain.services.client import ClientService

if __name__=="__main__":
    clients_repository=InMemoryClientRepo()
    client_service=ClientService(clients=clients_repository)
    client=client_service.create_client(client_id=1,created_by_admin_id=1,name="name")
    print(client)
    client=clients_repository.get(client_id=1)
    print(client.created_by_admin_id)
    print(clients_repository.get_all())