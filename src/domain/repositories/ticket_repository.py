from abc import ABC, abstractmethod
from typing import Iterator

from src.domain.ticket import Ticket


class TicketRepository(ABC):
    """
    Abstract repository for Ticket aggregate.
    """

    # ----------------------------
    # Reads
    # ----------------------------

    @abstractmethod
    def get(self, ticket_id: int) -> Ticket:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Ticket]:
        raise NotImplementedError

    @abstractmethod
    def iter_active_by_client_id(
            self,
            *,
            client_id: int,
            batch_size: int = 500,
    ) -> Iterator[list[Ticket]]:
        """
        Iterate active tickets of one client in batches.

        Active means:
            - belongs to client_id;
            - not closed.

        More specific domain rules are checked later by workflow.
        """
        raise NotImplementedError
    """
    @abstractmethod
    def iter_by_current_executor_id(
            self,
            *,
            executor_employee_id: int,
            batch_size: int = 500,
    ) -> Iterator[list[Ticket]]:
       
        raise NotImplementedError


    """
    # ----------------------------
    # Persistence
    # ----------------------------

    @abstractmethod
    def save(self, ticket: Ticket) -> Ticket:
        raise NotImplementedError

    @abstractmethod
    def delete(self, ticket_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def does_client_exist(self, client_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def does_user_tickets_exist(self, user_ticket_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_by_user_ticket_id(self, user_ticket_id: int) -> Ticket:
        raise NotImplementedError

    @abstractmethod
    def has_admin_reference(self, admin_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_department_reference(self, department_id: int) -> bool:
        raise NotImplementedError