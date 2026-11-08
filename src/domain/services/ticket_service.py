"""Domain facade for internal Ticket operations.

The application layer is responsible for loading aggregates, authorization,
locking, persistence and transactions. This facade delegates Ticket-local
rules to Ticket and cross-aggregate workflow/contact coordination to
TicketSyncService.

A linked pair must be structurally and workflow-consistent *before* a new
Admin-side workflow operation. Synchronization of the resulting state happens
before the application layer commits the pair.

After an exception, the application layer must roll back the transaction and
discard or restore mutated in-memory aggregates.
"""

from datetime import datetime, timedelta

from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.statuses.ticket_user_status import TicketUserStatus
from src.domain.statuses.ticket_user_status_record import TicketUserStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment, TicketUrgency
from src.domain.ticket_user import TicketUser
from src.domain.value_objects import CommonComment


class TicketService:
    """Provide a single domain entry point for internal Ticket operations."""

    def __init__(self, ticket_sync_service: TicketSyncService) -> None:
        self._ticket_sync_service = ticket_sync_service

    # ==================================================================
    # Creation
    # ==================================================================

    @staticmethod
    def create(
        *,
        client_id: int,
        admin_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        department_id: int = 0,
        description: str = "",
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        comment: str = "",
    ) -> Ticket:
        """Create a standalone, Admin-initiated Ticket (CREATED).

        This facade does not allow attaching a TicketUser to CREATED.
        """
        return Ticket.create(
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
        """Create Ticket from an existing user-facing request."""
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

    # ==================================================================
    # Ticket-local data
    # ==================================================================

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

    # ==================================================================
    # Shared Ticket / TicketUser data
    # ==================================================================

    def change_contact_user(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        contact_user_id: int,
    ) -> TicketUser | None:
        """Change contact User on Ticket alone, or on both linked aggregates.

        Contact id 0 resets contact to the owner where the aggregate permits it.
        RBAC is checked by the application layer.
        """
        if type(actor_employee_id) is not int or actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be a positive integer"
            )

        if type(contact_user_id) is not int or contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id must be a non-negative integer"
            )

        if ticket.user_ticket_id == 0:
            if ticket_user is not None:
                raise DomainOperationError(
                    "Standalone Ticket must not have TicketUser"
                )

            ticket.change_contact_user(contact_user_id=contact_user_id)
            return None

        linked_ticket_user = self._require_linked_ticket_user(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        self._ticket_sync_service.change_contact_user(
            ticket,
            linked_ticket_user,
            actor_employee_id=actor_employee_id,
            contact_user_id=contact_user_id,
        )
        return linked_ticket_user

    # ==================================================================
    # Planning
    # ==================================================================

    @staticmethod
    def schedule(*, ticket: Ticket, planned_at: datetime) -> None:
        ticket.schedule(planned_at=planned_at)

    @staticmethod
    def clear_schedule(*, ticket: Ticket) -> None:
        ticket.clear_schedule()

    # ==================================================================
    # Basic workflow
    # ==================================================================

    def accept(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.accept(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def reject(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str,
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        if linked is not None:
            self._validate_ticket_user_cancel_comment(
                actor_employee_id=actor_employee_id,
                comment=ticket_user_comment,
            )
        ticket.reject(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def defer(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str,
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.defer(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def suspend(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.suspend(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def assign(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        executor: Admin,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)

        if not isinstance(executor, Admin):
            raise DomainOperationError("executor must be an Admin")

        if type(executor.employee_id) is not int or executor.employee_id <= 0:
            raise DomainOperationError("executor.employee_id must be a positive integer")

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
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    # ==================================================================
    # Work
    # ==================================================================

    def start_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        work_is_remote: bool,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.start_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

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
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.register_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            duration=duration,
            comment=comment,
        )
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def pause_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.pause_work(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def resume_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        work_is_remote: bool,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.resume_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def submit_for_review(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.submit_for_review(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    # ==================================================================
    # Composite work scenario
    # ==================================================================

    def start_remote_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        """Start recommended remote work through Ticket's composite command."""
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.start_remote_work(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    # ==================================================================
    # Finalization
    # ==================================================================

    def execute(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        ticket.execute(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    def cancel(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str,
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked = self._prepare_workflow_operation(ticket=ticket, ticket_user=ticket_user)
        if linked is not None:
            self._validate_ticket_user_cancel_comment(
                actor_employee_id=actor_employee_id,
                comment=ticket_user_comment,
            )
        ticket.cancel(actor_employee_id=actor_employee_id, comment=comment)
        return self._sync_from_ticket(
            ticket=ticket, ticket_user=linked, comment=ticket_user_comment
        )

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _prepare_workflow_operation(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
    ) -> TicketUser | None:
        """Reject mismatched linked workflow before mutating internal Ticket.

        A standalone Ticket must not have an accompanying TicketUser.
        The linked pair must be both structurally and workflow-consistent.
        """
        if ticket.user_ticket_id == 0:
            if ticket_user is not None:
                raise DomainOperationError(
                    "Standalone Ticket must not have TicketUser"
                )
            return None

        linked = self._require_linked_ticket_user(ticket=ticket, ticket_user=ticket_user)
        self._ticket_sync_service.ensure_workflow_consistent(ticket, linked)
        return linked

    def _require_linked_ticket_user(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
    ) -> TicketUser:
        if ticket_user is None:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} is linked to TicketUser "
                f"{ticket.user_ticket_id}, but TicketUser was not provided"
            )

        self._ticket_sync_service.ensure_consistent(ticket, ticket_user)
        return ticket_user

    def _sync_from_ticket(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        comment: str = "",
    ) -> TicketUser | None:
        """Return the TicketUser only when its workflow status changed."""
        if ticket_user is None:
            return None

        previous_status = ticket_user.current_status()
        self._ticket_sync_service.sync_from_ticket(
            ticket,
            ticket_user,
            comment=comment,
        )

        if ticket_user.current_status() == previous_status:
            return None
        return ticket_user

    @staticmethod
    def _validate_ticket_user_cancel_comment(
        *,
        actor_employee_id: int,
        comment: str,
    ) -> None:
        """Validate the required user-facing comment before Ticket mutation.

        Use the *existing* TicketUserStatusRecord validation contract rather
        than duplicating CommonComment normalization or length rules here.
        This temporary record is validated but is not attached to any history.
        """
        TicketUserStatusRecord(
            status=TicketUserStatus.CANCELLED_BY_ADMIN,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
