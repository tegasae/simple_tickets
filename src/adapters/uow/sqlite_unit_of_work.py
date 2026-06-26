# src/adapters/uow/sqlite_unit_of_work.py

from __future__ import annotations

import logging
from types import TracebackType
from typing import Self

from src.adapters.repositories.admin import AdminRepositorySQLite
from src.adapters.repositories.client_repository import (
    ClientRepositorySQLite,
)
from src.adapters.repositories.department_repository import (
    DepartmentRepositorySQLite,
)
from src.adapters.repositories.role_repository import (
    RoleRepositorySQLite,
)
from src.adapters.repositories.ticket_repository import (
    TicketRepositorySQLite,
)
from src.adapters.repositories.ticket_user_repository import (
    TicketUserRepositorySQLite,
)
from src.adapters.repositories.user_repository import (
    UserRepositorySQLite,
)
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.uow.unit_of_work import UnitOfWork
from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError

logger = logging.getLogger(__name__)


class SQLiteUnitOfWork(UnitOfWork):
    """
    SQLite implementation of UnitOfWork.

    One UnitOfWork owns one database transaction.
    All repositories use the same Connection.
    """

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

        self._active = False
        self._completed = False

        self.admins = AdminRepositorySQLite(conn=self.connection)
        self.users = UserRepositorySQLite(conn=self.connection)
        self.clients = ClientRepositorySQLite(conn=self.connection)
        self.tickets = TicketRepositorySQLite(conn=self.connection)
        self.user_tickets = TicketUserRepositorySQLite(
            conn=self.connection,
        )
        self.departments = DepartmentRepositorySQLite(
            conn=self.connection,
        )

        self.roles_admin = RoleRepositorySQLite(
            conn=self.connection,
            permission_cls=AdminPermission,
            is_admin=True,
        )
        self.roles_user = RoleRepositorySQLite(
            conn=self.connection,
            permission_cls=UserPermission,
            is_admin=False,
        )

    # --------------------------------
    # Context manager
    # --------------------------------

    def __enter__(self) -> Self:
        if self._active:
            raise RuntimeError(
                "Cannot nest SQLiteUnitOfWork contexts"
            )

        self.connection.begin_transaction()

        self._active = True
        self._completed = False

        logger.debug("SQLite transaction started")

        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> bool:
        """
        On successful exit:
            commits unless commit() or rollback() was already called.

        On exceptional exit:
            rolls back unless transaction was already completed.

        Returns False so the original exception propagates.
        """
        try:
            if exc_type is None:
                if not self._completed:
                    self.commit()
            elif not self._completed:
                try:
                    self.rollback()
                except DBOperationError:
                    logger.exception(
                        "Failed to roll back SQLite transaction "
                        "after an application exception"
                    )
        finally:
            self._active = False
            self._completed = False

        return False
    # --------------------------------
    # Transaction control
    # --------------------------------

    def commit(self) -> None:
        if not self._active:
            raise RuntimeError(
                "Cannot commit without an active UnitOfWork"
            )

        if self._completed:
            return

        self.connection.commit()

        self._completed = True

        logger.debug("SQLite transaction committed")

    def rollback(self) -> None:
        if not self._active:
            return

        if self._completed:
            return

        self.connection.rollback()

        self._completed = True

        logger.debug("SQLite transaction rolled back")

    def is_active(self) -> bool:
        return self._active and not self._completed