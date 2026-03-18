# src/domain/uow/unit_of_work.py
from abc import ABC, abstractmethod
from typing import ContextManager, Self

from src.domain.rbac.permissions import AdminPermission, UserPermission
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
    roles_admin:RoleRepository[AdminPermission]
    roles_user:RoleRepository[UserPermission]
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




