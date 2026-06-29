
from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_command_service import TicketCommandApplicationService

from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import (
    TicketStatusRecord,
)
from src.domain.ticket import Ticket


ACTOR_ADMIN_ID = 10
CLIENT_ID = 20
USER_ID = 30
CONTACT_USER_ID = 31
DEPARTMENT_ID = 40
USER_TICKET_ID = 50
TICKET_ID = 100


# -------------------------------------------------------------------
# Local fakes
# -------------------------------------------------------------------


class FakeLookupRepository:
    def __init__(self) -> None:
        self.items: dict[int, object] = {}
        self.get_calls: list[dict[str, int]] = []

    def add(self, object_id: int, value: object) -> None:
        self.items[object_id] = value

    def get(self, **kwargs: int) -> object:
        self.get_calls.append(kwargs)

        object_id = next(iter(kwargs.values()))
        return self.items[object_id]


class FakeTicketRepository:
    def __init__(self) -> None:
        self.items: dict[int, Ticket] = {}
        self.saved: list[Ticket] = []
        self.deleted: list[int] = []
        self._next_id = 1000

    def add(self, ticket: Ticket) -> None:
        self.items[ticket.ticket_id] = ticket

    def get(self, *, ticket_id: int) -> Ticket:
        return self.items[ticket_id]

    def save(self, ticket: Ticket) -> Ticket:
        if ticket.ticket_id == 0:
            ticket.ticket_id = self._next_id
            self._next_id += 1

        self.items[ticket.ticket_id] = ticket
        self.saved.append(ticket)

        return ticket

    def delete(self, *, ticket_id: int) -> None:
        self.deleted.append(ticket_id)
        del self.items[ticket_id]


@dataclass
class FakeUnitOfWork:
    admins: FakeLookupRepository = field(
        default_factory=FakeLookupRepository,
    )
    users: FakeLookupRepository = field(
        default_factory=FakeLookupRepository,
    )
    clients: FakeLookupRepository = field(
        default_factory=FakeLookupRepository,
    )
    departments: FakeLookupRepository = field(
        default_factory=FakeLookupRepository,
    )
    user_tickets: FakeLookupRepository = field(
        default_factory=FakeLookupRepository,
    )
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


def make_client(
    *,
    client_id: int = CLIENT_ID,
    enabled: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        client_id=client_id,
        enabled=enabled,
    )


def make_user(
    *,
    employee_id: int = USER_ID,
    client_id: int = CLIENT_ID,
    enabled: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        employee_id=employee_id,
        client_id=client_id,
        enabled=enabled,
    )


def make_department(
    *,
    department_id: int = DEPARTMENT_ID,
    enabled: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        department_id=department_id,
        enabled=enabled,
    )


def make_user_ticket(
    *,
    ticket_id: int = USER_TICKET_ID,
    client_id: int = CLIENT_ID,
) -> SimpleNamespace:
    return SimpleNamespace(
        ticket_id=ticket_id,
        client_id=client_id,
    )


def make_ticket(
    *,
    ticket_id: int = TICKET_ID,
    department_id: int = 0,
    text_of_ticket: str = "Initial ticket text",
    description: str = "",
) -> Ticket:
    return Ticket.create(
        ticket_id=ticket_id,
        client_id=CLIENT_ID,
        admin_id=ACTOR_ADMIN_ID,
        text_of_ticket=text_of_ticket,
        department_id=department_id,
        description=description,
    )


def make_rejected_ticket() -> Ticket:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ACTOR_ADMIN_ID,
            status=TicketStatus.REJECTED,
            comment="Rejected for test",
        )
    )

    return ticket


def make_uow() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()

    uow.clients.add(
        CLIENT_ID,
        make_client(),
    )
    uow.users.add(
        USER_ID,
        make_user(employee_id=USER_ID),
    )
    uow.users.add(
        CONTACT_USER_ID,
        make_user(employee_id=CONTACT_USER_ID),
    )
    uow.departments.add(
        DEPARTMENT_ID,
        make_department(),
    )
    uow.user_tickets.add(
        USER_TICKET_ID,
        make_user_ticket(),
    )

    return uow


def make_service(
    uow: FakeUnitOfWork,
    *,
    actor: object | None = None,
    actor_error: Exception | None = None,
) -> tuple[TicketCommandApplicationService, FakeActorHelper]:
    service = TicketCommandApplicationService(uow)

    fake_actor = FakeActorHelper(
        actor=actor or make_actor(),
        error=actor_error,
    )
    service.actor = fake_actor  # type: ignore[assignment]

    return service, fake_actor


def assert_ticket_permission_required(
    actor_helper: FakeActorHelper,
) -> None:
    assert actor_helper.calls == [
        {
            "actor_admin_id": ACTOR_ADMIN_ID,
            "permission": AdminPermission.TICKET_OPERATION,
        }
    ]


