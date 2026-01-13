import sqlite3

from src.adapters.repositorysqlite import SQLiteAdminRepository
from utils.db.connect import Connection

if __name__=="__main__":
    conn=Connection.create_connection(url="../../db/admins.db",engine=sqlite3)
    repository=SQLiteAdminRepository(conn=conn)
    admins=repository.get_list_of_admins()
    print(admins.admins)
    conn.close()