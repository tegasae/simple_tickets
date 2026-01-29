#web/dependencies/dependencies.py
from fastapi import Depends
import sqlite3


from src.services.service_layer.factory import ServiceFactory  # Fixed import
from src.services.uow.uowsqlite import SqliteUnitOfWork  # Add this import
from src.web.config import get_settings, Settings
from utils.db.connect import Connection


def get_db_connection():
    """Create connection in the same thread that uses it"""
    conn = None
    try:
        # This will be called in the worker thread
        conn = Connection.create_connection(url=get_settings().DATABASE_URL, engine=sqlite3)
        yield conn
    finally:
        if conn:
            conn.close()


# The rest of your dependencies stay the same
def get_uow(conn: Connection = Depends(get_db_connection)):
    return SqliteUnitOfWork(connection=conn)


def get_service_factory(uow: SqliteUnitOfWork = Depends(get_uow)):
    return ServiceFactory(uow=uow)




def get_app_settings() -> Settings:
    return get_settings()
