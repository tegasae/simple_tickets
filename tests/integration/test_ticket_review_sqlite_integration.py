from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_review_service import (
    TicketReviewApplicationService,
)
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_execution_service import (
    TicketExecutionService,
)
from src.domain.services.ticket_management_service import (
    TicketManagementService,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from utils.db.connect import Connection


MANAGER_ID = 10

EXECUTOR_ID = 20
DISABLED_EXECUTOR_ID = 30
OTHER_EXECUTOR_ID = 40
OTHER_DEPARTMENT_EXECUTOR_ID = 50

CLIENT_ID = 100
SUPPORT_DEPARTMENT_ID = 1


class AllowTicketOperationActor:
    """
    Реальный RBAC проверяется отдельным integration module.

    Здесь проверяем, что application service запрашивает
    текущую generic permission для Ticket-операций.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def require_actor_admin(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> SimpleNamespace:
        self.calls.append(
            {
                "actor_admin_id": actor_admin_id,
                "permission": permission,
            }
        )

        assert permission is AdminPermission.TICKET_OPERATION

        return SimpleNamespace(
            employee_id=actor_admin_id,
        )


@pytest.fixture
def ticket_review_uow(
    ticket_command_connection: Connection,
) -> SQLiteUnitOfWork:
    """
    ticket_command_connection уже создаёт:

        - Department 1 (Support);
        - Admin 10 (Manager);
        - Client 100.

    Для review-переходов добавляем исполнителей:
        20 — активный, Support;
        30 — disabled, Support;
        40 — активный replacement executor, Support;
        50 — активный, но из другого Department.
    """

    ticket_command_connection.connect.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER UNIQUE,
            login TEXT UNIQUE,
            password TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            date_created TEXT,

            FOREIGN KEY (employee_id)
                REFERENCES employees(employee_id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            permissions TEXT,
            description TEXT,
            is_system_role INTEGER NOT NULL DEFAULT 0,
            date_created TEXT,
            is_admin INTEGER NOT NULL DEFAULT 1,
            version INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS admins_roles (
            employee_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,

            PRIMARY KEY (employee_id, role_id),

            FOREIGN KEY (employee_id)
                REFERENCES admins(employee_id)
                ON DELETE CASCADE,

            FOREIGN KEY (role_id)
                REFERENCES roles(role_id)
                ON DELETE CASCADE
        );

        INSERT INTO employees (
            employee_id,
            first_name,
            last_name,
            email,
            phone,
            date_created,
            enabled,
            version,
            is_admin
        )
        VALUES
            (
                20,
                'Bob',
                'Engineer',
                'bob@example.com',
                '+10000000020',
                '2026-01-01T00:00:00+00:00',
                1,
                0,
                1
            ),
            (
                30,
                'Carol',
                'DisabledEngineer',
                'carol@example.com',
                '+10000000030',
                '2026-01-01T00:00:00+00:00',
                0,
                0,
                1
            ),
            (
                40,
                'David',
                'ReplacementEngineer',
                'david@example.com',
                '+10000000040',
                '2026-01-01T00:00:00+00:00',
                1,
                0,
                1
            ),
            (
                50,
                'Eve',
                'InfrastructureEngineer',
                'eve@example.com',
                '+10000000050',
                '2026-01-01T00:00:00+00:00',
                1,
                0,
                1
            );

        INSERT INTO admins (
            employee_id,
            job_title,
            department_id
        )
        VALUES
            (20, 'Support engineer', 1),
            (30, 'Disabled support engineer', 1),
            (40, 'Replacement support engineer', 1),
            (50, 'Infrastructure engineer', 2);
        """
    )
    ticket_command_connection.connect.commit()

    return SQLiteUnitOfWork(
        connection=ticket_command_connection,
    )


@pytest.fixture
def ticket_review_service(
    ticket_review_uow: SQLiteUnitOfWork,
) -> tuple[
    TicketReviewApplicationService,
    AllowTicketOperationActor,
]:
    service = TicketReviewApplicationService(
        uow=ticket_review_uow,
    )

    actor = AllowTicketOperationActor()
    service.actor = actor  # type: ignore[assignment]

    return service, actor


