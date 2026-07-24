from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.ticket_dto import TicketUserDTO
from src.application.services.ticket_user_service import TicketUserApplicationService
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import UserPermission

from src.domain.services.ticket_user_sync_service import TicketUserSyncService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket_user import TicketUserStatus


CLIENT_ID = 1
USER_ID = 1
ADMIN_ID = 10


@dataclass(frozen=True)
class StubUser:
    employee_id: int
    client_id: int
    enabled: bool = True


class AllowAllActor:
    def require_actor_user(
        self,
        *,
        actor_user_id: int,
        permission: UserPermission,
    ) -> StubUser:
        return StubUser(
            employee_id=actor_user_id,
            client_id=CLIENT_ID,
            enabled=True,
        )


def prepare_reference_data(sqlite_schema) -> None:
    sqlite_schema.connect.executescript(
        f"""
        INSERT OR IGNORE INTO employees (
            employee_id,
            first_name,
            last_name,
            email,
            enabled,
            version,
            is_admin
        )
        VALUES
            (
                {USER_ID},
                'User',
                'One',
                'user1@example.com',
                1,
                0,
                0
            ),
            (
                {ADMIN_ID},
                'Admin',
                'One',
                'admin10@example.com',
                1,
                0,
                1
            );

        INSERT OR IGNORE INTO admins (
            employee_id,
            job_title,
            department_id
        )
        VALUES (
            {ADMIN_ID},
            'Manager',
            NULL
        );

        INSERT OR IGNORE INTO clients (
            client_id,
            admin_id,
            name,
            enabled
        )
        VALUES (
            {CLIENT_ID},
            {ADMIN_ID},
            'Acme',
            1
        );

        INSERT OR IGNORE INTO users (
            employee_id,
            client_id
        )
        VALUES (
            {USER_ID},
            {CLIENT_ID}
        );
        """
    )

    sqlite_schema.connect.execute(
        """
        UPDATE employees
        SET enabled = 1
        WHERE employee_id IN (?, ?)
        """,
        (USER_ID, ADMIN_ID),
    )

    sqlite_schema.connect.execute(
        """
        UPDATE clients
        SET enabled = 1
        WHERE client_id = ?
        """,
        (CLIENT_ID,),
    )

    sqlite_schema.connect.commit()


def make_service(sqlite_schema) -> TicketUserApplicationService:
    service = TicketUserApplicationService(
        uow=SQLiteUnitOfWork(sqlite_schema),
    )
    service.actor = AllowAllActor()
    return service


def make_create_dto(
    *,
    ticket_id: int = 0,
    ticket_user_id: int = 0,
) -> TicketUserDTO:
    return TicketUserDTO(
        ticket_id=ticket_id,
        ticket_user_id=ticket_user_id,
        actor_user_id=USER_ID,
        client_id=CLIENT_ID,
        contact_user_id=0,
        text_of_ticket="Need help",
        description="Created from service",
        urgency_level=2,
        department_id=0,
        is_remote=False,
        comment="Initial user comment",
    )


def make_cancel_dto(
    *,
    ticket_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        ticket_id=ticket_id,
        ticket_user_id=ticket_user_id,
        actor_user_id=USER_ID,
        client_id=CLIENT_ID,
        contact_user_id=0,
        text_of_ticket="",
        description="",
        urgency_level=0,
        department_id=0,
        is_remote=False,
        comment="Cancelled by user",
    )


def make_confirm_execution_dto(
    *,
    ticket_id: int,
    ticket_user_id: int,
) -> TicketUserDTO:
    return TicketUserDTO(
        ticket_id=ticket_id,
        ticket_user_id=ticket_user_id,
        actor_user_id=USER_ID,
        client_id=CLIENT_ID,
        contact_user_id=0,
        text_of_ticket="",
        description="",
        urgency_level=0,
        department_id=0,
        is_remote=False,
        comment="User confirms execution",
    )