# -------------------------------------------------------------------
# create_ticket
# -------------------------------------------------------------------


def test_create_ticket_creates_and_saves_aggregate() -> None:
    uow = make_uow()
    service, actor_helper = make_service(uow)

    result = service.create_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            user_ticket_id=USER_TICKET_ID,
            department_id=DEPARTMENT_ID,
            text_of_ticket="  Printer is unavailable  ",
            description="  Affected office: 4A  ",
            is_remote=True,
            urgency_level=3,
            comment="  Ticket registered  ",
        )
    )

    assert result.ticket_id == 1000
    assert result.client_id == CLIENT_ID
    assert result.admin_id == ACTOR_ADMIN_ID
    assert result.user_id == USER_ID
    assert result.contact_user_id == CONTACT_USER_ID
    assert result.user_ticket_id == USER_TICKET_ID
    assert result.department_id == DEPARTMENT_ID
    assert result.text_of_ticket == "Printer is unavailable"
    assert result.description == "Affected office: 4A"
    assert result.is_remote is True
    assert result.urgency_level == 3
    assert result.is_closed is False

    assert len(result.statuses) == 1
    assert result.statuses[0]["status"] == TicketStatus.CREATED.value
    assert result.statuses[0]["actor_id"] == ACTOR_ADMIN_ID

    assert len(result.comments) == 1
    assert result.comments[0]["actor_id"] == ACTOR_ADMIN_ID
    assert result.comments[0]["comment"] == "Ticket registered"

    saved_ticket = uow.tickets.saved[-1]
    assert saved_ticket.ticket_id == 1000
    assert saved_ticket.admin_id == ACTOR_ADMIN_ID

    assert_ticket_permission_required(actor_helper)
    assert uow.entered == 1
    assert uow.exited == 1


def test_create_ticket_rejects_admin_different_from_actor() -> None:
    uow = make_uow()
    service, actor_helper = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match="admin_id must match actor_admin_id",
    ):
        service.create_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                admin_id=999,
                client_id=CLIENT_ID,
                text_of_ticket="New ticket",
            )
        )

    assert uow.tickets.saved == []
    assert_ticket_permission_required(actor_helper)


def test_create_ticket_rejects_disabled_client() -> None:
    uow = make_uow()
    uow.clients.add(
        CLIENT_ID,
        make_client(enabled=False),
    )
    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=f"disabled client {CLIENT_ID}",
    ):
        service.create_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                client_id=CLIENT_ID,
                text_of_ticket="New ticket",
            )
        )

    assert uow.tickets.saved == []


@pytest.mark.parametrize(
    ("field_name", "user_id"),
    [
        ("user_id", USER_ID),
        ("contact_user_id", CONTACT_USER_ID),
    ],
)
def test_create_ticket_rejects_user_from_another_client(
    field_name: str,
    user_id: int,
) -> None:
    uow = make_uow()
    uow.users.add(
        user_id,
        make_user(
            employee_id=user_id,
            client_id=999,
        ),
    )
    service, _ = make_service(uow)

    dto_kwargs: dict[str, Any] = {
        "actor_admin_id": ACTOR_ADMIN_ID,
        "client_id": CLIENT_ID,
        "text_of_ticket": "New ticket",
        field_name: user_id,
    }

    with pytest.raises(
        DomainOperationError,
        match=f"User {user_id} does not belong to client {CLIENT_ID}",
    ):
        service.create_ticket(
            ticket_dto=TicketDTO(**dto_kwargs)
        )

    assert uow.tickets.saved == []


@pytest.mark.parametrize(
    ("field_name", "user_id"),
    [
        ("user_id", USER_ID),
        ("contact_user_id", CONTACT_USER_ID),
    ],
)
def test_create_ticket_rejects_disabled_user_reference(
    field_name: str,
    user_id: int,
) -> None:
    uow = make_uow()
    uow.users.add(
        user_id,
        make_user(
            employee_id=user_id,
            enabled=False,
        ),
    )
    service, _ = make_service(uow)

    dto_kwargs: dict[str, Any] = {
        "actor_admin_id": ACTOR_ADMIN_ID,
        "client_id": CLIENT_ID,
        "text_of_ticket": "New ticket",
        field_name: user_id,
    }

    with pytest.raises(
        DomainOperationError,
        match=f"User {user_id} is disabled",
    ):
        service.create_ticket(
            ticket_dto=TicketDTO(**dto_kwargs)
        )

    assert uow.tickets.saved == []


def test_create_ticket_rejects_disabled_department() -> None:
    uow = make_uow()
    uow.departments.add(
        DEPARTMENT_ID,
        make_department(enabled=False),
    )
    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=f"Department {DEPARTMENT_ID} is disabled",
    ):
        service.create_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                client_id=CLIENT_ID,
                department_id=DEPARTMENT_ID,
                text_of_ticket="New ticket",
            )
        )

    assert uow.tickets.saved == []


