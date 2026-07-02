from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_managment_service import (
    TicketManagementApplicationService,
)
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from utils.db.connect import Connection


ACTOR_ADMIN_ID = 10

EXECUTOR_ID = 20
DISABLED_EXECUTOR_ID = 30
OTHER_DEPARTMENT_EXECUTOR_ID = 40

CLIENT_ID = 100

SUPPORT_DEPARTMENT_ID = 1
INFRASTRUCTURE_DEPARTMENT_ID = 2


class AllowTicketOperationActor:
    """
    RBAC is tested separately.

    This stub verifies that management commands request
    the current generic Ticket permission and returns an actor.
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
def ticket_management_uow(
    ticket_command_connection: Connection,
) -> SQLiteUnitOfWork:
    """
    ticket_command_connection already contains:
        - departments 1, 2, 3;
        - actor Admin 10;
        - active Client 100.

    Add executors required only by management use cases.
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
                'SupportEngineer',
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
                'InfrastructureEngineer',
                'david@example.com',
                '+10000000040',
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
            (30, 'Disabled engineer', 1),
            (40, 'Infrastructure engineer', 2);
        """
    )
    ticket_command_connection.connect.commit()

    return SQLiteUnitOfWork(
        connection=ticket_command_connection,
    )


@pytest.fixture
def ticket_management_service(
    ticket_management_uow: SQLiteUnitOfWork,
) -> tuple[
    TicketManagementApplicationService,
    AllowTicketOperationActor,
]:
    service = TicketManagementApplicationService(
        uow=ticket_management_uow,
    )

    actor = AllowTicketOperationActor()
    service.actor = actor  # type: ignore[assignment]

    return service, actor


def create_created_ticket(
    uow: SQLiteUnitOfWork,
    *,
    department_id: int = SUPPORT_DEPARTMENT_ID,
) -> int:
    with uow:
        ticket = Ticket.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=ACTOR_ADMIN_ID,
            department_id=department_id,
            text_of_ticket="Office network is unavailable",
            description="Third-floor office",
        )

        saved = uow.tickets.save(ticket)

    return saved.ticket_id


def accept_ticket(
    service: TicketManagementApplicationService,
    *,
    ticket_id: int,
) -> None:
    service.accept_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            comment="Ticket accepted",
        )
    )


def load_ticket(
    uow: SQLiteUnitOfWork,
    *,
    ticket_id: int,
) -> Ticket:
    with uow:
        return uow.tickets.get(ticket_id=ticket_id)


def assert_ticket_operation_calls(
    actor: AllowTicketOperationActor,
    *,
    count: int,
) -> None:
    assert len(actor.calls) == count

    assert all(
        call["actor_admin_id"] == ACTOR_ADMIN_ID
        and call["permission"] is AdminPermission.TICKET_OPERATION
        for call in actor.calls
    )


def test_accept_ticket_persists_accepted_status(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    response = service.accept_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            comment="Ticket accepted",
        )
    )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert ticket.statuses[-1].actor_employee_id == ACTOR_ADMIN_ID
    assert ticket.statuses[-1].comment == "Ticket accepted"

    assert response.ticket_id == ticket_id
    assert response.statuses[-1]["status"] == TicketStatus.ACCEPTED.value

    assert_ticket_operation_calls(actor, count=1)


def test_reject_ticket_persists_terminal_status(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    service.reject_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            comment="Request has insufficient information",
        )
    )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.REJECTED
    assert ticket.is_terminal() is True
    assert ticket.is_closed is True
    assert ticket.statuses[-1].comment == (
        "Request has insufficient information"
    )

    assert_ticket_operation_calls(actor, count=1)


def test_schedule_ticket_persists_planned_interval(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    accept_ticket(service, ticket_id=ticket_id)

    planned_start_at = datetime.now(timezone.utc) + timedelta(hours=2)
    planned_finish_at = planned_start_at + timedelta(hours=3)

    response = service.schedule_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="Visit scheduled for tomorrow",
        )
    )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )
    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0

    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "Visit scheduled for tomorrow"

    assert response.statuses[-1]["status"] == TicketStatus.SCHEDULED.value
    assert_ticket_operation_calls(actor, count=2)


def test_assign_executor_persists_current_executor(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    accept_ticket(service, ticket_id=ticket_id)

    response = service.assign_executor(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            executor_id=EXECUTOR_ID,
            comment="Assigned to Bob",
        )
    )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID

    record = ticket.current_status_record()
    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.comment == "Assigned to Bob"

    assert response.statuses[-1]["status"] == TicketStatus.ASSIGNED.value
    assert response.statuses[-1]["executor_id"] == EXECUTOR_ID

    assert_ticket_operation_calls(actor, count=2)


def test_ready_to_work_persists_executor_and_plan(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    accept_ticket(service, ticket_id=ticket_id)

    planned_start_at = datetime.now(timezone.utc) + timedelta(hours=1)
    planned_finish_at = planned_start_at + timedelta(hours=2)

    response = service.ready_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            executor_id=EXECUTOR_ID,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="Engineer is ready to start",
        )
    )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )
    record = ticket.current_status_record()

    assert ticket.current_status() is TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID

    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "Engineer is ready to start"

    assert response.statuses[-1]["status"] == (
        TicketStatus.READY_TO_WORK.value
    )
    assert response.statuses[-1]["executor_id"] == EXECUTOR_ID

    assert_ticket_operation_calls(actor, count=2)


def test_defer_ticket_persists_reason(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    accept_ticket(service, ticket_id=ticket_id)

    service.defer_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            comment="Waiting for access approval",
        )
    )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.DEFERRED
    assert ticket.is_terminal() is False
    assert ticket.current_status_record().comment == (
        "Waiting for access approval"
    )

    assert_ticket_operation_calls(actor, count=2)


def test_cancel_ticket_persists_terminal_status(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    accept_ticket(service, ticket_id=ticket_id)

    service.cancel_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
            comment="Duplicate ticket",
        )
    )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.CANCELLED
    assert ticket.is_terminal() is True
    assert ticket.is_closed is True
    assert ticket.current_status_record().comment == "Duplicate ticket"

    assert_ticket_operation_calls(actor, count=2)


@pytest.mark.parametrize(
    ("executor_id", "expected_message"),
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
def test_assign_executor_rejects_invalid_executor_and_rolls_back(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
    executor_id: int,
    expected_message: str,
) -> None:
    service, _ = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    accept_ticket(service, ticket_id=ticket_id)

    with pytest.raises(
        DomainOperationError,
        match=expected_message,
    ):
        service.assign_executor(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=ticket_id,
                executor_id=executor_id,
                comment="Attempt invalid assignment",
            )
        )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert len(ticket.statuses) == 2


def test_management_operation_rejects_disabled_client_and_rolls_back(
    ticket_management_service,
    ticket_management_uow: SQLiteUnitOfWork,
    ticket_command_connection: Connection,
) -> None:
    service, _ = ticket_management_service
    ticket_id = create_created_ticket(ticket_management_uow)

    ticket_command_connection.connect.execute(
        """
        UPDATE clients
        SET enabled = 0
        WHERE client_id = ?
        """,
        (CLIENT_ID,),
    )
    ticket_command_connection.connect.commit()

    with pytest.raises(
        DomainOperationError,
        match="disabled",
    ):
        service.accept_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=ticket_id,
                comment="Must not be accepted",
            )
        )

    ticket = load_ticket(
        ticket_management_uow,
        ticket_id=ticket_id,
    )

    assert ticket.current_status() is TicketStatus.CREATED
    assert len(ticket.statuses) == 1