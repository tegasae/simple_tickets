from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_execution_service import (
    TicketExecutionApplicationService,
)
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_management_service import (
    TicketManagementService,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from utils.db.connect import Connection


MANAGER_ID = 10
EXECUTOR_ID = 20

CLIENT_ID = 100
DEPARTMENT_ID = 1


class AllowTicketOperationActor:
    """
    RBAC persistence is tested separately.

    This stub checks that each execution use case requests
    the current generic Ticket permission and returns the actor.
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
def ticket_execution_uow(
    ticket_command_connection: Connection,
) -> SQLiteUnitOfWork:
    """
    ticket_command_connection creates Admin 10, Client 100
    and Department 1.

    Execution tests additionally require a real executor Admin 20.
    The auxiliary account/role tables are needed by AdminRepositorySQLite.
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
        VALUES (
            20,
            'Bob',
            'Engineer',
            'bob@example.com',
            '+10000000020',
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
        VALUES (
            20,
            'Support engineer',
            1
        );
        """
    )
    ticket_command_connection.connect.commit()

    return SQLiteUnitOfWork(
        connection=ticket_command_connection,
    )


@pytest.fixture
def ticket_execution_service(
    ticket_execution_uow: SQLiteUnitOfWork,
) -> tuple[
    TicketExecutionApplicationService,
    AllowTicketOperationActor,
]:
    service = TicketExecutionApplicationService(
        uow=ticket_execution_uow,
    )

    actor = AllowTicketOperationActor()
    service.actor = actor  # type: ignore[assignment]

    return service, actor


def create_assigned_ticket(
    uow: SQLiteUnitOfWork,
) -> int:
    with uow:
        ticket = Ticket.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=MANAGER_ID,
            department_id=DEPARTMENT_ID,
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

        saved = uow.tickets.save(ticket)

    return saved.ticket_id


def create_scheduled_ticket(
    uow: SQLiteUnitOfWork,
) -> int:
    planned_start_at = datetime.now(timezone.utc) + timedelta(days=1)

    with uow:
        ticket = Ticket.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=MANAGER_ID,
            department_id=DEPARTMENT_ID,
            text_of_ticket="Printer requires maintenance",
            description="Office 305",
        )

        TicketManagementService.accept(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            comment="Accepted for processing",
        )

        TicketManagementService.schedule(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            planned_start_at=planned_start_at,
            comment="Maintenance scheduled",
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


def test_online_execution_workflow_persists_actual_times(
    ticket_execution_service,
    ticket_execution_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_execution_service
    ticket_id = create_assigned_ticket(ticket_execution_uow)

    started_response = service.take_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ID,
            ticket_id=ticket_id,
            comment="Started diagnostics",
        )
    )

    paused_response = service.pause_work(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ID,
            ticket_id=ticket_id,
            comment="Waiting for access to server room",
        )
    )

    resumed_response = service.resume_work(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ID,
            ticket_id=ticket_id,
            comment="Access received",
        )
    )

    review_response = service.submit_for_review(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ID,
            ticket_id=ticket_id,
            comment="Network connection restored",
        )
    )

    ticket = load_ticket(
        ticket_execution_uow,
        ticket_id=ticket_id,
    )

    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
        TicketStatus.ASSIGNED,
        TicketStatus.AT_WORK,
        TicketStatus.PAUSED,
        TicketStatus.AT_WORK,
        TicketStatus.READY_FOR_REVIEW,
    ]

    first_at_work = ticket.statuses[3]
    paused = ticket.statuses[4]
    resumed_at_work = ticket.statuses[5]
    ready_for_review = ticket.statuses[6]

    assert first_at_work.executor_id == EXECUTOR_ID
    assert first_at_work.actual_started_at is not None
    assert first_at_work.actual_finished_at is None
    assert first_at_work.comment == "Started diagnostics"

    assert paused.executor_id == EXECUTOR_ID
    assert paused.actual_started_at is None
    assert paused.actual_finished_at is None
    assert paused.comment == "Waiting for access to server room"

    assert resumed_at_work.executor_id == EXECUTOR_ID
    assert resumed_at_work.actual_started_at is not None
    assert resumed_at_work.actual_finished_at is None
    assert resumed_at_work.comment == "Access received"

    assert ready_for_review.executor_id == EXECUTOR_ID
    assert ready_for_review.actual_started_at is None
    assert ready_for_review.actual_finished_at is not None
    assert ready_for_review.comment == "Network connection restored"

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == EXECUTOR_ID

    assert started_response.statuses[-1]["status"] == (
        TicketStatus.AT_WORK.value
    )
    assert paused_response.statuses[-1]["status"] == (
        TicketStatus.PAUSED.value
    )
    assert resumed_response.statuses[-1]["status"] == (
        TicketStatus.AT_WORK.value
    )
    assert review_response.statuses[-1]["status"] == (
        TicketStatus.READY_FOR_REVIEW.value
    )

    assert_ticket_operation_calls(
        actor,
        actor_ids=[
            EXECUTOR_ID,
            EXECUTOR_ID,
            EXECUTOR_ID,
            EXECUTOR_ID,
        ],
    )


def test_record_completed_work_persists_given_actual_interval(
    ticket_execution_service,
    ticket_execution_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_execution_service
    ticket_id = create_scheduled_ticket(ticket_execution_uow)

    actual_started_at = (
        datetime.now(timezone.utc) - timedelta(hours=4)
    )
    actual_finished_at = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    )

    response = service.record_completed_work_for_review(
        ticket_dto=TicketDTO(
            actor_admin_id=MANAGER_ID,
            ticket_id=ticket_id,
            executor_id=EXECUTOR_ID,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            comment="Maintenance completed during the weekend",
        )
    )

    ticket = load_ticket(
        ticket_execution_uow,
        ticket_id=ticket_id,
    )

    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
        TicketStatus.SCHEDULED,
        TicketStatus.READY_FOR_REVIEW,
    ]

    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == EXECUTOR_ID

    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at == actual_started_at
    assert record.actual_finished_at == actual_finished_at
    assert record.comment == (
        "Maintenance completed during the weekend"
    )

    assert response.statuses[-1]["status"] == (
        TicketStatus.READY_FOR_REVIEW.value
    )
    assert response.statuses[-1]["executor_id"] == EXECUTOR_ID

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


def test_take_to_work_rejects_non_executor_and_rolls_back(
    ticket_execution_service,
    ticket_execution_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_execution_service
    ticket_id = create_assigned_ticket(ticket_execution_uow)

    with pytest.raises(
        DomainOperationError,
        match="Only current executor",
    ):
        service.take_to_work(
            ticket_dto=TicketDTO(
                actor_admin_id=MANAGER_ID,
                ticket_id=ticket_id,
                comment="Manager cannot start executor work",
            )
        )

    ticket = load_ticket(
        ticket_execution_uow,
        ticket_id=ticket_id,
    )

    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
        TicketStatus.ASSIGNED,
    ]
    assert ticket.current_status() is TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID

    assert_ticket_operation_calls(
        actor,
        actor_ids=[MANAGER_ID],
    )


@pytest.mark.parametrize(
    (
        "actual_started_at",
        "actual_finished_at",
    ),
    [
        (
            None,
            datetime.now(timezone.utc) - timedelta(hours=1),
        ),
        (
            datetime.now(timezone.utc) - timedelta(hours=2),
            None,
        ),
    ],
)
def test_record_completed_work_requires_complete_actual_interval(
    ticket_execution_service,
    ticket_execution_uow: SQLiteUnitOfWork,
    actual_started_at: datetime | None,
    actual_finished_at: datetime | None,
) -> None:
    service, _ = ticket_execution_service
    ticket_id = create_scheduled_ticket(ticket_execution_uow)

    with pytest.raises(DomainOperationError):
        service.record_completed_work_for_review(
            ticket_dto=TicketDTO(
                actor_admin_id=MANAGER_ID,
                ticket_id=ticket_id,
                executor_id=EXECUTOR_ID,
                actual_started_at=actual_started_at,
                actual_finished_at=actual_finished_at,
                comment="Incomplete retrospective record",
            )
        )

    ticket = load_ticket(
        ticket_execution_uow,
        ticket_id=ticket_id,
    )

    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
        TicketStatus.SCHEDULED,
    ]
    assert ticket.current_status() is TicketStatus.SCHEDULED