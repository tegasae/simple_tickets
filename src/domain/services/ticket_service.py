"""Domain facade for internal Ticket operations.

Ticket owns its data and workflow rules. TicketSyncService synchronizes
linked Ticket/TicketUser instances after Ticket mutations.

The application layer creates and saves a new TicketUser first when a user
request is registered by staff, because TicketUser.create() initially has
id 0 and a linked Ticket requires its persisted positive identifier.

Authorization, persistence, transaction rollback, and disposal/restoration
of mutated aggregates on failure belong to the application layer.
"""

from datetime import datetime, timedelta

from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment, TicketUrgency
from src.domain.ticket_user import TicketUser
from src.domain.value_objects import CommonComment


class TicketService:
    """The domain entry point for commands on internal Tickets."""

    def __init__(self, ticket_sync_service: TicketSyncService) -> None:
        self._ticket_sync_service = ticket_sync_service

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        client_id: int,
        admin_id: int,
        text_of_ticket: str,
        user_id: int = 0,
        ticket_user: TicketUser | None = None,
        contact_user_id: int = 0,
        department_id: int = 0,
        description: str = "",
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        comment: str = "",
    ) -> Ticket:
        """Create an Admin Ticket or register an existing persisted user request.

        user_id == 0: standalone Ticket, initial CREATED.
        user_id > 0:  linked Ticket, initial CREATED_FROM_REQUEST_USER.

        A linked request's TicketUser must have been created and saved in the
        same application transaction before calling this factory; otherwise
        its ticket_user_id is still 0 and a valid Ticket cannot be created.
        """
        if type(user_id) is not int or user_id < 0:
            raise DomainOperationError("user_id must be a non-negative integer")

        if user_id == 0:
            if ticket_user is not None:
                raise DomainOperationError(
                    "Standalone Ticket must not have TicketUser"
                )
            ticket = Ticket.create(
                client_id=client_id,
                admin_id=admin_id,
                text_of_ticket=text_of_ticket,
                contact_user_id=contact_user_id,
                department_id=department_id,
                description=description,
                remote_work_recommended=remote_work_recommended,
                urgency=urgency,
                planned_at=planned_at,
                comment=comment,
            )
        else:
            if ticket_user is None:
                raise DomainOperationError(
                    "User request requires a previously saved TicketUser"
                )
            ticket = Ticket.create_from_request_user(
                client_id=client_id,
                admin_id=admin_id,
                user_id=user_id,
                user_ticket_id=ticket_user.ticket_user_id,
                text_of_ticket=text_of_ticket,
                contact_user_id=contact_user_id,
                department_id=department_id,
                description=description,
                remote_work_recommended=remote_work_recommended,
                urgency=urgency,
                planned_at=planned_at,
                comment=comment,
            )

        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)
        return ticket

    @staticmethod
    def create_from_ticket_user(
        *,
        client_id: int,
        user_id: int,
        user_ticket_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        department_id: int = 0,
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        comment: str = "",
    ) -> Ticket:
        """Create a Ticket from a TicketUser registered earlier by the user."""
        return Ticket.create_from_ticket_user(
            client_id=client_id,
            user_id=user_id,
            user_ticket_id=user_ticket_id,
            text_of_ticket=text_of_ticket,
            contact_user_id=contact_user_id,
            description=description,
            department_id=department_id,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
        )

    # ------------------------------------------------------------------
    # Ticket-local data
    # ------------------------------------------------------------------

    @staticmethod
    def add_comment(*, ticket: Ticket, employee_id: int, comment: str) -> None:
        ticket.add_comment(
            Comment(employee_id=employee_id, comment=CommonComment(comment))
        )

    @staticmethod
    def change_department(*, ticket: Ticket, department_id: int) -> None:
        ticket.change_department(department_id=department_id)

    @staticmethod
    def update_description(*, ticket: Ticket, description: str) -> None:
        ticket.update_description(description=description)

    @staticmethod
    def set_remote_work_recommended(*, ticket: Ticket, recommend: bool) -> None:
        ticket.set_remote_work_recommended(recommend=recommend)

    @staticmethod
    def change_urgency(*, ticket: Ticket, urgency: TicketUrgency) -> None:
        ticket.change_urgency(urgency=urgency)

    def change_contact_user(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        contact_user_id: int,
    ) -> None:
        """Change Ticket contact, then synchronize the linked TicketUser.

        The actor parameter is retained in the facade for caller compatibility.
        No contact-change actor is stored in either aggregate's status history.
        """
        if type(actor_employee_id) is not int or actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be a positive integer"
            )

        # Ticket.change_contact_user() does not accept zero when user_id > 0.
        # Preserve the command's established meaning: zero resets to owner.
        resolved_contact = (
            ticket.user_id
            if contact_user_id == 0 and ticket.user_id > 0
            else contact_user_id
        )
        ticket.change_contact_user(contact_user_id=resolved_contact)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    @staticmethod
    def schedule(*, ticket: Ticket, planned_at: datetime) -> None:
        ticket.schedule(planned_at=planned_at)

    @staticmethod
    def clear_schedule(*, ticket: Ticket) -> None:
        ticket.clear_schedule()

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def accept(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        ticket.accept(actor_employee_id=actor_employee_id, comment=comment)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def reject(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str,
    ) -> None:
        ticket.reject(actor_employee_id=actor_employee_id, comment=comment)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def defer(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str,
    ) -> None:
        ticket.defer(actor_employee_id=actor_employee_id, comment=comment)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def suspend(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        ticket.suspend(actor_employee_id=actor_employee_id, comment=comment)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def assign(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        executor: Admin,
        comment: str = "",
    ) -> None:
        if not isinstance(executor, Admin):
            raise DomainOperationError("executor must be an Admin")
        if type(executor.employee_id) is not int or executor.employee_id <= 0:
            raise DomainOperationError(
                "executor.employee_id must be a positive integer"
            )
        if type(ticket.department_id) is not int or ticket.department_id <= 0:
            raise DomainOperationError("Ticket must have a valid department_id")
        if executor.department_id != ticket.department_id:
            raise DomainOperationError(
                f"Ticket has department {ticket.department_id}; "
                f"executor has department {executor.department_id}"
            )
        ticket.assign(
            actor_employee_id=actor_employee_id,
            executor_id=executor.employee_id,
            comment=comment,
        )
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    # ------------------------------------------------------------------
    # Work
    # ------------------------------------------------------------------

    def start_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        work_is_remote: bool,
        comment: str = "",
    ) -> None:
        ticket.start_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def register_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        work_is_remote: bool,
        actual_started_at: datetime | None = None,
        actual_finished_at: datetime | None = None,
        duration: timedelta = timedelta(0),
        comment: str = "",
    ) -> None:
        ticket.register_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            duration=duration,
            comment=comment,
        )
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def pause_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        ticket.pause_work(actor_employee_id=actor_employee_id, comment=comment)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def resume_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        work_is_remote: bool,
        comment: str = "",
    ) -> None:
        ticket.resume_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def submit_for_review(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        ticket.submit_for_review(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def start_remote_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        ticket.start_remote_work(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def execute(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        ticket.execute(actor_employee_id=actor_employee_id, comment=comment)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)

    def cancel(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str,
    ) -> None:
        ticket.cancel(actor_employee_id=actor_employee_id, comment=comment)
        self._ticket_sync_service.sync_from_ticket(ticket, ticket_user)