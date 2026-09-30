# src/domain/repositories/ticket_user_repository.py

from abc import ABC, abstractmethod

from src.domain.ticket_user import TicketUser


class TicketUserRepository(ABC):
    """
    Repository interface for TicketUser aggregate.
    """

    # ==================================================================
    # Reads
    # ==================================================================

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
        """
        Return all TicketUser aggregates.

        Kept as a simple general-purpose method while the number of
        requests remains small.
        """

        raise NotImplementedError

    @abstractmetho
    def get_by_user_id(
        self,
        user_id: int,
    ) -> list[TicketUser]:
        """
        Return all requests belonging to the specified User.

        Both open and closed requests are returned.
        """

        raise NotImplementedError



    @abstractmethod
    def get_by_client_id(
        self,
        client_id: int,
    ) -> list[TicketUser]:
        """
        Return all requests belonging to the specified Client.

        Both open and closed requests are returned.
        """

        raise NotImplementedError

    @abstractmethod
    def get_open_by_user_id(
            self,
            user_id: int,
    ) -> list[TicketUser]:


        raise NotImplementedError



    @abstractmethod
    def get_open_by_client_id(
            self,
            client_id: int,
    ) -> list[TicketUser]:


        raise NotImplementedError

    @abstractmethod
    def get_finished_by_user_id(
        self,
        user_id: int,
    ) -> list[TicketUser]:
        """
        Return closed requests belonging to the specified User.

        Persistence may use:

            date_finished IS NOT NULL
        """

        raise NotImplementedError

    @abstractmethod
    def get_finished_by_client_id(
        self,
        client_id: int,
    ) -> list[TicketUser]:
        """
        Return closed requests belonging to the specified Client.

        Persistence may use:

            client_id = ?
            AND date_finished IS NOT NULL
        """

        raise NotImplementedError

    # ==================================================================
    # Persistence
    # ==================================================================

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

    # ==================================================================
    # Reference checks
    # ==================================================================

    @abstractmethod
    def does_client_exist(
        self,
        client_id: int,
    ) -> bool:
        """
        Return True when at least one TicketUser belongs to client_id.

        Historical method name is preserved for compatibility.
        """

        raise NotImplementedError

    @abstractmethod
    def has_admin_reference(
        self,
        admin_id: int,
    ) -> bool:
        """
        Return True when Admin is referenced by TicketUser aggregate data.

        Used before deleting Admin.
        """

        raise NotImplementedError

    @abstractmethod
    def has_user_reference(
        self,
        user_id: int,
    ) -> bool:
        """
        Return True when User is referenced by TicketUser aggregate data.

        Used before deleting User.
        """

        raise NotImplementedError

    @abstractmethod
    def touch(
            self,
            ticket: TicketUser,
    ) -> None:
        raise NotImplementedError