from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from src.domain.ticket import Ticket

@dataclass(frozen=True, kw_only=True)
class TicketSearchCriteria:
        client_id: int = 0
        user_id: int = 0
        admin_id: int = 0
        executor_id: int = 0
        department_id: int = 0

        status: str = ""
        is_closed: bool | None = None

        date_from: datetime | None = None
        date_to: datetime | None = None

        text: str = ""

        limit: int = 100
        offset: int = 0



@dataclass(frozen=True, kw_only=True)
class TicketSearchCriteria:
    client_id: int = 0
    user_id: int = 0
    admin_id: int = 0
    executor_id: int = 0
    department_id: int = 0

    status: str = ""
    is_closed: bool | None = None

    date_from: datetime | None = None
    date_to: datetime | None = None

    text: str = ""

    limit: int = 100
    offset: int = 0


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
        Iterate non-terminal tickets of one client in batches.

        More specific workflow rules are checked later by domain services.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_user_ticket_id(
        self,
        user_ticket_id: int,
    ) -> Ticket:
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

    # ----------------------------
    # Reference checks
    # ----------------------------

    @abstractmethod
    def does_client_exist(self, client_id: int) -> bool:
        """
        Returns True when at least one Ticket belongs to client_id.

        Historical method name is preserved for compatibility.
        """
        raise NotImplementedError

    @abstractmethod
    def does_user_tickets_exist(
        self,
        user_ticket_id: int,
    ) -> bool:
        """
        Returns True when at least one Ticket references user_ticket_id.

        Historical method name is preserved for compatibility.
        """
        raise NotImplementedError

    @abstractmethod
    def has_admin_reference(self, admin_id: int) -> bool:
        """
        Returns True when an Admin is referenced by Ticket aggregate data.
        """
        raise NotImplementedError

    @abstractmethod
    def has_department_reference(
        self,
        department_id: int,
    ) -> bool:
        """
        Returns True when at least one Ticket belongs to department_id.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
            self,
            criteria: TicketSearchCriteria,
    ) -> list[Ticket]:
        raise NotImplementedError