from src.domain.ticket import Ticket, TicketStatus
from src.domain.ticket_components import Comment, ExecutorAssignment
from src.domain.repositories.ticket_repository import TicketRepository


class TicketService:
    """
    Domain service for Ticket use-cases.

    Responsibilities:
        - create ticket
        - change status
        - add comments
        - assign executors
        - close / cancel
        - delete ticket
    """

    def __init__(self, ticket_repository: TicketRepository):
        self._ticket_repository = ticket_repository

    # --------------------------------
    # Create
    # --------------------------------

    def create_ticket(
        self,
        *,
        client_id: int,
        admin_id: int,
        description: str,
        text_of_ticket: str = "",
        user_id: int = 0,
        contact_user_id: int = 0,
        is_remote: bool = False,
        urgency_level: int = 0,
    ) -> Ticket:

        ticket = Ticket.create(
            ticket_id=0,
            client_id=client_id,
            admin_id=admin_id,
            description=description,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            is_remote=is_remote,
            urgency_level=urgency_level,
        )

        return self._ticket_repository.save(ticket)

    # --------------------------------
    # Status operations
    # --------------------------------

    def change_status(
        self,
        *,
        ticket_id: int,
        new_status: TicketStatus,
        actor_employee_id: int,
    ) -> Ticket:

        ticket = self._ticket_repository.get(ticket_id)

        ticket.change_status(new_status, actor_employee_id)

        return self._ticket_repository.save(ticket)

    def start_work(self, *, ticket_id: int, actor_employee_id: int) -> Ticket:

        ticket = self._ticket_repository.get(ticket_id)

        ticket.start_work(actor_employee_id)

        return self._ticket_repository.save(ticket)

    def execute(self, *, ticket_id: int, actor_employee_id: int) -> Ticket:

        ticket = self._ticket_repository.get(ticket_id)

        ticket.execute(actor_employee_id)

        return self._ticket_repository.save(ticket)

    def cancel(self, *, ticket_id: int, actor_employee_id: int,comment:str) -> Ticket:

        ticket = self._ticket_repository.get(ticket_id)
        ticket.add_comment(comment=Comment(employee_id=actor_employee_id,comment=comment))
        ticket.cancel(actor_employee_id)
        return self._ticket_repository.save(ticket)

    def defer(self, *, ticket_id: int, actor_employee_id: int,comment:str) -> Ticket:

        ticket = self._ticket_repository.get(ticket_id)
        ticket.add_comment(comment=Comment(employee_id=actor_employee_id, comment=comment))
        ticket.defer(actor_employee_id)

        return self._ticket_repository.save(ticket)

    # --------------------------------
    # Comments
    # --------------------------------

    def add_comment(
        self,
        *,
        ticket_id: int,
        employee_id: int,
        comment: str,
    ) -> Ticket:

        ticket = self._ticket_repository.get(ticket_id)

        ticket.add_comment(
            Comment(
                employee_id=employee_id,
                comment=comment,
            )
        )

        return self._ticket_repository.save(ticket)

    # --------------------------------
    # Executors
    # --------------------------------

    def assign_executor(
        self,
        *,
        ticket_id: int,
        admin_id: int,
    ) -> Ticket:

        ticket = self._ticket_repository.get(ticket_id)

        ticket.add_executor(
            ExecutorAssignment(
                admin_id=admin_id
            )
        )

        return self._ticket_repository.save(ticket)

    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(self, ticket_id: int) -> Ticket:
        return self._ticket_repository.get(ticket_id)

    def get_all(self) -> list[Ticket]:
        return self._ticket_repository.get_all()

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(self, *, ticket_id: int) -> None:
        """
        Hard delete ticket.
        Usually rare operation.
        """
        self._ticket_repository.delete(ticket_id)