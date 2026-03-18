# src/adapters/uow/sqlite_unit_of_work.py
import logging

from typing import Self

from src.adapters.repositories.admin import AdminRepositorySQLite
from src.adapters.repositories.client_repository import ClientRepositorySQLite
from src.adapters.repositories.role_repository import RoleRepositorySQLite
from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
from src.adapters.repositories.ticket_user_repository import TicketUserRepositorySQLite
from src.adapters.repositories.user_repository import UserRepositorySQLite
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.services.uow.uow import UnitOfWork



from utils.db.connect import Connection
logger = logging.getLogger(__name__)

class SQLiteUnitOfWork(UnitOfWork):
    """
    SQLite implementation of UnitOfWork.

    Responsibilities:
        - manage DB connection
        - initialize repositories
        - control transactions
    """


    def __init__(self, connection:Connection):
        self.connection: Connection =connection
        self._active = False
        self._committed = False
        # repositories (initialized in __enter__)
        self.admins = AdminRepositorySQLite(conn=self.connection)
        self.users = UserRepositorySQLite(conn=self.connection)
        self.clients = ClientRepositorySQLite(conn=self.connection)
        self.tickets = TicketRepositorySQLite(conn=self.connection)
        self.user_tickets = TicketUserRepositorySQLite(conn=self.connection)
        self.roles_admin =  RoleRepositorySQLite(conn=self.connection,permission_cls=AdminPermission,is_admin=True)
        self.roles_user = RoleRepositorySQLite(conn=self.connection, permission_cls=UserPermission, is_admin=False)

    # --------------------------------
    # Context manager
    # --------------------------------

    def __enter__(self) -> Self:
        """Start SQLite transaction"""
        if self._active:
            raise RuntimeError("Already in a transaction - cannot nest context managers")
        self.connection.begin_transaction()
        self._active = True
        self._committed = False
        logger.debug("SQLite transaction started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Handle SQLite transaction completion"""

        try:
            if exc_type is not None:
                # Exception occurred - auto rollback
                self.rollback()
                logger.debug("Auto-rollback due to exception")
                raise
            else:
                if  self._committed:
                    self.commit()
                    logger.warning("Commited")
                else:
                    # No explicit commit - safety rollback
                    self.rollback()
                    logger.warning("Auto-rollback: no commit called")
            return True
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
            # Don't mask original exception
            if exc_type is None:
                raise
        finally:  # ✅ Add this to ensure _active is always set to False
            self._active = False
            return False
        #return False  # Re-raise original exception


    # --------------------------------
    # Transaction control
    # --------------------------------

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


    def is_active(self) -> bool:
        """Check if SQLite transaction is active"""
        return self._active