def prepare_waiting_for_confirmation(
    *,
    sqlite_schema,
    service: TicketUserApplicationService,
) -> tuple[int, int]:
    created = service.create_from_user(
        ticket_user_dto=make_create_dto(),
    )

    now = datetime.now(timezone.utc)

    with SQLiteUnitOfWork(sqlite_schema) as uow:
        ticket_user = uow.user_tickets.get(created.ticket_id)
        ticket = uow.tickets.get_by_user_ticket_id(ticket_user.ticket_id)

        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.ACCEPTED,
                date_created=now,
            )
        )
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment="Accepted by admin",
        )

        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.READY_TO_WORK,
                executor_id=ADMIN_ID,
                planned_start_at=now + timedelta(hours=1),
                date_created=now + timedelta(minutes=1),
            )
        )
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment="Ready to work",
        )

        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.AT_WORK,
                executor_id=ADMIN_ID,
                actual_started_at=now + timedelta(minutes=2),
                date_created=now + timedelta(minutes=2),
            )
        )
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment="At work",
        )

        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.READY_FOR_REVIEW,
                executor_id=ADMIN_ID,
                actual_finished_at=now + timedelta(minutes=10),
                date_created=now + timedelta(minutes=10),
            )
        )
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment="Waiting for user confirmation",
        )

        uow.tickets.save(ticket)
        uow.user_tickets.save(ticket_user)

        return ticket.ticket_id, ticket_user.ticket_id


def test_create_from_user_creates_ticket_user_and_linked_ticket(
    sqlite_schema,
) -> None:
    prepare_reference_data(sqlite_schema)

    service = make_service(sqlite_schema)

    result = service.create_from_user(
        ticket_user_dto=make_create_dto(),
    )

    assert result.ticket_id > 0

    with SQLiteUnitOfWork(sqlite_schema) as uow:
        ticket_user = uow.user_tickets.get(result.ticket_id)
        ticket = uow.tickets.get_by_user_ticket_id(result.ticket_id)

    assert ticket_user.ticket_id == result.ticket_id
    assert ticket_user.client_id == CLIENT_ID
    assert ticket_user.user_id == USER_ID
    assert ticket_user.contact_user_id == 0
    assert ticket_user.text_of_ticket == "Need help"
    assert ticket_user.description == "Created from service"
    assert ticket_user.urgency_level == 2
    assert ticket_user.current_status() == TicketUserStatus.CREATED
    assert ticket_user.current_status_record().actor_employee_id == USER_ID

    assert [
        comment.comment
        for comment in ticket_user.comments
    ] == [
        "Initial user comment",
    ]

    assert ticket.ticket_id > 0
    assert ticket.user_ticket_id == ticket_user.ticket_id
    assert ticket.client_id == ticket_user.client_id
    assert ticket.user_id == ticket_user.user_id
    assert ticket.contact_user_id == ticket_user.contact_user_id
    assert ticket.text_of_ticket == ticket_user.text_of_ticket
    assert ticket.description == ticket_user.description
    assert ticket.urgency_level == ticket_user.urgency_level

    assert ticket.admin_id == 0
    assert ticket.current_status() == TicketStatus.CREATED_FROM_TICKET_USER
    assert ticket.current_status_record().actor_employee_id == 0


def test_create_from_user_rejects_nonzero_ticket_user_id(
    sqlite_schema,
) -> None:
    prepare_reference_data(sqlite_schema)

    service = make_service(sqlite_schema)

    with pytest.raises(DomainOperationError):
        service.create_from_user(
            ticket_user_dto=make_create_dto(
                ticket_user_id=123,
            ),
        )


def test_create_from_user_rejects_nonzero_ticket_id(
    sqlite_schema,
) -> None:
    prepare_reference_data(sqlite_schema)

    service = make_service(sqlite_schema)

    with pytest.raises(DomainOperationError):
        service.create_from_user(
            ticket_user_dto=make_create_dto(
                ticket_id=123,
            ),
        )


