from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.ticket_components import Comment, ExecutorAssignment


class TicketWorkflowService:
    """
    Domain workflow service.

    Coordinates related domain objects:
        - Ticket
        - TicketUser

    Does NOT:
        - use repositories;
        - open transactions;
        - check permissions;
        - return DTOs.
    """

    @staticmethod
    def create_from_admin(
            *,
        ticket_id: int,
        client_id: int,
        admin_id: int,
        text_of_ticket: str = "",
        user_id: int = 0,
        contact_user_id: int = 0,
        is_remote: bool = False,
        urgency_level: int = 0,
        user_ticket: TicketUser | None = None,
        executor_id: int = 0,
        comment: str = "",
    ) -> Ticket:
        user_ticket_id = 0

        if user_ticket is not None:
            user_ticket_id = user_ticket.ticket_id
            user_ticket.confirm(actor_employee_id=admin_id)
            text_of_ticket = (
                f"{text_of_ticket}\n\n"
                f"{user_ticket.description}"
            ).strip()


        return Ticket.create(
            ticket_id=ticket_id,
            client_id=client_id,
            admin_id=admin_id,
            text_of_ticket=text_of_ticket,
            user_id=user_id,
            contact_user_id=contact_user_id,
            is_remote=is_remote,
            urgency_level=urgency_level,
            user_ticket_id=user_ticket_id,
            executor_id=executor_id,
            comment=comment,
        )

    @staticmethod
    def start_work(
            *,
        ticket: Ticket,
        user_ticket: TicketUser | None,
        actor_admin_id: int,
        executor_id: int = 0,
    ) -> None:
        ticket.at_work(
            actor_employee_id=actor_admin_id,
            executor_id=executor_id,
        )

        if user_ticket is not None:
            user_ticket.start_work(
                actor_employee_id=executor_id or actor_admin_id,
            )

    @staticmethod
    def defer_admin(
            *,
            ticket: Ticket,
            actor_admin_id: int,

    ) -> None:
        ticket.defer(
            actor_employee_id=actor_admin_id,
        )


    @staticmethod
    def execute(
            *,
        ticket: Ticket,
        user_ticket: TicketUser | None,
        actor_admin_id: int,
        comment: str = "",
    ) -> None:
        ticket.execute(
            actor_employee_id=actor_admin_id,
            comment=comment,
        )

        if user_ticket is not None:
            user_ticket.execute(
                actor_employee_id=actor_admin_id,
            )

    @staticmethod
    def cancel_by_admin(
            *,
        ticket: Ticket,
        user_ticket: TicketUser | None,
        actor_admin_id: int,
        comment: str = "",
    ) -> None:
        ticket.cancel(
            actor_employee_id=actor_admin_id,
            comment=comment,
        )

        if user_ticket is not None:
            user_ticket.cancel_by_admin(
                actor_employee_id=actor_admin_id,
            )

    @staticmethod
    def add_comment_from_admin(
            *,
        ticket: Ticket,
        actor_admin_id: int,
        comment: str,
    ) -> None:
        ticket.add_comment(
            Comment(
                employee_id=actor_admin_id,
                comment=comment,
            )
        )

    @staticmethod
    def assign_executor(
            *,
        ticket: Ticket,
        actor_admin_id: int,
        executor_id: int,
    ) -> None:
        ticket.add_executor(
            ExecutorAssignment(
                admin_id=actor_admin_id,
                executor_id=executor_id,
            )
        )