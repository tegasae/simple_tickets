import sqlite3

from src.adapters.repositories.admin import AdminRepositorySQLite
from src.adapters.repositories.client_repository import ClientRepositorySQLite
from src.adapters.repositories.user_repository import UserRepositorySQLite
from src.services.uow.uow import UnitOfWork
from utils.db.connect import Connection


class SQLiteUnitOfWork(UnitOfWork):

    def __init__(self, db_url: str):

        self.connection = Connection.create_connection(
            url=db_url,
            engine=sqlite3
        )

        self.admins = AdminRepositorySQLite(self.connection)
        self.users = UserRepositorySQLite(self.connection)
        self.clients = ClientRepositorySQLite(self.connection)

    def __enter__(self):

        self.connection.begin_transaction()
        return super().__enter__()

    def __exit__(self, exc_type, exc, tb):

        if exc_type is None:
            self.commit()
        else:
            self.rollback()

        self.connection.close()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()