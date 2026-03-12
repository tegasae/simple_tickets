from abc import ABC, abstractmethod
from src.domain.ticket_user import TicketUser


class TicketUserRepository(ABC):

    @abstractmethod
    def get(self, ticket_id: int) -> TicketUser:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[TicketUser]:
        raise NotImplementedError

    @abstractmethod
    def save(self, ticket: TicketUser) -> TicketUser:
        raise NotImplementedError

    @abstractmethod
    def delete(self, ticket_id: int) -> None:
        raise NotImplementedError