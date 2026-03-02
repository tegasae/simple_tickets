import sqlite3

from src.adapters.repository_memory import InMemoryClientRepo
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.client import ClientService
from utils.db.connect import Connection

if __name__=="__main__":
    clients_repository=InMemoryClientRepo()
    conn1 = Connection.create_connection(url="../../db/admins.db", engine=sqlite3)
    user_repository = UserRepositorySQLite(conn=conn1)
    client_service=ClientService(client_repository=clients_repository,user_repository=user_repository)
    client=client_service.create(client_id=1,created_by_admin_id=1,name="name")
    print(client)
    client=clients_repository.get(client_id=1)
    print(client.created_by_admin_id)
    print(clients_repository.get_all())