def create_ready_for_review_ticket(
    uow: SQLiteUnitOfWork,
) -> int:
    with uow:
        ticket = Ticket.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=MANAGER_ID,
            department_id=SUPPORT_DEPARTMENT_ID,
            text_of_ticket="Office network is unavailable",
            description="Third-floor office",
        )

        TicketManagementService.accept(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            comment="Accepted for processing",
        )

        TicketManagementService.assign(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            executor_id=EXECUTOR_ID,
            comment="Assigned to support engineer",
        )

        TicketExecutionService.take_to_work(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
            comment="Started diagnostics",
        )

        TicketExecutionService.submit_for_review(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
            comment="Network connection restored",
        )

        saved = uow.tickets.save(ticket)

    return saved.ticket_id


def load_ticket(
    uow: SQLiteUnitOfWork,
    *,
    ticket_id: int,
) -> Ticket:
    with uow:
        return uow.tickets.get(
            ticket_id=ticket_id,
        )


def assert_ticket_operation_calls(
    actor: AllowTicketOperationActor,
    *,
    actor_ids: list[int],
) -> None:
    assert actor.calls == [
        {
            "actor_admin_id": actor_id,
            "permission": AdminPermission.TICKET_OPERATION,
        }
        for actor_id in actor_ids
    ]


def test_confirm_execution_persists_terminal_executed_status(
    ticket_review_service,
    ticket_review_uow: SQLiteUnitOfWork,
    ticket_command_connection: Connection,
) -> None:
    service, actor = ticket_review_service
    ticket_id = create_ready_for_review_ticket(
        ticket_review_uow,
    )

    # Disabled Client must not block final review of already completed work.
    ticket_command_connection.connect.execute(
        """
        UPDATE clients
        SET enabled = 0
        WHERE client_id = ?
        """,
        (CLIENT_ID,),
    )
    ticket_command_connection.connect.commit()

    response = service.confirm_execution(
        ticket_dto=TicketDTO(
            actor_admin_id=MANAGER_ID,
            ticket_id=ticket_id,
            comment="Result confirmed",
        )
    )

    ticket = load_ticket(
        ticket_review_uow,
        ticket_id=ticket_id,
    )

    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.EXECUTED
    assert ticket.is_terminal() is True
    assert ticket.is_closed is True
    assert ticket.current_executor_id() == 0

    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == 0
    assert record.comment == "Result confirmed"

    assert response.statuses[-1]["status"] == (
        TicketStatus.EXECUTED.value
    )

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


def test_return_to_work_keeps_current_executor_and_starts_new_interval(
    ticket_review_service,
    ticket_review_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_review_service
    ticket_id = create_ready_for_review_ticket(
        ticket_review_uow,
    )

    response = service.return_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=MANAGER_ID,
            ticket_id=ticket_id,
            comment="Please resolve the remaining issue",
        )
    )

    ticket = load_ticket(
        ticket_review_uow,
        ticket_id=ticket_id,
    )

    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID
    assert ticket.is_terminal() is False

    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at is not None
    assert record.actual_finished_at is None
    assert record.comment == "Please resolve the remaining issue"

    assert response.statuses[-1]["status"] == (
        TicketStatus.AT_WORK.value
    )
    assert response.statuses[-1]["executor_id"] == EXECUTOR_ID

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


