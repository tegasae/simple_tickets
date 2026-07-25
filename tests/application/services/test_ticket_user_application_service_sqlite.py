# tests/application/services/test_ticket_user_application_service_sqlite.py

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.ticket_dto import TicketUserDTO

from src.application.services.ticket_user_service import TicketUserApplicationService
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import UserPermission

from src.domain.statuses.ticket_status import TicketStatus
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
            name
        )
        VALUES (
            {CLIENT_ID},
            {ADMIN_ID},
            'Acme'
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

    assert [comment.comment for comment in ticket_user.comments] == [
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