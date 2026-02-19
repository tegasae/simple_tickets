import sqlite3
from datetime import datetime

from src.adapters.repositories.account import AccountRepositorySQLite
from src.adapters.repositories.admin import AdminRepositorySQLite
from src.domain.employee import Admin
from src.domain.services.admin import AdminService
from utils.db.connect import Connection

if __name__=="__main__":
    conn1=Connection.create_connection(url="../../db/admins.db",engine=sqlite3)
    admin_repository=AdminRepositorySQLite(conn=conn1)
    account_repository=AccountRepositorySQLite(conn=conn1)


    conn1.begin_transaction()

    admin_service=AdminService(admin_repository=admin_repository,account_repository=account_repository)
    admin=admin_service.create_admin(admin_id=0,first_name="first_name",last_name="last_name",login="login1",password="password1234567890@T")


    conn1.commit()
    conn1.close()