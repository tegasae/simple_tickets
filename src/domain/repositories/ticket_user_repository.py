# src/domain/repositories/ticket_user_repository.py

from abc import ABC, abstractmethod

from src.domain.ticket_user import TicketUser


class TicketUserRepository(ABC):
    """
    Repository interface for TicketUser aggregate.
    """

    # --------------------------------
    # Reads
    # --------------------------------

    @abstractmethod
    def get(
        self,
        ticket_id: int,
    ) -> TicketUser:
        raise NotImplementedError

    @abstractmethod
    def get_all(
        self,
    ) -> list[TicketUser]:
        raise NotImplementedError

    # --------------------------------
    # Persistence
    # --------------------------------

    @abstractmethod
    def save(
        self,
        ticket: TicketUser,
    ) -> TicketUser:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        ticket_id: int,
    ) -> None:
        raise NotImplementedError

    # --------------------------------
    # Reference checks
    # --------------------------------

    @abstractmethod
    def does_client_exist(
        self,
        client_id: int,
    ) -> bool:
        """
        Returns True when at least one TicketUser
        belongs to client_id.

        Historical method name is preserved
        for compatibility.
        """
        raise NotImplementedError

    @abstractmethod
    def has_admin_reference(
        self,
        admin_id: int,
    ) -> bool:
        """
        Returns True when Admin is referenced
        by TicketUser aggregate data.

        Used before deleting Admin.
        """
        raise NotImplementedError

    @abstractmethod
    def has_user_reference(
        self,
        user_id: int,
    ) -> bool:
        """
        Returns True when User is referenced
        by TicketUser aggregate data.

        Used before deleting User.
        """
        raise NotImplementedError