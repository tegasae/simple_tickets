# src/domain/uow/unit_of_work.py
from abc import ABC, abstractmethod
from typing import ContextManager, Self

from src.domain.rbac.role_repository import RoleRepository
from src.domain.repositories.admin_repository import AdminRepository
from src.domain.repositories.ticket_user_repository import TicketUserRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.repositories.client_repository import ClientRepository
from src.domain.repositories.ticket_repository import TicketRepository

class UnitOfWork(ContextManager, ABC):
    """
    Abstract Unit of Work.

    Responsibilities:
        - provide access to repositories
        - manage transaction boundaries
    """

    # repositories (set in concrete implementation)
    admins: AdminRepository
    users: UserRepository
    clients: ClientRepository
    tickets: TicketRepository
    user_tickets: TicketUserRepository
    roles: RoleRepository

    # --------------------------------
    # Context manager
    # --------------------------------

    def __enter__(self)->Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()

    # --------------------------------
    # Transaction control
    # --------------------------------

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError

    @abstractmethod
    def is_active(self) -> bool:
        """Check if transaction is active"""
        raise NotImplementedError




class SqliteUnitOfWork(AbstractUnitOfWork):
    """
    Concrete implementation for SQLite database
    Inherits from AbstractUnitOfWork and implements all abstract methods
    """

    def __init__(self, connection:Connection):
        self.connection = connection
        self._admins_repo = None
        self._active = False
        self._committed = False
        self.admins_repository = repositorysqlite.SQLiteAdminRepository(conn=self.connection)

    # ========== ContextManager Methods ==========
    def __enter__(self) -> 'SqliteUnitOfWork':
        """Start SQLite transaction"""
        if self._active:
            raise RuntimeError("Already in a transaction - cannot nest context managers")
        self.connection.begin_transaction()
        self._active = True
        self._committed = False
        logger.debug("SQLite transaction started")
        return self


    # ========== Business Methods ==========
    def commit(self) -> None:
        """Commit SQLite transaction"""
        if not self._active:
            raise RuntimeError("No active transaction to commit")

        self.connection.commit()
        self._committed = True
        logger.info("SQLite transaction committed")

    def rollback(self) -> None:
        """Rollback SQLite transaction"""
        if self._active:
            self.connection.rollback()
            self._committed = True  # Mark as handled
            logger.info("SQLite transaction rolled back")

    @property
    def admins(self)->repository.AdminRepositoryAbstract:

        # if self._admins_repo is None:
        #    from src.adapters.repository_sqlite import SQLiteAdminRepository
        #    self._admins_repo = SQLiteAdminRepository(self.connection)
        # return self._admins_repo
        return self.admins_repository

    def is_active(self) -> bool:
        """Check if SQLite transaction is active"""
        return self._active
if __name__=='__main__':
    # conn1 = Connection.create_connection(url=":memory:", engine=sqlite3)

    conn1 = Connection.create_connection(
        url='../../../db/admins.db',  # or "admins.db" for file-based
        engine=sqlite3
    )
    #db_creator = CreateDB(conn1)
    uow=SqliteUnitOfWork(connection=conn1)
    with uow:
        admins=uow.admins.get_list_of_admins()
        #raise ValueError()
        print(admins)
        uow.commit()
    conn1.close()
