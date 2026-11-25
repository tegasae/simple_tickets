# src/domain/uow/unit_of_work.py

from abc import ABC, abstractmethod
from contextlib import nullcontext
from types import TracebackType
from typing import ContextManager, Self

from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_repository import RoleRepository
from src.domain.repositories.admin_repository import AdminRepository
from src.domain.repositories.creation_result_repository import CreationResultRepository
from src.domain.repositories.client_repository import ClientRepository
from src.domain.repositories.department_repository import (
    DepartmentRepository,
)
from src.domain.repositories.refresh_session_repository import RefreshSessionRepository
from src.domain.repositories.ticket_repository import TicketRepository
from src.domain.repositories.ticket_user_repository import (
    TicketUserRepository,
)
from src.domain.repositories.user_repository import UserRepository


class UnitOfWork(ContextManager[Self], ABC):
    """
    Abstract Unit of Work.

    Responsibilities:
        - provide access to repositories;
        - define transaction boundaries;
        - commit or rollback one atomic application operation.
    """

    admins: AdminRepository
    users: UserRepository
    clients: ClientRepository
    tickets: TicketRepository
    user_tickets: TicketUserRepository
    departments: DepartmentRepository
    creation_results: CreationResultRepository
    refresh_sessions: RefreshSessionRepository

    roles_admin: RoleRepository[AdminPermission]
    roles_user: RoleRepository[UserPermission]

    # --------------------------------
    # Context manager
    # --------------------------------

    @abstractmethod
    def __enter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """
        Return False so exceptions from the with-block propagate.
        """
        raise NotImplementedError

    # --------------------------------
    # Transaction control
    # --------------------------------

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_active(self) -> bool:
        """Return True while the UnitOfWork owns an active transaction."""
        raise NotImplementedError

    def transaction(self, *, join: bool = False) -> ContextManager[Self]:
        """Join only when the command passes ownership explicitly."""
        if not join:
            return self
        if not self.is_active():
            raise RuntimeError("An active UnitOfWork is required")
        return nullcontext(self)
