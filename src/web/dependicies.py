from fastapi import Depends
import sqlite3

from config import settings
from src.services.service_layer.factory import ServiceFactory  # Fixed import
from src.services.uow.uowsqlite import SqliteUnitOfWork  # Add this import
from utils.db.connect import Connection




def get_db_connection():
    """Get database connection"""
    conn = None
    try:
        conn = Connection.create_connection(
            url="admins.db",  # Fixed path
            engine=sqlite3
        )
        yield conn
    finally:
        if conn:
            conn.close()


def get_uow(conn: Connection = Depends(get_db_connection)):
    """Get Unit of Work"""
    return SqliteUnitOfWork(connection=conn)


def get_service_factory(uow: SqliteUnitOfWork = Depends(get_uow)):
    """Get service factory"""
    return ServiceFactory(uow=uow)


