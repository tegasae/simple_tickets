# src/domain/services/ticket_service.py

from datetime import datetime, timedelta

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.ticket import (
    Ticket,
    TicketUrgency,
)
from src.domain.ticket_components import Comment
from src.domain.ticket_user import TicketUser
from src.domain.value_objects import CommonComment


class TicketService:
    """
    Domain facade for Ticket operations.

    Responsibilities:
    - provides a single domain entry point for Ticket use cases;
    - invokes Ticket aggregate commands;
    - validates linked Ticket / TicketUser pair before mutation;
    - synchronizes Ticket -> TicketUser after Ticket workflow changes;
    - coordinates shared Ticket / TicketUser data.

    Does not handle:
    - repositories;
    - UnitOfWork;
    - persistence;
    - transactions;
    - RBAC;
    - permissions;
    - loading aggregates;
    - actor role checks.

    Application layer decides whether an actor is allowed to invoke
    a particular operation.

    Ticket remains responsible for:
    - its workflow;
    - transition validity;
    - aggregate invariants;
    - status-record context rules.

    TicketSyncService remains responsible for:
    - Ticket / TicketUser structural consistency;
    - workflow synchronization;
    - shared contact_user_id.
    """

    def __init__(
        self,
        ticket_sync_service: TicketSyncService,
    ) -> None:
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
        ticket_user_id: int = 0,
        user_id: int = 0,
        contact_user_id: int = 0,
        department_id: int = 0,
        description: str = "",
        remote_work_recommended: bool = False,
        urgency: TicketUrgency = TicketUrgency.NORMAL,
        planned_at: datetime | None = None,
        comment: str = "",
    ) -> Ticket:
        return Ticket.create(
            client_id=client_id,
            admin_id=admin_id,
            text_of_ticket=text_of_ticket,
            ticket_user_id=ticket_user_id,
            user_id=user_id,
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
    # Ticket data
    # ==================================================================

    @staticmethod
    def add_comment(
        *,
        ticket: Ticket,
        employee_id: int,
        comment: str,
    ) -> None:
        ticket.add_comment(
            Comment(
                employee_id=employee_id,
                comment=CommonComment(comment),
            )
        )

    @staticmethod
    def change_department(
        *,
        ticket: Ticket,
        department_id: int,
    ) -> None:
        ticket.change_department(
            department_id=department_id,
        )

    @staticmethod
    def update_description(
        *,
        ticket: Ticket,
        description: str,
    ) -> None:
        ticket.update_description(
            description=description,
        )

    @staticmethod
    def set_remote_work_recommended(
        *,
        ticket: Ticket,
        recommend: bool,
    ) -> None:
        ticket.set_remote_work_recommended(
            recommend=recommend,
        )

    @staticmethod
    def change_urgency(
        *,
        ticket: Ticket,
        urgency: TicketUrgency,
    ) -> None:
        ticket.change_urgency(
            urgency=urgency,
        )

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
        """
        Change Ticket contact User.

        Standalone Ticket:
            changes Ticket only.

        Linked Ticket:
            contact_user_id is a permanent shared invariant and therefore
            TicketSyncService changes both aggregates.

        Returns modified TicketUser when linked, otherwise None.
        """

        if ticket.user_ticket_id == 0:
            if ticket_user is not None:
                raise DomainOperationError(
                    "Standalone Ticket must not have TicketUser"
                )

            ticket.change_contact_user(
                contact_user_id=contact_user_id,
            )

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
    def schedule(
        *,
        ticket: Ticket,
        planned_at: datetime,
    ) -> None:
        ticket.schedule(
            planned_at=planned_at,
        )

    @staticmethod
    def clear_schedule(
        *,
        ticket: Ticket,
    ) -> None:
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.accept(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.reject(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.defer(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.suspend(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
        )

    def assign(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        executor_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.assign(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.start_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        duration: timedelta = timedelta(),
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.register_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            duration=duration,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.pause_work(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.resume_work(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.submit_for_review(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
        )

    # ==================================================================
    # Composite work scenarios
    # ==================================================================

    def complete_work_retroactively(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        work_is_remote: bool,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        duration: timedelta = timedelta(),
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        """
        Register completed work retrospectively.

        Ticket workflow:

            ASSIGNED
                -> AT_WORK
                -> READY_FOR_REVIEW

        TicketUser is synchronized only after the complete Ticket
        operation.

        Since both ASSIGNED and AT_WORK correspond to IN_WORK,
        no external workflow information is lost by synchronizing
        only the final READY_FOR_REVIEW state.
        """

        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.complete_work_retroactively(
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            started_at=started_at,
            finished_at=finished_at,
            duration=duration,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
        )

    def start_remote_work(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        actor_employee_id: int,
        comment: str = "",
        ticket_user_comment: str = "",
    ) -> TicketUser | None:
        """
        Start recommended remote work.

        Ticket workflow:

            ACCEPTED
                -> ASSIGNED
                -> AT_WORK

        or:

            ASSIGNED
                -> AT_WORK

        Ticket itself validates:
        - remote_work_recommended;
        - allowed source status;
        - current executor when already ASSIGNED.
        """

        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.start_remote_work(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        """
        READY_FOR_REVIEW -> EXECUTED.

        Whether the Admin has permission to perform this operation
        is decided by application/RBAC.
        """

        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.execute(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        linked_ticket_user = self._prepare_workflow_operation(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        ticket.cancel(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._sync_from_ticket(
            ticket=ticket,
            ticket_user=linked_ticket_user,
            comment=ticket_user_comment,
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
        """
        Validate linked pair before Ticket is mutated.

        Standalone Ticket:
            ticket_user must be None.

        Linked Ticket:
            ticket_user is required and structural consistency is
            validated before workflow mutation.
        """

        if ticket.user_ticket_id == 0:
            if ticket_user is not None:
                raise DomainOperationError(
                    "Standalone Ticket must not have TicketUser"
                )

            return None

        return self._require_linked_ticket_user(
            ticket=ticket,
            ticket_user=ticket_user,
        )

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

        self._ticket_sync_service.ensure_consistent(
            ticket,
            ticket_user,
        )

        return ticket_user

    def _sync_from_ticket(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None,
        comment: str = "",
    ) -> TicketUser | None:
        """
        Synchronize Ticket -> TicketUser.

        Returns TicketUser only when synchronization actually changed
        its workflow. This allows application layer to avoid saving an
        unchanged TicketUser.
        """

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