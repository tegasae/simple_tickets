# src/application/services/ticket_application_service.py

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.application.assemblers.assembler import TicketAssembler
from src.application.dto.ticket_dto import TicketDTO, TicketResponseDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket import TicketPolicy

from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_execution_service import TicketExecutionService
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.services.ticket_review_service import TicketReviewService
from src.domain.services.ticket_user_sync_service import TicketUserSyncService
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment
from src.domain.ticket_user import TicketUser
from src.domain.uow.unit_of_work import UnitOfWork


class TicketApplicationService:
    """
    Application service для внутренней Ticket.

    Отвечает за:
    - permission checks;
    - загрузку агрегатов через UnitOfWork;
    - cross-aggregate validation;
    - вызов domain services;
    - сохранение Ticket;
    - синхронизацию TicketUser, если Ticket связана с TicketUser.

    Не отвечает за:
    - workflow-граф статусов;
    - ручное создание status records;
    - SQL;
    - repository-логику.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow
        self.actor = EmployeeActorHelper(self.uow)

    # --------------------------------
    # Create
    # --------------------------------

    def create_ticket(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        Admin создаёт обычную внутреннюю Ticket.

        Этот метод не создаёт TicketUser.

        Если нужна пользовательская заявка, созданная пользователем,
        используй TicketUserApplicationService.create_from_user(...).

        Если Admin создаёт заявку для User с пользовательским отображением,
        это лучше оформить отдельным use case.
        """
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            if ticket_dto.user_ticket_id != 0:
                raise DomainOperationError(
                    "create_ticket cannot create Ticket linked to existing "
                    "TicketUser. Use TicketUserApplicationService instead."
                )

            effective_admin_id = self._effective_admin_id_for_create(
                ticket_dto=ticket_dto,
            )

            self._validate_create_references(
                ticket_dto=ticket_dto,
                effective_admin_id=effective_admin_id,
            )

            ticket = Ticket.create(
                ticket_id=ticket_dto.ticket_id,
                client_id=ticket_dto.client_id,
                admin_id=effective_admin_id,
                text_of_ticket=ticket_dto.text_of_ticket,
                user_id=ticket_dto.user_id,
                contact_user_id=ticket_dto.contact_user_id,
                department_id=self._dto_attr(
                    ticket_dto,
                    "department_id",
                    default=0,
                ),
                is_remote=ticket_dto.is_remote,
                description=self._dto_attr(
                    ticket_dto,
                    "description",
                    default="",
                ),
                urgency_level=ticket_dto.urgency_level,
            )

            return self._save_commit_and_to_dto(ticket)

    # --------------------------------
    # Management status operations
    # --------------------------------

    def accept(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            if ticket.user_ticket_id != 0:
                TicketPolicy.ensure_ticket_has_no_admin_yet(
                    ticket=ticket,
                )

            TicketManagementService.accept(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def reject(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        if not ticket_dto.comment.strip():
            raise DomainOperationError(
                "Reject ticket requires comment",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketManagementService.reject(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def defer(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        if not ticket_dto.comment.strip():
            raise DomainOperationError(
                "Defer ticket requires comment",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketManagementService.defer(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def schedule(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        planned_start_at = self._required_dto_attr(
            ticket_dto,
            "planned_start_at",
        )
        planned_finish_at = self._dto_attr(
            ticket_dto,
            "planned_finish_at",
            default=None,
        )

        if not isinstance(planned_start_at, datetime):
            raise DomainOperationError(
                "planned_start_at must be datetime",
            )

        if (
            planned_finish_at is not None
            and not isinstance(planned_finish_at, datetime)
        ):
            raise DomainOperationError(
                "planned_finish_at must be datetime or None",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketManagementService.schedule(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                planned_start_at=planned_start_at,
                planned_finish_at=planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def assign_executor(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            self._ensure_executor_valid(
                executor_id=ticket_dto.executor_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketManagementService.assign(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                executor_id=ticket_dto.executor_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def ready_to_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        planned_start_at = self._required_dto_attr(
            ticket_dto,
            "planned_start_at",
        )
        planned_finish_at = self._dto_attr(
            ticket_dto,
            "planned_finish_at",
            default=None,
        )

        if not isinstance(planned_start_at, datetime):
            raise DomainOperationError(
                "planned_start_at must be datetime",
            )

        if (
            planned_finish_at is not None
            and not isinstance(planned_finish_at, datetime)
        ):
            raise DomainOperationError(
                "planned_finish_at must be datetime or None",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            self._ensure_executor_valid(
                executor_id=ticket_dto.executor_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketManagementService.ready_to_work(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                executor_id=ticket_dto.executor_id,
                planned_start_at=planned_start_at,
                planned_finish_at=planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def cancel(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        if not ticket_dto.comment.strip():
            raise DomainOperationError(
                "Cancel ticket requires comment",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketManagementService.cancel(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    # --------------------------------
    # Execution operations
    # --------------------------------

    def at_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        ASSIGNED / READY_TO_WORK -> AT_WORK

        Действие выполняет текущий executor.
        Поэтому actor_admin_id должен быть current executor.
        """
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketExecutionService.take_to_work(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def pause_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketExecutionService.pause_work(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def resume_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketExecutionService.resume_work(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def submit_for_review(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketExecutionService.submit_for_review(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def record_completed_work_for_review(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        actual_started_at = self._required_dto_attr(
            ticket_dto,
            "actual_started_at",
        )
        actual_finished_at = self._required_dto_attr(
            ticket_dto,
            "actual_finished_at",
        )

        if not isinstance(actual_started_at, datetime):
            raise DomainOperationError(
                "actual_started_at must be datetime",
            )

        if not isinstance(actual_finished_at, datetime):
            raise DomainOperationError(
                "actual_finished_at must be datetime",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            self._ensure_executor_valid(
                executor_id=ticket_dto.executor_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketExecutionService.record_completed_work_for_review(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                executor_id=ticket_dto.executor_id,
                actual_started_at=actual_started_at,
                actual_finished_at=actual_finished_at,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    # --------------------------------
    # Review operations
    # --------------------------------

    def execute(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        """
        READY_FOR_REVIEW -> EXECUTED

        Старое имя метода оставлено как публичный API.
        По смыслу это confirm_execution.
        """
        return self.confirm_execution(
            ticket_dto=ticket_dto,
        )

    def confirm_execution(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketReviewService.confirm_execution(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def return_to_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketReviewService.return_to_work(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def return_to_assigned(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            self._ensure_executor_valid(
                executor_id=ticket_dto.executor_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketReviewService.return_to_assigned(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                executor_id=ticket_dto.executor_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def return_to_scheduled(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        planned_start_at = self._required_dto_attr(
            ticket_dto,
            "planned_start_at",
        )
        planned_finish_at = self._dto_attr(
            ticket_dto,
            "planned_finish_at",
            default=None,
        )

        if not isinstance(planned_start_at, datetime):
            raise DomainOperationError(
                "planned_start_at must be datetime",
            )

        if (
            planned_finish_at is not None
            and not isinstance(planned_finish_at, datetime)
        ):
            raise DomainOperationError(
                "planned_finish_at must be datetime or None",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketReviewService.return_to_scheduled(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                planned_start_at=planned_start_at,
                planned_finish_at=planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def return_to_ready_to_work(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        planned_start_at = self._required_dto_attr(
            ticket_dto,
            "planned_start_at",
        )
        planned_finish_at = self._dto_attr(
            ticket_dto,
            "planned_finish_at",
            default=None,
        )

        if not isinstance(planned_start_at, datetime):
            raise DomainOperationError(
                "planned_start_at must be datetime",
            )

        if (
            planned_finish_at is not None
            and not isinstance(planned_finish_at, datetime)
        ):
            raise DomainOperationError(
                "planned_finish_at must be datetime or None",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )
            self._ensure_executor_valid(
                executor_id=ticket_dto.executor_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketReviewService.return_to_ready_to_work(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                executor_id=ticket_dto.executor_id,
                planned_start_at=planned_start_at,
                planned_finish_at=planned_finish_at,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    def return_to_deferred(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        if not ticket_dto.comment.strip():
            raise DomainOperationError(
                "Return to deferred requires comment",
            )

        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketReviewService.return_to_deferred(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

            return self._save_sync_commit_and_to_dto(
                ticket=ticket,
                actor_employee_id=ticket_dto.actor_admin_id,
                comment=ticket_dto.comment,
            )

    # --------------------------------
    # Comments
    # --------------------------------

    def add_comment(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            ticket.add_comment(
                Comment(
                    employee_id=ticket_dto.actor_admin_id,
                    comment=ticket_dto.comment,
                ),
            )

            return self._save_commit_and_to_dto(ticket)

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> None:
        """
        Удаляем только несвязанную внутреннюю Ticket.

        Связанную TicketUser здесь не удаляем.
        TicketUser — это отдельная пользовательская история.
        """
        with self.uow:
            self._require_operation_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            TicketPolicy.ensure_ticket_has_no_ticket_user(
                ticket=ticket,
            )

            self.uow.tickets.delete(ticket.ticket_id)
            self.uow.commit()

    # --------------------------------
    # Queries
    # --------------------------------

    def get_by_id(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> TicketResponseDTO:
        with self.uow:
            self._require_view_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            ticket = self._get_ticket(ticket_dto.ticket_id)

            return TicketAssembler.to_dto(ticket)

    def get_all(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> list[TicketResponseDTO]:
        with self.uow:
            self._require_view_admin(
                actor_admin_id=ticket_dto.actor_admin_id,
            )

            tickets = self.uow.tickets.get_all()

            return [
                TicketAssembler.to_dto(ticket)
                for ticket in tickets
            ]

    # --------------------------------
    # Internal helpers
    # --------------------------------

    def _require_operation_admin(
        self,
        *,
        actor_admin_id: int,
    ) -> None:
        actor = self.actor.require_actor_admin(
            actor_admin_id=actor_admin_id,
            permission=AdminPermission.TICKET_OPERATION,
        )

        TicketPolicy.ensure_admin_enabled(actor)

    def _require_view_admin(
        self,
        *,
        actor_admin_id: int,
    ) -> None:
        actor = self.actor.require_actor_admin(
            actor_admin_id=actor_admin_id,
            permission=AdminPermission.TICKET_VIEW,
        )

        TicketPolicy.ensure_admin_enabled(actor)

    def _validate_create_references(
        self,
        *,
        ticket_dto: TicketDTO,
        effective_admin_id: int,
    ) -> None:
        admin = self.uow.admins.get(effective_admin_id)
        TicketPolicy.ensure_admin_enabled(admin)

        client = self.uow.clients.get(ticket_dto.client_id)
        TicketPolicy.ensure_client_enabled(client)

        if ticket_dto.user_id != 0:
            user = self.uow.users.get(ticket_dto.user_id)
            TicketPolicy.ensure_user_enabled(user)
            TicketPolicy.ensure_user_belongs_to_client(
                user=user,
                client=client,
            )

        if ticket_dto.contact_user_id != 0:
            contact_user = self.uow.users.get(ticket_dto.contact_user_id)
            TicketPolicy.ensure_user_enabled(contact_user)
            TicketPolicy.ensure_contact_user_belongs_to_client(
                contact_user=contact_user,
                client=client,
            )

        department_id = self._dto_attr(
            ticket_dto,
            "department_id",
            default=0,
        )
        self._ensure_department_valid(
            department_id=department_id,
        )

    def _effective_admin_id_for_create(
        self,
        *,
        ticket_dto: TicketDTO,
    ) -> int:
        if ticket_dto.admin_id != 0:
            return ticket_dto.admin_id

        return ticket_dto.actor_admin_id

    def _ensure_department_valid(
        self,
        *,
        department_id: int,
    ) -> None:
        if department_id == 0:
            return

        self.uow.departments.get(department_id)

    def _ensure_executor_valid(
        self,
        *,
        executor_id: int,
    ) -> None:
        executor = self.uow.admins.get(executor_id)
        TicketPolicy.ensure_admin_enabled(executor)

    def _get_ticket(
        self,
        ticket_id: int,
    ) -> Ticket:
        return self.uow.tickets.get(ticket_id)

    def _load_linked_ticket_user(
        self,
        *,
        ticket: Ticket,
    ) -> TicketUser | None:
        if ticket.user_ticket_id == 0:
            return None

        ticket_user = self.uow.user_tickets.get(
            ticket.user_ticket_id,
        )

        TicketPolicy.ensure_ticket_matches_ticket_user(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        return ticket_user

    def _sync_linked_ticket_user(
        self,
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> bool:
        ticket_user = self._load_linked_ticket_user(
            ticket=ticket,
        )

        if ticket_user is None:
            return False

        ticket_user_changed = TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        if ticket_user_changed:
            self.uow.user_tickets.save(ticket_user)

        return ticket_user_changed

    def _save_sync_commit_and_to_dto(
        self,
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketResponseDTO:
        self._sync_linked_ticket_user(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return self._save_commit_and_to_dto(ticket)

    def _save_commit_and_to_dto(
        self,
        ticket: Ticket,
    ) -> TicketResponseDTO:
        saved_ticket = self.uow.tickets.save(
            ticket=ticket,
        )

        self.uow.commit()

        if saved_ticket is None:
            saved_ticket = ticket

        return TicketAssembler.to_dto(saved_ticket)

    @staticmethod
    def _dto_attr(
        ticket_dto: TicketDTO,
        name: str,
        *,
        default: Any,
    ) -> Any:
        return getattr(
            ticket_dto,
            name,
            default,
        )

    @staticmethod
    def _required_dto_attr(
        ticket_dto: TicketDTO,
        name: str,
    ) -> Any:
        value = getattr(
            ticket_dto,
            name,
            None,
        )

        if value is None:
            raise DomainOperationError(
                f"TicketDTO.{name} is required",
            )

        return value

