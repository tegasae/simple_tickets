import sqlite3
import datetime
from src.adapters.repositorysqlite import SQLiteAdminRepository
from src.services.service_layer.admins import AdminService
from src.services.service_layer.clients import ClientService
from src.services.service_layer.data import CreateClientData, CreateAdminData
from src.services.service_layer.factory import ServiceFactory
from src.services.uow.uowsqlite import SqliteUnitOfWork
from utils.db.connect import Connection

if __name__ == "__main__":
    connect = Connection.create_connection(url="../../db/admins.db", engine=sqlite3)
    repository = SQLiteAdminRepository(conn=connect)
    admins = repository.get_list_of_admins()
    sf = ServiceFactory(uow=SqliteUnitOfWork(connection=connect), admin_name="name")
    client_service = sf.get_client_service()
    client_service.create_client(create_client_data=CreateClientData(name="name",email="email",address="address",phones="1",admin_id=1))

    connect.close()