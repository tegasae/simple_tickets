from abc import ABC, abstractmethod

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

    # ----------------------------
    # Persistence
    # ----------------------------

    @abstractmethod
    def save(self, ticket: Ticket) -> Ticket:
        raise NotImplementedError

    @abstractmethod
    def delete(self, ticket_id: int) -> None:
        raise NotImplementedError