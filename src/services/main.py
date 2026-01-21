import sqlite3

from src.adapters.repositorysqlite import SQLiteAdminRepository
from src.services.service_layer.admins import AdminService
from src.services.uow.uowsqlite import SqliteUnitOfWork
from utils.db.connect import Connection

if __name__=="__main__":
    connect=Connection.create_connection(url="../../db/admins.db",engine=sqlite3)
    repository=SQLiteAdminRepository(conn=connect)
    admins=repository.get_list_of_admins()
    print(admins.admins)
    admin_service=AdminService(uow=SqliteUnitOfWork(connection=connect))
    list_all_admins=admin_service.list_all_admins()
    print(list_all_admins)
    admin_service.execute(requesting_admin_id=2,operation='toggle_status',target_admin_id=3)
    connect.close()