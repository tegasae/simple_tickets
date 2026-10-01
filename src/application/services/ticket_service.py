# src/application/services/ticket_application_service.py

from __future__ import annotations

from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import (
    TicketDTO,
    TicketResponseDTO,
)
from src.application.helper.actor_helper import EmployeeActorHelper

from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_service import TicketService
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.ticket import Ticket, TicketUrgency
from src.domain.ticket_user import TicketUser
from src.domain.uow.unit_of_work import UnitOfWork


class TicketApplicationService:
    """
    Application service for internal Ticket.

    Responsibilities:
    - RBAC / permissions;
    - UnitOfWork and transaction;
    - aggregate loading;
    - validation of external references;
    - optimistic concurrency guards for read-only aggregates;
    - calling TicketService;
    - persistence;
    - DTO assembly.

    Does not contain:
    - Ticket workflow rules;
    - TicketStatusRecord construction;
    - Ticket / TicketUser synchronization rules;
    - SQL;
    - repository business logic.

    TicketService coordinates Ticket and linked TicketUser.

    EmployeeActorHelper is responsible for:
    - loading actor;
    - checking actor enabled state;
    - permission checks;
    - actor caching inside its lifecycle.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

        self.actor = EmployeeActorHelper(
            self.uow
        )

        self.ticket_sync_service = TicketSyncService()

        self.ticket_service = TicketService(
            ticket_sync_service=self.ticket_sync_service,
        )

    # ==================================================================
    # Creation
    # ==================================================================

    def create_ticket(
            self,
            *,
            ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Create internal Ticket.

        Required permission:

            TICKET_CREATED
                OR
            TICKET_OPERATION

        If user_id == 0:

            create standalone internal Ticket:

                Ticket.CREATED

        If user_id > 0:

            create TicketUser first:

                TicketUser.CREATED

            then create linked internal Ticket:

                Ticket.CREATED

            Ticket is created by Admin, therefore its initial status
            is CREATED, not CREATED_FROM_TICKET_USER.

        If actor additionally has TICKET_ACCEPTED:

            standalone Ticket:

                CREATED -> ACCEPTED

            linked Ticket:

                Ticket.CREATED -> ACCEPTED
                TicketUser.CREATED -> IN_WORK
        """

        with self.uow:
            actor = self.actor.require_actor_admin_any(
                actor_admin_id=ticket_dto.actor_admin_id,
                permissions=(
                    AdminPermission.TICKET_CREATED,
                    AdminPermission.TICKET_OPERATION,
                ),
            )

            if ticket_dto.ticket_id != 0:
                raise DomainOperationError(
                    "create_ticket requires ticket_id = 0"
                )

            if ticket_dto.user_ticket_id != 0:
                raise DomainOperationError(
                    "create_ticket cannot use existing TicketUser"
                )

            self._validate_create_references(
                ticket_dto=ticket_dto,
            )

            ticket_user: TicketUser | None = None
            user_ticket_id = 0

            # --------------------------------------------------------------
            # If User is specified, create TicketUser first.
            # --------------------------------------------------------------

            if ticket_dto.user_id > 0:
                ticket_user = TicketUser.create(
                    client_id=ticket_dto.client_id,
                    user_id=ticket_dto.user_id,
                    contact_user_id=ticket_dto.contact_user_id,
                    text_of_ticket=ticket_dto.text_of_ticket,
                    description=ticket_dto.description,
                    comment=ticket_dto.comment,
                )

                saved_ticket_user = self.uow.user_tickets.save(
                    ticket_user
                )

                if saved_ticket_user is not None:
                    ticket_user = saved_ticket_user

                if ticket_user.ticket_user_id <= 0:
                    raise DomainOperationError(
                        "TicketUser repository must assign "
                        "ticket_user_id before creating linked Ticket"
                    )

                user_ticket_id = ticket_user.ticket_user_id

            # --------------------------------------------------------------
            # Resolve contact_user_id.
            #
            # TicketUser.create() may normalize:
            #
            #     contact_user_id == 0
            #
            # to:
            #
            #     contact_user_id == user_id
            #
            # Therefore linked Ticket must use the value from TicketUser.
            # --------------------------------------------------------------

            contact_user_id = (
                ticket_user.contact_user_id
                if ticket_user is not None
                else ticket_dto.contact_user_id
            )

            # --------------------------------------------------------------
            # Create internal Ticket.
            #
            # In both cases Ticket is created by Admin, therefore its
            # initial status is CREATED.
            # --------------------------------------------------------------

            ticket = self.ticket_service.create(
                client_id=ticket_dto.client_id,
                admin_id=actor.employee_id,
                text_of_ticket=ticket_dto.text_of_ticket,
                ticket_user_id=user_ticket_id,
                user_id=ticket_dto.user_id,
                contact_user_id=contact_user_id,
                department_id=ticket_dto.department_id,
                description=ticket_dto.description,
                remote_work_recommended=(
                    ticket_dto.remote_work_recommended
                ),
                urgency=TicketUrgency(
                    ticket_dto.urgency
                ),
                planned_at=ticket_dto.planned_at,
                comment=ticket_dto.comment,
            )

            # --------------------------------------------------------------
            # Validate linked pair.
            # --------------------------------------------------------------

            if ticket_user is not None:
                self.ticket_sync_service.ensure_consistent(
                    ticket,
                    ticket_user,
                )

            # --------------------------------------------------------------
            # Optional automatic acceptance.
            # --------------------------------------------------------------

            changed_ticket_user: TicketUser | None = None

            if self.actor.has_admin_permission(
                    actor_admin_id=actor.employee_id,
                    permission=AdminPermission.TICKET_ACCEPTED,
            ):
                changed_ticket_user = self.ticket_service.accept(
                    ticket=ticket,
                    ticket_user=ticket_user,
                    actor_employee_id=actor.employee_id,
                    comment=ticket_dto.comment,
                )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )
    # ==================================================================
    # Ticket data
    # ==================================================================

    def add_comment(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            self.ticket_service.add_comment(
                ticket=ticket,
                employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
            )

    def update_description(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Ticket.description is independent from
        TicketUser.description.
        """

        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            self.ticket_service.update_description(
                ticket=ticket,
                description=ticket_dto.description,
            )

            return self._save_and_to_dto(
                ticket=ticket,
            )

    def change_department(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            if ticket_dto.department_id < 0:
                raise DomainOperationError(
                    "department_id cannot be negative"
                )

            if ticket_dto.department_id > 0:
                department = self.uow.departments.get(
                    ticket_dto.department_id,
                )

                department.ensure_enabled()

                # Department is read-only, but its enabled state
                # participates in the business decision.
                self.uow.departments.touch(
                    department
                )

            self.ticket_service.change_department(
                ticket=ticket,
                department_id=ticket_dto.department_id,
            )

            return self._save_and_to_dto(
                ticket=ticket,
            )

    def change_contact_user(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            if ticket_dto.contact_user_id < 0:
                raise DomainOperationError(
                    "contact_user_id cannot be negative"
                )

            if ticket_dto.contact_user_id > 0:
                contact_user = self.uow.users.get(
                    ticket_dto.contact_user_id,
                )

                contact_user.can_do_operation()

                if contact_user.client_id != ticket.client_id:
                    raise DomainOperationError(
                        "Contact User does not belong "
                        "to Ticket Client"
                    )

                self.uow.users.touch(
                    contact_user
                )

            changed_ticket_user = (
                self.ticket_service.change_contact_user(
                    ticket=ticket,
                    ticket_user=ticket_user,
                    actor_employee_id=actor.employee_id,
                    contact_user_id=ticket_dto.contact_user_id,
                )
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def set_remote_work_recommended(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            self.ticket_service.set_remote_work_recommended(
                ticket=ticket,
                recommend=ticket_dto.remote_work_recommended,
            )

            return self._save_and_to_dto(
                ticket=ticket,
            )

    def change_urgency(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            self.ticket_service.change_urgency(
                ticket=ticket,
                urgency=TicketUrgency(ticket_dto.urgency),
            )

            return self._save_and_to_dto(
                ticket=ticket,
            )

    # ==================================================================
    # Planning
    # ==================================================================

    def schedule(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            if ticket_dto.planned_at is None:
                raise DomainOperationError(
                    "planned_at is required"
                )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            self.ticket_service.schedule(
                ticket=ticket,
                planned_at=ticket_dto.planned_at,
            )

            return self._save_and_to_dto(
                ticket=ticket,
            )

    def clear_schedule(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            self.ticket_service.clear_schedule(
                ticket=ticket,
            )

            return self._save_and_to_dto(
                ticket=ticket,
            )

    # ==================================================================
    # Management workflow
    # ==================================================================

    def accept(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Requires TICKET_ACCEPTED.
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_ACCEPTED,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.accept(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def reject(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Requires TICKET_CANCELLED.
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_CANCELLED,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.reject(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def defer(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.defer(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def assign(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_OPERATION,
            )

            if ticket_dto.executor_id <= 0:
                raise DomainOperationError(
                    "assign requires executor_id > 0"
                )

            # If Admin assigns Ticket to himself, we already have
            # the loaded and validated aggregate in actor cache.
            if ticket_dto.executor_id == actor.employee_id:
                executor = actor
            else:
                executor = self.uow.admins.get(
                    ticket_dto.executor_id,
                )

                executor.can_do_operation()

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.assign(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                executor_id=executor.employee_id,
                comment=ticket_dto.comment,
            )

            if executor.employee_id != actor.employee_id:
                self.uow.admins.touch(
                    executor
                )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    # ==================================================================
    # Work
    # ==================================================================

    def start_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Requires TICKET_AT_WORK.

        Ticket validates that actor is current executor.
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_AT_WORK,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.start_work(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                work_is_remote=ticket_dto.work_is_remote,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def start_remote_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Requires TICKET_AT_WORK_REMOTE.

        Ticket performs:

            ACCEPTED
                -> ASSIGNED
                -> AT_WORK

        or:

            ASSIGNED
                -> AT_WORK
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_AT_WORK_REMOTE,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = (
                self.ticket_service.start_remote_work(
                    ticket=ticket,
                    ticket_user=ticket_user,
                    actor_employee_id=actor.employee_id,
                    comment=ticket_dto.comment,
                )
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def pause_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_AT_WORK,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.pause_work(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def resume_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_AT_WORK,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.resume_work(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                work_is_remote=ticket_dto.work_is_remote,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    # ==================================================================
    # Completion
    # ==================================================================

    def finish_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Requires TICKET_AT_WORK.

        Normal actor:

            AT_WORK
                -> READY_FOR_REVIEW

        Actor with TICKET_EXECUTED:

            AT_WORK
                -> READY_FOR_REVIEW
                -> EXECUTED
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_AT_WORK,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = (
                self.ticket_service.submit_for_review(
                    ticket=ticket,
                    ticket_user=ticket_user,
                    actor_employee_id=actor.employee_id,
                    comment=ticket_dto.comment,
                )
            )

            if self.actor.has_admin_permission(
                actor_admin_id=actor.employee_id,
                permission=AdminPermission.TICKET_EXECUTED,
            ):
                executed_ticket_user = (
                    self.ticket_service.execute(
                        ticket=ticket,
                        ticket_user=ticket_user,
                        actor_employee_id=actor.employee_id,
                    )
                )

                if executed_ticket_user is not None:
                    changed_ticket_user = executed_ticket_user

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def complete_work_retroactively(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Requires TICKET_AT_WORK_RETROSPECTIVE.

        Ticket performs:

            ASSIGNED
                -> AT_WORK
                -> READY_FOR_REVIEW

        Actor with TICKET_EXECUTED additionally performs:

            READY_FOR_REVIEW
                -> EXECUTED
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=(
                    AdminPermission.TICKET_AT_WORK_RETROSPECTIVE
                ),
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = (
                self.ticket_service.complete_work_retroactively(
                    ticket=ticket,
                    ticket_user=ticket_user,
                    actor_employee_id=actor.employee_id,
                    work_is_remote=ticket_dto.work_is_remote,
                    started_at=ticket_dto.actual_started_at,
                    finished_at=ticket_dto.actual_finished_at,
                    duration=ticket_dto.duration,
                    comment=ticket_dto.comment,
                )
            )

            if self.actor.has_admin_permission(
                actor_admin_id=actor.employee_id,
                permission=AdminPermission.TICKET_EXECUTED,
            ):
                executed_ticket_user = (
                    self.ticket_service.execute(
                        ticket=ticket,
                        ticket_user=ticket_user,
                        actor_employee_id=actor.employee_id,
                    )
                )

                if executed_ticket_user is not None:
                    changed_ticket_user = executed_ticket_user

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    # ==================================================================
    # Finalization
    # ==================================================================

    def execute(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        READY_FOR_REVIEW -> EXECUTED.

        Requires TICKET_EXECUTED.
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_EXECUTED,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.execute(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    def cancel(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Requires TICKET_CANCELLED.
        """

        with self.uow:
            actor = self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_CANCELLED,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            ticket_user = self._load_linked_ticket_user(
                ticket=ticket,
            )

            changed_ticket_user = self.ticket_service.cancel(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                comment=ticket_dto.comment,
            )

            return self._save_and_to_dto(
                ticket=ticket,
                ticket_user=changed_ticket_user,
            )

    # ==================================================================
    # Queries
    # ==================================================================

    def get_by_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            ticket = self._get_ticket(
                ticket_dto.ticket_id,
            )

            return TicketAssembler.to_dto(
                ticket
            )

    def get_all(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_all()
            )

    def get_by_client_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_by_client_id(
                    ticket_dto.client_id,
                )
            )

    def get_by_user_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_by_user_id(
                    ticket_dto.user_id,
                )
            )

    def get_by_contact_user_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_by_contact_user_id(
                    ticket_dto.contact_user_id,
                )
            )

    def get_by_department_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_by_department_id(
                    ticket_dto.department_id,
                )
            )

    def get_by_current_executor(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_by_current_executor(
                    executor_id=ticket_dto.executor_id,
                )
            )

    def get_open(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_open()
            )

    def get_closed(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self.actor.require_actor_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
                permission=AdminPermission.TICKET_VIEW,
            )

            return self._to_dto_list(
                self.uow.tickets.get_finished()
            )

    # ==================================================================
    # External reference validation
    # ==================================================================

    def _validate_create_references(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> None:
        """
        Validate external aggregates referenced by a new Ticket.

        Referenced aggregates are read-only in this use case,
        therefore touch() protects the decision from concurrent change.
        """

        if ticket_dto.client_id <= 0:
            raise DomainOperationError(
                "client_id must be positive"
            )

        client = self.uow.clients.get(
            ticket_dto.client_id,
        )

        if not client.enabled:
            raise DomainOperationError(
                "Cannot create Ticket for disabled Client"
            )

        user = None

        if ticket_dto.user_id > 0:
            user = self.uow.users.get(
                ticket_dto.user_id,
            )

            user.can_do_operation()

            if user.client_id != client.client_id:
                raise DomainOperationError(
                    "User does not belong to Ticket Client"
                )

        contact_user = None

        if ticket_dto.contact_user_id > 0:
            if (
                user is not None
                and user.employee_id
                == ticket_dto.contact_user_id
            ):
                contact_user = user

            else:
                contact_user = self.uow.users.get(
                    ticket_dto.contact_user_id,
                )

                contact_user.can_do_operation()

                if contact_user.client_id != client.client_id:
                    raise DomainOperationError(
                        "Contact User does not belong "
                        "to Ticket Client"
                    )

        department = None

        if ticket_dto.department_id > 0:
            department = self.uow.departments.get(
                ticket_dto.department_id,
            )

            department.ensure_enabled()

        # --------------------------------------------------------------
        # Optimistic concurrency guards
        # --------------------------------------------------------------

        self.uow.clients.touch(
            client
        )

        if user is not None:
            self.uow.users.touch(
                user
            )

        if (
            contact_user is not None
            and (
                user is None
                or contact_user.employee_id
                != user.employee_id
            )
        ):
            self.uow.users.touch(
                contact_user
            )

        if department is not None:
            self.uow.departments.touch(
                department
            )

    # ==================================================================
    # Loading
    # ==================================================================

    def _get_ticket(
        self,
        ticket_id: int,
    ) -> Ticket:
        if ticket_id <= 0:
            raise DomainOperationError(
                "ticket_id must be positive"
            )

        return self.uow.tickets.get(
            ticket_id
        )

    def _load_linked_ticket_user(
        self,
        *,
        ticket: Ticket,
    ) -> TicketUser | None:
        """
        Load linked TicketUser.

        Structural consistency is checked by TicketService
        before mutation.
        """

        if ticket.user_ticket_id == 0:
            return None

        return self.uow.user_tickets.get(
            ticket.user_ticket_id
        )

    # ==================================================================
    # Persistence
    # ==================================================================

    def _save_and_to_dto(
        self,
        *,
        ticket: Ticket,
        ticket_user: TicketUser | None = None,
    ) -> TicketResponseDTO:
        """
        Persist changed aggregates in the current UoW transaction.
        """

        if ticket_user is not None:
            self.uow.user_tickets.save(
                ticket_user
            )

        saved_ticket = self.uow.tickets.save(
            ticket
        )

        self.uow.commit()

        if saved_ticket is None:
            saved_ticket = ticket

        return TicketAssembler.to_dto(
            saved_ticket
        )

    @staticmethod
    def _to_dto_list(
        tickets: list[Ticket],
    ) -> list[TicketResponseDTO]:
        return [
            TicketAssembler.to_dto(ticket)
            for ticket in tickets
        ]