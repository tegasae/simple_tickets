from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_query_service import (
    TicketQueryApplicationService,
)
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.ticket import Ticket


ACTOR_ADMIN_ID = 10
CLIENT_ID = 20

TICKET_ID = 100
SECOND_TICKET_ID = 101

USER_TICKET_ID = 500


# -------------------------------------------------------------------
# Local fakes
# -------------------------------------------------------------------


class FakeTicketRepository:
    def __init__(self) -> None:
        self.items: dict[int, Ticket] = {}

        self.get_calls: list[int] = []
        self.get_all_calls = 0
        self.get_by_user_ticket_id_calls: list[int] = []

    def add(self, ticket: Ticket) -> None:
        self.items[ticket.ticket_id] = ticket

    def get(self, *, ticket_id: int) -> Ticket:
        self.get_calls.append(ticket_id)
        return self.items[ticket_id]

    def get_all(self) -> list[Ticket]:
        self.get_all_calls += 1
        return list(self.items.values())

    def get_by_user_ticket_id(
        self,
        *,
        user_ticket_id: int,
    ) -> Ticket:
        self.get_by_user_ticket_id_calls.append(
            user_ticket_id
        )

        for ticket in self.items.values():
            if ticket.user_ticket_id == user_ticket_id:
                return ticket

        raise KeyError(
            f"Ticket for user_ticket_id={user_ticket_id} not found"
        )

    def save(self, ticket: Ticket) -> Ticket:
        raise AssertionError(
            "Query service must not save Ticket"
        )


@dataclass
class FakeUnitOfWork:
    tickets: FakeTicketRepository = field(
        default_factory=FakeTicketRepository,
    )

    entered: int = 0
    exited: int = 0

    def __enter__(self) -> "FakeUnitOfWork":
        self.entered += 1
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> bool:
        self.exited += 1
        return False


class FakeActorHelper:
    def __init__(
        self,
        *,
        actor: object,
        error: Exception | None = None,
    ) -> None:
        self.actor = actor
        self.error = error
        self.calls: list[dict[str, object]] = []

    def require_actor_admin(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> object:
        self.calls.append(
            {
                "actor_admin_id": actor_admin_id,
                "permission": permission,
            }
        )

        if self.error is not None:
            raise self.error

        return self.actor


# -------------------------------------------------------------------
# Factories
# -------------------------------------------------------------------


def make_actor(
    *,
    employee_id: int = ACTOR_ADMIN_ID,
) -> SimpleNamespace:
    return SimpleNamespace(
        employee_id=employee_id,
        enabled=True,
    )


def make_ticket(
    *,
    ticket_id: int = TICKET_ID,
    text_of_ticket: str = "Printer is unavailable",
    user_ticket_id: int = 0,
) -> Ticket:
    return Ticket.create(
        ticket_id=ticket_id,
        client_id=CLIENT_ID,
        admin_id=ACTOR_ADMIN_ID,
        text_of_ticket=text_of_ticket,
        user_ticket_id=user_ticket_id,
    )


def make_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


def make_service(
    uow: FakeUnitOfWork,
    *,
    actor: object | None = None,
    actor_error: Exception | None = None,
) -> tuple[
    TicketQueryApplicationService,
    FakeActorHelper,
]:
    service = TicketQueryApplicationService(uow)

    fake_actor = FakeActorHelper(
        actor=actor or make_actor(),
        error=actor_error,
    )
    service.actor = fake_actor  # type: ignore[assignment]

    return service, fake_actor


def assert_ticket_view_required(
    actor_helper: FakeActorHelper,
) -> None:
    assert actor_helper.calls == [
        {
            "actor_admin_id": ACTOR_ADMIN_ID,
            "permission": AdminPermission.TICKET_VIEW,
        }
    ]


# -------------------------------------------------------------------
# get_by_id
# -------------------------------------------------------------------


def test_get_by_id_returns_ticket_response_dto() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.get_by_id(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
        )
    )

    assert result.ticket_id == TICKET_ID
    assert result.client_id == CLIENT_ID
    assert result.admin_id == ACTOR_ADMIN_ID
    assert result.text_of_ticket == "Printer is unavailable"
    assert result.is_closed is False

    assert len(result.statuses) == 1
    assert result.statuses[0]["status"] == "created"

    assert result.comments == []

    assert uow.tickets.get_calls == [TICKET_ID]
    assert_ticket_view_required(actor_helper)

    assert uow.entered == 1
    assert uow.exited == 1


# -------------------------------------------------------------------
# get_all
# -------------------------------------------------------------------


def test_get_all_returns_response_dtos_for_all_tickets() -> None:
    uow = make_uow()

    first_ticket = make_ticket(
        ticket_id=TICKET_ID,
        text_of_ticket="First ticket",
    )
    second_ticket = make_ticket(
        ticket_id=SECOND_TICKET_ID,
        text_of_ticket="Second ticket",
    )

    uow.tickets.add(first_ticket)
    uow.tickets.add(second_ticket)

    service, actor_helper = make_service(uow)

    result = service.get_all(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
        )
    )

    assert len(result) == 2

    assert result[0].ticket_id == TICKET_ID
    assert result[0].text_of_ticket == "First ticket"

    assert result[1].ticket_id == SECOND_TICKET_ID
    assert result[1].text_of_ticket == "Second ticket"

    assert uow.tickets.get_all_calls == 1
    assert_ticket_view_required(actor_helper)

    assert uow.entered == 1
    assert uow.exited == 1


def test_get_all_returns_empty_list_when_no_tickets_exist() -> None:
    uow = make_uow()
    service, actor_helper = make_service(uow)

    result = service.get_all(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
        )
    )

    assert result == []
    assert uow.tickets.get_all_calls == 1
    assert_ticket_view_required(actor_helper)


# -------------------------------------------------------------------
# get_by_user_ticket_id
# -------------------------------------------------------------------


def test_get_by_user_ticket_id_returns_linked_ticket() -> None:
    uow = make_uow()

    ticket = make_ticket(
        user_ticket_id=USER_TICKET_ID,
    )
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.get_by_user_ticket_id(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            user_ticket_id=USER_TICKET_ID,
        )
    )

    assert result.ticket_id == TICKET_ID
    assert result.user_ticket_id == USER_TICKET_ID

    assert uow.tickets.get_by_user_ticket_id_calls == [
        USER_TICKET_ID
    ]
    assert_ticket_view_required(actor_helper)

    assert uow.entered == 1
    assert uow.exited == 1


# -------------------------------------------------------------------
# RBAC boundary
# -------------------------------------------------------------------


@pytest.mark.parametrize(
    "operation",
    [
        "get_by_id",
        "get_all",
        "get_by_user_ticket_id",
    ],
)
def test_query_does_not_access_repository_when_rbac_denies(
    operation: str,
) -> None:
    uow = make_uow()
    uow.tickets.add(
        make_ticket(
            user_ticket_id=USER_TICKET_ID,
        )
    )

    service, actor_helper = make_service(
        uow,
        actor_error=DomainOperationError("Permission denied"),
    )

    ticket_dto = TicketDTO(
        actor_admin_id=ACTOR_ADMIN_ID,
        ticket_id=TICKET_ID,
        user_ticket_id=USER_TICKET_ID,
    )

    with pytest.raises(
        DomainOperationError,
        match="Permission denied",
    ):
        getattr(service, operation)(
            ticket_dto=ticket_dto,
        )

    assert uow.tickets.get_calls == []
    assert uow.tickets.get_all_calls == 0
    assert uow.tickets.get_by_user_ticket_id_calls == []

    assert_ticket_view_required(actor_helper)