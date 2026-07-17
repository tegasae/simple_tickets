from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_query_service import (
    TicketQueryApplicationService,
)
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.services.ticket_management_service import (
    TicketManagementService,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from utils.db.connect import Connection


ACTOR_ADMIN_ID = 10
CLIENT_ID = 100

USER_ID = 40
USER_TICKET_ID = 500

SUPPORT_DEPARTMENT_ID = 1


class AllowTicketViewActor:
    """
    RBAC persistence is covered separately.

    This stub confirms that query use cases request TICKET_VIEW.
    """

    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
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

        if self.error is not None:
            raise self.error

        assert permission is AdminPermission.TICKET_VIEW

        return SimpleNamespace(
            employee_id=actor_admin_id,
        )


@pytest.fixture
def ticket_query_uow(
    ticket_command_connection: Connection,
) -> SQLiteUnitOfWork:
    """
    ticket_command_connection already contains:

        - Admin 10;
        - Client 100;
        - Department 1.

    get_by_user_ticket_id needs a real linked UserTicket.
    """

    ticket_command_connection.connect.executescript(
        """
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
            40,
            'David',
            'ClientUser',
            'david@example.com',
            '+10000000040',
            '2026-01-01T00:00:00+00:00',
            1,
            0,
            0
        );

        INSERT INTO users (
            employee_id,
            client_id
        )
        VALUES (
            40,
            100
        );

        INSERT INTO user_tickets (
            user_ticket_id,
            client_id,
            user_id,
            user_ticket_contact_user_id,
            text_of_ticket,
            date_created,
            version,
            is_closed
        )
        VALUES (
            500,
            100,
            40,
            40,
            'The network is unavailable',
            '2026-01-01T00:00:00+00:00',
            0,
            0
        );
        """
    )
    ticket_command_connection.connect.commit()

    return SQLiteUnitOfWork(
        connection=ticket_command_connection,
    )


@pytest.fixture
def ticket_query_service(
    ticket_query_uow: SQLiteUnitOfWork,
) -> tuple[
    TicketQueryApplicationService,
    AllowTicketViewActor,
]:
    service = TicketQueryApplicationService(
        uow=ticket_query_uow,
    )

    actor = AllowTicketViewActor()
    service.actor = actor  # type: ignore[assignment]

    return service, actor


def create_ticket(
    uow: SQLiteUnitOfWork,
    *,
    text_of_ticket: str,
    description: str = "",
    user_id: int = 0,
    contact_user_id: int = 0,
    user_ticket_id: int = 0,
    initial_comment: str = "",
    accept: bool = False,
) -> int:
    with uow:
        ticket = Ticket.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=ACTOR_ADMIN_ID,
            user_id=user_id,
            contact_user_id=contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=SUPPORT_DEPARTMENT_ID,
            text_of_ticket=text_of_ticket,
            description=description,
            comment=initial_comment,
        )

        if accept:
            TicketManagementService.accept(
                ticket=ticket,
                actor_employee_id=ACTOR_ADMIN_ID,
                comment="Accepted for processing",
            )

        saved = uow.tickets.save(ticket)

    return saved.ticket_id


def assert_ticket_view_requested(
    actor: AllowTicketViewActor,
    *,
    count: int,
) -> None:
    assert actor.calls == [
        {
            "actor_admin_id": ACTOR_ADMIN_ID,
            "permission": AdminPermission.TICKET_VIEW,
        }
        for _ in range(count)
    ]


def test_get_by_id_loads_complete_ticket_response_from_sqlite(
    ticket_query_service,
    ticket_query_uow: SQLiteUnitOfWork,
    ticket_command_connection: Connection,
) -> None:
    service, actor = ticket_query_service

    ticket_id = create_ticket(
        ticket_query_uow,
        text_of_ticket="Office network is unavailable",
        description="Third-floor office",
        initial_comment="Registered by phone",
        accept=True,
    )

    version_before = ticket_command_connection.connect.execute(
        """
        SELECT version
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    ).fetchone()[0]

    response = service.get_by_id(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
        )
    )

    version_after = ticket_command_connection.connect.execute(
        """
        SELECT version
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    ).fetchone()[0]

    assert response.ticket_id == ticket_id
    assert response.client_id == CLIENT_ID
    assert response.admin_id == ACTOR_ADMIN_ID
    assert response.department_id == SUPPORT_DEPARTMENT_ID

    assert response.text_of_ticket == "Office network is unavailable"
    assert response.description == "Third-floor office"

    assert response.is_closed is False
    assert response.version == 0

    assert [record["status"] for record in response.statuses] == [
        TicketStatus.CREATED.value,
        TicketStatus.ACCEPTED.value,
    ]

    assert response.statuses[0]["actor_id"] == ACTOR_ADMIN_ID
    assert response.statuses[1]["comment"] == "Accepted for processing"

    assert [comment["comment"] for comment in response.comments] == [
        "Registered by phone",
    ]
    assert response.comments[0]["actor_id"] == ACTOR_ADMIN_ID

    # Query must not update the aggregate root.
    assert version_after == version_before == 0

    assert_ticket_view_requested(
        actor,
        count=1,
    )