def test_cancel_by_user_cancels_ticket_user_and_linked_ticket(
    sqlite_schema,
) -> None:
    prepare_reference_data(sqlite_schema)

    service = make_service(sqlite_schema)

    created = service.create_from_user(
        ticket_user_dto=make_create_dto(),
    )

    with SQLiteUnitOfWork(sqlite_schema) as uow:
        ticket_user = uow.user_tickets.get(created.ticket_id)
        ticket = uow.tickets.get_by_user_ticket_id(ticket_user.ticket_id)

    result = service.cancel_by_user(
        ticket_user_dto=make_cancel_dto(
            ticket_id=ticket.ticket_id,
            ticket_user_id=ticket_user.ticket_id,
        ),
    )

    assert result.ticket_id == ticket_user.ticket_id
    assert result.ticket_user_id == ticket_user.ticket_id

    with SQLiteUnitOfWork(sqlite_schema) as uow:
        loaded_ticket_user = uow.user_tickets.get(ticket_user.ticket_id)
        loaded_ticket = uow.tickets.get(ticket.ticket_id)

    assert loaded_ticket_user.current_status() == (
        TicketUserStatus.CANCELLED_BY_USER
    )
    assert loaded_ticket_user.current_status_record().actor_employee_id == USER_ID
    assert loaded_ticket_user.current_status_record().comment == "Cancelled by user"
    assert loaded_ticket_user.is_closed is True
    assert loaded_ticket_user.date_finished == (
        loaded_ticket_user.current_status_record().date_created
    )

    assert loaded_ticket.current_status() == TicketStatus.CANCELLED_BY_USER
    assert loaded_ticket.current_status_record().actor_employee_id == 0
    assert loaded_ticket.current_status_record().comment == "Cancelled by user"
    assert loaded_ticket.is_closed is True
    assert loaded_ticket.date_finished == (
        loaded_ticket.current_status_record().date_created
    )

    assert [
        record.status
        for record in loaded_ticket_user.statuses
    ] == [
        TicketUserStatus.CREATED,
        TicketUserStatus.CANCELLED_BY_USER,
    ]

    assert [
        record.status
        for record in loaded_ticket.statuses
    ] == [
        TicketStatus.CREATED_FROM_TICKET_USER,
        TicketStatus.CANCELLED_BY_USER,
    ]


def test_confirm_execution_by_user_closes_ticket_user_and_linked_ticket(
    sqlite_schema,
) -> None:
    prepare_reference_data(sqlite_schema)

    service = make_service(sqlite_schema)

    ticket_id, ticket_user_id = prepare_waiting_for_confirmation(
        sqlite_schema=sqlite_schema,
        service=service,
    )

    result = service.confirm_execution_by_user(
        ticket_user_dto=make_confirm_execution_dto(
            ticket_id=ticket_id,
            ticket_user_id=ticket_user_id,
        ),
    )

    assert result.ticket_id == ticket_user_id
    assert result.ticket_user_id == ticket_user_id

    with SQLiteUnitOfWork(sqlite_schema) as uow:
        loaded_ticket_user = uow.user_tickets.get(ticket_user_id)
        loaded_ticket = uow.tickets.get(ticket_id)

    assert loaded_ticket_user.current_status() == (
        TicketUserStatus.EXECUTION_CONFIRMED_BY_USER
    )
    assert loaded_ticket_user.current_status_record().actor_employee_id == USER_ID
    assert loaded_ticket_user.current_status_record().comment == (
        "User confirms execution"
    )
    assert loaded_ticket_user.is_closed is True
    assert loaded_ticket_user.date_finished == (
        loaded_ticket_user.current_status_record().date_created
    )

    assert loaded_ticket.current_status() == TicketStatus.EXECUTED
    assert loaded_ticket.current_status_record().actor_employee_id == USER_ID
    assert loaded_ticket.current_status_record().comment == (
        "User confirms execution"
    )
    assert loaded_ticket.is_closed is True
    assert loaded_ticket.date_finished == (
        loaded_ticket.current_status_record().date_created
    )


def test_confirm_execution_by_user_does_not_mark_ticket_user_as_admin_confirmed(
    sqlite_schema,
) -> None:
    prepare_reference_data(sqlite_schema)

    service = make_service(sqlite_schema)

    ticket_id, ticket_user_id = prepare_waiting_for_confirmation(
        sqlite_schema=sqlite_schema,
        service=service,
    )

    service.confirm_execution_by_user(
        ticket_user_dto=make_confirm_execution_dto(
            ticket_id=ticket_id,
            ticket_user_id=ticket_user_id,
        ),
    )

    with SQLiteUnitOfWork(sqlite_schema) as uow:
        loaded_ticket_user = uow.user_tickets.get(ticket_user_id)

    assert [
        record.status
        for record in loaded_ticket_user.statuses
    ] == [
        TicketUserStatus.CREATED,
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.IN_WORK,
        TicketUserStatus.WAITING_FOR_CONFIRMATION,
        TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
    ]