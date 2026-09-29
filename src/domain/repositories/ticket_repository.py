from abc import ABC, abstractmethod
from typing import Iterator

from src.domain.ticket import Ticket


class TicketRepository(ABC):
    """
    Abstract repository for Ticket aggregate.

    Repository contains:

    - loading of individual Ticket aggregates;
    - frequently used Ticket selections;
    - auxiliary iterators used for batch processing/testing;
    - persistence operations;
    - reference checks used by other application services.

    Complex universal search is intentionally not implemented here.

    At the current expected data volume, additional UI filtering may be
    performed on the client side.

    If query requirements become significantly more complex later,
    read operations may be moved to a dedicated query/read repository.
    """

    # ==================================================================
    # Reads
    # ==================================================================

    @abstractmethod
    def get(
        self,
        ticket_id: int,
    ) -> Ticket:
        """
        Return Ticket by ticket_id.

        Repository implementation defines the concrete behavior when
        Ticket does not exist.
        """

        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Ticket]:
        """
        Return all Tickets.

        This method is currently intended as a simple source for relatively
        small Ticket lists.

        With the expected number of Tickets, additional sorting/filtering
        may initially be performed outside the repository.

        If the number of Tickets grows substantially, this method may later
        be complemented or replaced on the read side by pagination or a
        dedicated query model.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_client_id(
        self,
        client_id: int,
    ) -> list[Ticket]:
        """
        Return all Tickets belonging to the specified Client.

        Both open and closed Tickets are returned.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_user_id(
        self,
        user_id: int,
    ) -> list[Ticket]:
        """
        Return all Tickets associated with the specified User.

        Both open and closed Tickets are returned.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_department_id(
        self,
        department_id: int,
    ) -> list[Ticket]:
        """
        Return all Tickets belonging to the specified Department.

        Department-based selection is a normal operational query because
        different departments may have different work processes.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_current_executor(
        self,
        executor_id: int,
    ) -> list[Ticket]:
        """
        Return Tickets whose current executor is executor_id.

        Persistence may use the denormalized projection:

            tickets.current_executor_id

        for this query.

        The authoritative domain value is still derived by:

            Ticket.current_executor_id()

        from Ticket workflow history.
        """

        raise NotImplementedError

    @abstractmethod
    def get_open(self) -> list[Ticket]:
        """
        Return all currently open Tickets.

        Persistence may use:

            date_finished IS NULL

        rather than enumerating all non-terminal Ticket statuses.

        date_finished is a persisted projection derived from Ticket
        workflow history.
        """

        raise NotImplementedError

    @abstractmethod
    def get_closed(self) -> list[Ticket]:
        """
        Return all currently closed Tickets.

        Persistence may use:

            date_finished IS NOT NULL

        rather than enumerating concrete terminal statuses.

        This selection is primarily useful for historical and analytical
        operations.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_user_ticket_id(
        self,
        user_ticket_id: int,
    ) -> Ticket:
        """
        Return Ticket linked to the specified TicketUser.

        For a linked pair:

            Ticket.user_ticket_id == TicketUser.ticket_id
        """

        raise NotImplementedError

    # ==================================================================
    # Auxiliary iteration
    # ==================================================================

    @abstractmethod
    def iter_get_all(
        self,
        *,
        batch_size: int = 500,
    ) -> Iterator[Ticket]:
        """
        Iterate over all Tickets in batches.

        This method is retained primarily for testing, maintenance and
        batch-processing scenarios.

        It is not intended to replace normal operational query methods.
        """

        raise NotImplementedError

    @abstractmethod
    def iter_by_client_id(
        self,
        *,
        client_id: int,
        batch_size: int = 500,
    ) -> Iterator[Ticket]:
        """
        Iterate over Tickets belonging to one Client in batches.

        Both open and closed Tickets are returned.

        This method is retained primarily for testing, maintenance and
        batch-processing scenarios.
        """

        raise NotImplementedError

    # ==================================================================
    # Persistence
    # ==================================================================

    @abstractmethod
    def save(
        self,
        ticket: Ticket,
    ) -> Ticket:
        """
        Persist Ticket aggregate.

        In addition to aggregate data and workflow history, persistence
        should update derived query projections such as:

            current_executor_id
            date_finished

        Their values must be taken from the aggregate:

            ticket.current_executor_id()
            ticket.date_finished

        Repository must not duplicate Ticket workflow rules in order to
        calculate these values.
        """

        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        ticket_id: int,
    ) -> None:
        """
        Delete Ticket by ticket_id.
        """

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
        Return True when at least one Ticket references client_id.

        Historical method name is preserved for compatibility.
        """

        raise NotImplementedError

    @abstractmethod
    def does_user_tickets_exist(
        self,
        user_ticket_id: int,
    ) -> bool:
        """
        Return True when at least one Ticket references user_ticket_id.

        Historical method name is preserved for compatibility.
        """

        raise NotImplementedError

    @abstractmethod
    def has_admin_reference(
        self,
        admin_id: int,
    ) -> bool:
        """
        Return True when Admin is referenced by Ticket aggregate data.

        The concrete persistence implementation determines which Ticket
        records constitute an Admin reference.
        """

        raise NotImplementedError

    @abstractmethod
    def has_department_reference(
        self,
        department_id: int,
    ) -> bool:
        """
        Return True when at least one Ticket references department_id.
        """

        raise NotImplementedError