def test_get_all_loads_all_ticket_responses_from_sqlite(
    ticket_query_service,
    ticket_query_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_query_service

    first_ticket_id = create_ticket(
        ticket_query_uow,
        text_of_ticket="First ticket",
    )
    second_ticket_id = create_ticket(
        ticket_query_uow,
        text_of_ticket="Second ticket",
        accept=True,
    )

    response = service.get_all(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
        )
    )

    by_id = {
        ticket.ticket_id: ticket
        for ticket in response
    }

    assert set(by_id) == {
        first_ticket_id,
        second_ticket_id,
    }

    assert by_id[first_ticket_id].text_of_ticket == "First ticket"
    assert by_id[first_ticket_id].statuses[-1]["status"] == (
        TicketStatus.CREATED.value
    )

    assert by_id[second_ticket_id].text_of_ticket == "Second ticket"
    assert by_id[second_ticket_id].statuses[-1]["status"] == (
        TicketStatus.ACCEPTED.value
    )

    assert_ticket_view_requested(
        actor,
        count=1,
    )


def test_get_all_returns_empty_list_when_database_has_no_tickets(
    ticket_query_service,
) -> None:
    service, actor = ticket_query_service

    response = service.get_all(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
        )
    )

    assert response == []

    assert_ticket_view_requested(
        actor,
        count=1,
    )


def test_get_by_user_ticket_id_loads_linked_ticket_from_sqlite(
    ticket_query_service,
    ticket_query_uow: SQLiteUnitOfWork,
) -> None:
    service, actor = ticket_query_service

    ticket_id = create_ticket(
        ticket_query_uow,
        text_of_ticket="Network request from user portal",
        user_id=USER_ID,
        contact_user_id=USER_ID,
        user_ticket_id=USER_TICKET_ID,
        initial_comment="Created from user ticket",
    )

    response = service.get_by_user_ticket_id(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            user_ticket_id=USER_TICKET_ID,
        )
    )

    assert response.ticket_id == ticket_id
    assert response.client_id == CLIENT_ID
    assert response.user_id == USER_ID
    assert response.contact_user_id == USER_ID
    assert response.user_ticket_id == USER_TICKET_ID

    assert response.text_of_ticket == (
        "Network request from user portal"
    )

    assert [comment["comment"] for comment in response.comments] == [
        "Created from user ticket",
    ]

    assert_ticket_view_requested(
        actor,
        count=1,
    )


@pytest.mark.parametrize(
    "operation",
    [
        "get_by_id",
        "get_all",
        "get_by_user_ticket_id",
    ],
)
def test_query_denied_by_rbac_does_not_change_database(
    ticket_query_uow: SQLiteUnitOfWork,
    ticket_command_connection: Connection,
    operation: str,
) -> None:
    ticket_id = create_ticket(
        ticket_query_uow,
        text_of_ticket="Ticket must remain unchanged",
        user_id=USER_ID,
        contact_user_id=USER_ID,
        user_ticket_id=USER_TICKET_ID,
    )

    service = TicketQueryApplicationService(
        uow=ticket_query_uow,
    )
    actor = AllowTicketViewActor(
        error=DomainOperationError("Permission denied"),
    )
    service.actor = actor  # type: ignore[assignment]

    version_before = ticket_command_connection.connect.execute(
        """
        SELECT version
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    ).fetchone()[0]

    with pytest.raises(
        DomainOperationError,
        match="Permission denied",
    ):
        getattr(service, operation)(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=ticket_id,
                user_ticket_id=USER_TICKET_ID,
            )
        )

    version_after = ticket_command_connection.connect.execute(
        """
        SELECT version
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    ).fetchone()[0]

    assert version_after == version_before == 0

    assert_ticket_view_requested(
        actor,
        count=1,
    )