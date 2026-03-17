# src/adapters/uow/sqlite_unit_of_work.py

import sqlite3

from src.adapters.repositories.admin import AdminRepositorySQLite
from src.adapters.repositories.client_repository import ClientRepositorySQLite
from src.adapters.repositories.role_repository import RoleRepositorySQLite
from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
from src.adapters.repositories.ticket_user_repository import TicketUserRepositorySQLite
from src.adapters.repositories.user_repository import UserRepositorySQLite
from src.services.uow.uow import UnitOfWork



from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError


class SQLiteUnitOfWork(UnitOfWork):
    """
    SQLite implementation of UnitOfWork.

    Responsibilities:
        - manage DB connection
        - initialize repositories
        - control transactions
    """

    def __init__(self, db_url: str):
        self._db_url = db_url
        self.conn: Connection | None = None

        # repositories (initialized in __enter__)
        self.admins = None
        self.users = None
        self.clients = None
        self.tickets = None
        self.user_tickets = None
        self.roles = None

    # --------------------------------
    # Context manager
    # --------------------------------

    def __enter__(self):
        try:
            self.conn = Connection.create_connection(
                url=self._db_url,
                engine=sqlite3,
            )

            self.conn.begin_transaction()

            # init repositories
            self.admins = AdminRepositorySQLite(self.conn)
            self.users = UserRepositorySQLite(self.conn)
            self.clients = ClientRepositorySQLite(self.conn)
            self.tickets = TicketRepositorySQLite(self.conn)
            self.user_tickets = TicketUserRepositorySQLite(self.conn)
            self.roles = RoleRepositorySQLite(self.conn)

            return super().__enter__()

        except Exception as e:
            raise DBOperationError(f"Failed to initialize UnitOfWork: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            if self.conn:
                self.conn.close()

    # --------------------------------
    # Transaction control
    # --------------------------------

    def commit(self):
        if not self.conn:
            raise DBOperationError("Connection is not initialized")
        self.conn.commit()

    def rollback(self):
        if not self.conn:
            raise DBOperationError("Connection is not initialized")
        self.conn.rollback()