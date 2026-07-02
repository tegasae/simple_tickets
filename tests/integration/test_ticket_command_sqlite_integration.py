from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_command_service import (
    TicketCommandApplicationService,
)
from src.domain.exceptions import (
    DomainOperationError,
    ItemNotFoundError,
)
from src.domain.rbac.permissions import AdminPermission
from src.domain.statuses.ticket_status import TicketStatus


ACTOR_ADMIN_ID = 10
CLIENT_ID = 100

SUPPORT_DEPARTMENT_ID = 1
INFRASTRUCTURE_DEPARTMENT_ID = 2
DISABLED_DEPARTMENT_ID = 3


class AllowTicketOperationActor:
    """
    RBAC is isolated from this persistence integration test.

    The stub verifies that the application service requests
    exactly TICKET_OPERATION and returns the authenticated actor.
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
def ticket_command_service(
    ticket_command_uow,
) -> tuple[
    TicketCommandApplicationService,
    AllowTicketOperationActor,
]:
    service = TicketCommandApplicationService(
        uow=ticket_command_uow,
    )

    actor = AllowTicketOperationActor()
    service.actor = actor  # type: ignore[assignment]

    return service, actor


def create_ticket(
    service: TicketCommandApplicationService,
    *,
    text_of_ticket: str = "Office network is unavailable",
    description: str = "Third-floor office",
    department_id: int = SUPPORT_DEPARTMENT_ID,
    comment: str = "",
):
    return service.create_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            client_id=CLIENT_ID,
            department_id=department_id,
            text_of_ticket=text_of_ticket,
            description=description,
            urgency_level=2,
            is_remote=False,
            comment=comment,
        )
    )


def test_create_ticket_persists_root_initial_status_and_comment(
    ticket_command_service,
    ticket_command_uow,
) -> None:
    service, actor = ticket_command_service

    response = create_ticket(
        service,
        comment="Registered by phone",
    )

    with ticket_command_uow as uow:
        ticket = uow.tickets.get(
            ticket_id=response.ticket_id,
        )

    assert ticket.ticket_id > 0
    assert ticket.client_id == CLIENT_ID
    assert ticket.admin_id == ACTOR_ADMIN_ID
    assert ticket.department_id == SUPPORT_DEPARTMENT_ID

    assert ticket.text_of_ticket == "Office network is unavailable"
    assert ticket.description == "Third-floor office"
    assert ticket.urgency_level == 2
    assert ticket.is_remote is False

    assert len(ticket.statuses) == 1
    assert ticket.current_status() is TicketStatus.CREATED
    assert ticket.statuses[0].actor_employee_id == ACTOR_ADMIN_ID

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == ACTOR_ADMIN_ID
    assert ticket.comments[0].comment == "Registered by phone"

    assert actor.calls == [
        {
            "actor_admin_id": ACTOR_ADMIN_ID,
            "permission": AdminPermission.TICKET_OPERATION,
        }
    ]


def test_update_text_description_comment_and_department_persist(
    ticket_command_service,
    ticket_command_uow,
) -> None:
    service, _ = ticket_command_service

    created = create_ticket(service)

    service.update_ticket_text(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=created.ticket_id,
            text_of_ticket="  Network is unavailable on the third floor  ",
        )
    )

    service.update_description(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=created.ticket_id,
            description="Check the switch in the server room",
        )
    )

    service.add_comment(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=created.ticket_id,
            comment="Engineer has been notified",
        )
    )

    service.change_department(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=created.ticket_id,
            department_id=INFRASTRUCTURE_DEPARTMENT_ID,
        )
    )

    with ticket_command_uow as uow:
        ticket = uow.tickets.get(
            ticket_id=created.ticket_id,
        )

    assert ticket.text_of_ticket == (
        "Network is unavailable on the third floor"
    )
    assert ticket.description == (
        "Check the switch in the server room"
    )
    assert ticket.department_id == INFRASTRUCTURE_DEPARTMENT_ID

    assert [comment.comment for comment in ticket.comments] == [
        "Engineer has been notified",
    ]
    assert ticket.comments[0].employee_id == ACTOR_ADMIN_ID

    assert ticket.current_status() is TicketStatus.CREATED
    assert ticket.version == 4


def test_create_ticket_with_disabled_department_rolls_back(
    ticket_command_service,
    ticket_command_connection,
) -> None:
    service, _ = ticket_command_service

    with pytest.raises(
        DomainOperationError,
        match="disabled",
    ):
        create_ticket(
            service,
            department_id=DISABLED_DEPARTMENT_ID,
        )

    ticket_count = ticket_command_connection.connect.execute(
        """
        SELECT COUNT(*)
        FROM tickets
        """
    ).fetchone()[0]

    status_count = ticket_command_connection.connect.execute(
        """
        SELECT COUNT(*)
        FROM ticket_status_records
        """
    ).fetchone()[0]

    comment_count = ticket_command_connection.connect.execute(
        """
        SELECT COUNT(*)
        FROM ticket_comments
        """
    ).fetchone()[0]

    assert ticket_count == 0
    assert status_count == 0
    assert comment_count == 0


def test_delete_ticket_commits_cascade_for_history_and_comments(
    ticket_command_service,
    ticket_command_uow,
    ticket_command_connection,
) -> None:
    service, _ = ticket_command_service

    created = create_ticket(
        service,
        comment="Initial ticket comment",
    )

    ticket_id = created.ticket_id

    service.delete_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=ticket_id,
        )
    )

    with pytest.raises(ItemNotFoundError):
        with ticket_command_uow as uow:
            uow.tickets.get(
                ticket_id=ticket_id,
            )

    status_count = ticket_command_connection.connect.execute(
        """
        SELECT COUNT(*)
        FROM ticket_status_records
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    ).fetchone()[0]

    comment_count = ticket_command_connection.connect.execute(
        """
        SELECT COUNT(*)
        FROM ticket_comments
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    ).fetchone()[0]

    assert status_count == 0
    assert comment_count == 0