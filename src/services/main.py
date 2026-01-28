import sqlite3
import datetime
from src.adapters.repositorysqlite import SQLiteAdminRepository
from src.services.service_layer.admins import AdminService
from src.services.service_layer.clients import ClientService
from src.services.service_layer.data import CreateClientData, CreateAdminData
from src.services.uow.uowsqlite import SqliteUnitOfWork
from utils.db.connect import Connection

if __name__=="__main__":
    connect=Connection.create_connection(url="../../db/admins.db",engine=sqlite3)
    repository=SQLiteAdminRepository(conn=connect)
    admins=repository.get_list_of_admins()

    #print(admins.admins)
    admin_service= AdminService(uow=SqliteUnitOfWork(connection=connect))
    create_data = CreateAdminData(
        name='string1111111111112221'+datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        email="email@email.email",
        password='1234567890',
        enabled=True,
        roles={}
    )

    # Create admin
    list_all_admins = admin_service.list_all_admins()
    print(len(list_all_admins))

    admin = admin_service.create_admin(requesting_admin_id=1,create_admin_data=create_data)
    print(admin)
    # Convert to view model
    admin=admin_service.update_admin_email(requesting_admin_id=1,target_admin_id=admin.admin_id,new_email="EMAIL@1.11")
    print(admin)
    admin_service.remove_admin_by_id(requesting_admin_id=1, target_admin_id=admin.admin_id)

    list_all_admins = admin_service.list_all_admins()
    print(len(list_all_admins))

    client_service=ClientService(uow=SqliteUnitOfWork(connection=connect))

    #print(list_all_admins)
    #admin_service.execute(requesting_admin_id=2,operation='toggle_status',target_admin_id=1)
    #admin_service.execute(requesting_admin_id=2, operation='change_password', target_admin_id=1,new_password='1234567890')
    #print(admin_service._get_admin_by_id(admin_id=3))
    #create_client_data=CreateClientData(name="name1",address="address1",email="email1",phones="phones1")
    #client_service.create_client(requesting_admin_id=1,create_client_data=create_client_data)
    #client=client_service.execute(requesting_admin_id=2,operation='create',create_client_data=create_client_data)

    #print(client)
    #clients=client_service.get_all_clients()
    #print(clients)
    #client=client_service.get_client_by_id(client_id=7)
    #print(client)

    #client=client_service.execute(requesting_admin_id=2,operation='change_status',client_id=7,enabled=True)
    #client_service.execute(requesting_admin_id=2,operation='change_admin',client_id=7)
    #print(client)
    #client = client_service.get_client_by_id(client_id=7)
    #print(client)
    connect.close()