def test_create_ticket_rejects_user_ticket_from_another_client() -> None:
    uow = make_uow()
    uow.user_tickets.add(
        USER_TICKET_ID,
        make_user_ticket(client_id=999),
    )
    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=(
            f"TicketUser {USER_TICKET_ID} "
            f"does not belong to client {CLIENT_ID}"
        ),
    ):
        service.create_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                client_id=CLIENT_ID,
                user_ticket_id=USER_TICKET_ID,
                text_of_ticket="New ticket",
            )
        )

    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# update_ticket_text
# -------------------------------------------------------------------


def test_update_ticket_text_updates_and_saves_ticket() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.update_ticket_text(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            text_of_ticket="  Updated text  ",
        )
    )

    assert ticket.text_of_ticket == "Updated text"
    assert result.text_of_ticket == "Updated text"
    assert uow.tickets.saved == [ticket]
    assert_ticket_permission_required(actor_helper)


# -------------------------------------------------------------------
# update_description
# -------------------------------------------------------------------


def test_update_description_updates_and_saves_ticket() -> None:
    uow = make_uow()
    ticket = make_ticket(description="Old description")
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.update_description(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            description="  Updated description  ",
        )
    )

    assert ticket.description == "Updated description"
    assert result.description == "Updated description"
    assert uow.tickets.saved == [ticket]
    assert_ticket_permission_required(actor_helper)


# -------------------------------------------------------------------
# add_comment
# -------------------------------------------------------------------


def test_add_comment_adds_comment_from_actor_and_saves_ticket() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.add_comment(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="  Added by actor  ",
        )
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == ACTOR_ADMIN_ID
    assert ticket.comments[0].comment == "Added by actor"

    assert len(result.comments) == 1
    assert result.comments[0]["actor_id"] == ACTOR_ADMIN_ID
    assert result.comments[0]["comment"] == "Added by actor"

    assert uow.tickets.saved == [ticket]
    assert_ticket_permission_required(actor_helper)


def test_add_comment_rejects_terminal_ticket() -> None:
    uow = make_uow()
    ticket = make_rejected_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=(
            f"The ticket {TICKET_ID} is in terminal status "
            f"{TicketStatus.REJECTED.value}"
        ),
    ):
        service.add_comment(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                comment="Additional explanation",
            )
        )

    assert ticket.comments == []
    assert uow.tickets.saved == []
# -------------------------------------------------------------------
# change_department
# -------------------------------------------------------------------


def test_change_department_validates_enabled_department_and_saves() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    new_department_id = 41
    uow.departments.add(
        new_department_id,
        make_department(department_id=new_department_id),
    )

    service, actor_helper = make_service(uow)

    result = service.change_department(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            department_id=new_department_id,
        )
    )

    assert ticket.department_id == new_department_id
    assert result.department_id == new_department_id
    assert uow.tickets.saved == [ticket]
    assert_ticket_permission_required(actor_helper)


def test_change_department_allows_removing_department() -> None:
    uow = make_uow()
    ticket = make_ticket(department_id=DEPARTMENT_ID)
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    result = service.change_department(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            department_id=0,
        )
    )

    assert ticket.department_id == 0
    assert result.department_id == 0
    assert uow.departments.get_calls == []
    assert uow.tickets.saved == [ticket]


def test_change_department_rejects_disabled_department() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    uow.departments.add(
        DEPARTMENT_ID,
        make_department(enabled=False),
    )

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=f"Department {DEPARTMENT_ID} is disabled",
    ):
        service.change_department(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                department_id=DEPARTMENT_ID,
            )
        )

    assert ticket.department_id == 0
    assert uow.tickets.saved == []


def test_change_department_rejects_terminal_ticket() -> None:
    uow = make_uow()
    ticket = make_rejected_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(DomainOperationError):
        service.change_department(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                department_id=DEPARTMENT_ID,
            )
        )

    assert ticket.department_id == 0
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# delete_ticket
# -------------------------------------------------------------------


def test_delete_ticket_checks_existence_and_deletes_ticket() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.delete_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
        )
    )

    assert result is None
    assert uow.tickets.deleted == [TICKET_ID]
    assert TICKET_ID not in uow.tickets.items
    assert_ticket_permission_required(actor_helper)


# -------------------------------------------------------------------
# RBAC boundary
# -------------------------------------------------------------------


def test_command_does_not_load_or_save_ticket_when_rbac_denies_actor() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(
        uow,
        actor_error=DomainOperationError("Permission denied"),
    )

    with pytest.raises(
        DomainOperationError,
        match="Permission denied",
    ):
        service.update_description(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                description="Should not be applied",
            )
        )

    assert ticket.description == ""
    assert uow.tickets.saved == []
    assert_ticket_permission_required(actor_helper)