def test_return_to_assigned_persists_replacement_executor(
    ticket_review_service,
    ticket_review_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_review_service
    ticket_id = create_ready_for_review_ticket(
        ticket_review_uow,
    )

    response = service.return_to_assigned(
        ticket_dto=TicketDTO(
            actor_admin_id=MANAGER_ID,
            ticket_id=ticket_id,
            executor_id=OTHER_EXECUTOR_ID,
            comment="Another specialist is required",
        )
    )

    ticket = load_ticket(
        ticket_review_uow,
        ticket_id=ticket_id,
    )

    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == OTHER_EXECUTOR_ID

    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == OTHER_EXECUTOR_ID
    assert record.comment == "Another specialist is required"

    assert response.statuses[-1]["status"] == (
        TicketStatus.ASSIGNED.value
    )
    assert response.statuses[-1]["executor_id"] == OTHER_EXECUTOR_ID

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


def test_return_to_scheduled_persists_new_plan_without_executor(
    ticket_review_service,
    ticket_review_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_review_service
    ticket_id = create_ready_for_review_ticket(
        ticket_review_uow,
    )

    planned_start_at = datetime.now(timezone.utc) + timedelta(days=1)
    planned_finish_at = planned_start_at + timedelta(hours=2)

    response = service.return_to_scheduled(
        ticket_dto=TicketDTO(
            actor_admin_id=MANAGER_ID,
            ticket_id=ticket_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="A new visit must be scheduled",
        )
    )

    ticket = load_ticket(
        ticket_review_uow,
        ticket_id=ticket_id,
    )

    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0

    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == 0
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "A new visit must be scheduled"

    assert response.statuses[-1]["status"] == (
        TicketStatus.SCHEDULED.value
    )

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


def test_return_to_ready_to_work_persists_executor_and_plan(
    ticket_review_service,
    ticket_review_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_review_service
    ticket_id = create_ready_for_review_ticket(
        ticket_review_uow,
    )

    planned_start_at = datetime.now(timezone.utc) + timedelta(hours=2)
    planned_finish_at = planned_start_at + timedelta(hours=3)

    response = service.return_to_ready_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=MANAGER_ID,
            ticket_id=ticket_id,
            executor_id=OTHER_EXECUTOR_ID,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="Prepare for repeat diagnostics",
        )
    )

    ticket = load_ticket(
        ticket_review_uow,
        ticket_id=ticket_id,
    )

    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == OTHER_EXECUTOR_ID

    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == OTHER_EXECUTOR_ID
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "Prepare for repeat diagnostics"

    assert response.statuses[-1]["status"] == (
        TicketStatus.READY_TO_WORK.value
    )
    assert response.statuses[-1]["executor_id"] == OTHER_EXECUTOR_ID

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


def test_return_to_deferred_persists_reason(
    ticket_review_service,
    ticket_review_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_review_service
    ticket_id = create_ready_for_review_ticket(
        ticket_review_uow,
    )

    response = service.return_to_deferred(
        ticket_dto=TicketDTO(
            actor_admin_id=MANAGER_ID,
            ticket_id=ticket_id,
            comment="Waiting for access approval",
        )
    )

    ticket = load_ticket(
        ticket_review_uow,
        ticket_id=ticket_id,
    )

    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.DEFERRED
    assert ticket.is_terminal() is False
    assert ticket.current_executor_id() == 0

    assert record.actor_employee_id == MANAGER_ID
    assert record.comment == "Waiting for access approval"

    assert response.statuses[-1]["status"] == (
        TicketStatus.DEFERRED.value
    )

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


@pytest.mark.parametrize(
    ("executor_id", "expected_error"),
    [
        (
            DISABLED_EXECUTOR_ID,
            "disabled",
        ),
        (
            OTHER_DEPARTMENT_EXECUTOR_ID,
            "department",
        ),
    ],
)
def test_return_to_assigned_rejects_invalid_executor_and_rolls_back(
    ticket_review_service,
    ticket_review_uow: SQLiteUnitOfWork,
    executor_id: int,
    expected_error: str,
) -> None:
    service, actor = ticket_review_service
    ticket_id = create_ready_for_review_ticket(
        ticket_review_uow,
    )

    with pytest.raises(
        DomainOperationError,
        match=expected_error,
    ):
        service.return_to_assigned(
            ticket_dto=TicketDTO(
                actor_admin_id=MANAGER_ID,
                ticket_id=ticket_id,
                executor_id=executor_id,
                comment="Invalid reassignment",
            )
        )

    ticket = load_ticket(
        ticket_review_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == EXECUTOR_ID
    assert len(ticket.statuses) == 5

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )