from __future__ import annotations

from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit

from src.application.dto.ticket_dto import TicketUserDTO
from tests_pyramid.support.service_imports import TicketUserApplicationService
from src.domain.department import Department
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import UserPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_user_status import TicketUserStatus

CLIENT_ID = 10
OTHER_CLIENT_ID = 11
USER_ID = 201
CONTACT_USER_ID = 202
OUTSIDER_USER_ID = 203
TICKET_ID = 1001
TICKET_USER_ID = 5001
ENABLED_DEPARTMENT_ID = 1
DISABLED_DEPARTMENT_ID = 2


class FakeRepo:
    def __init__(
        self,
        *,
        id_attr: str,
        items: list[object] | None = None,
        next_id: int = 1,
        save_label: str = "",
        calls: list[str] | None = None,
    ) -> None:
        self.id_attr = id_attr
        self.items: dict[int, object] = {}
        self.next_id = next_id
        self.save_label = save_label
        self.calls = calls

        for item in items or []:
            self.items[getattr(item, id_attr)] = item

    def get(
        self,
        item_id: int | None = None,
        **kwargs: int,
    ) -> object:
        if item_id is None:
            if not kwargs:
                raise KeyError("ID is required")
            item_id = next(iter(kwargs.values()))

        return self.items[item_id]

    def get_all(self) -> list[object]:
        return list(self.items.values())

    def save(self, item: object) -> object:
        if self.calls is not None and self.save_label:
            self.calls.append(self.save_label)

        current_id = getattr(item, self.id_attr)
        if current_id == 0:
            current_id = self.next_id
            self.next_id += 1
            setattr(item, self.id_attr, current_id)

        self.items[current_id] = item
        return item


class FakeTicketRepo(FakeRepo):
    def get_by_user_ticket_id(self, user_ticket_id: int) -> object:
        for ticket in self.items.values():
            if getattr(ticket, "user_ticket_id", 0) == user_ticket_id:
                return ticket
        raise KeyError(user_ticket_id)


class FakeUow:
    def __init__(self) -> None:
        self.calls: list[str] = []

        self.clients = FakeRepo(
            id_attr="client_id",
            items=[
                SimpleNamespace(client_id=CLIENT_ID, enabled=True),
                SimpleNamespace(client_id=OTHER_CLIENT_ID, enabled=True),
            ],
        )
        self.users = FakeRepo(
            id_attr="employee_id",
            items=[
                SimpleNamespace(
                    employee_id=USER_ID,
                    client_id=CLIENT_ID,
                    enabled=True,
                ),
                SimpleNamespace(
                    employee_id=CONTACT_USER_ID,
                    client_id=CLIENT_ID,
                    enabled=True,
                ),
                SimpleNamespace(
                    employee_id=OUTSIDER_USER_ID,
                    client_id=OTHER_CLIENT_ID,
                    enabled=True,
                ),
            ],
        )
        self.departments = FakeRepo(
            id_attr="department_id",
            items=[
                Department.create(
                    department_id=ENABLED_DEPARTMENT_ID,
                    name="Support",
                    enabled=True,
                ),
                Department.create(
                    department_id=DISABLED_DEPARTMENT_ID,
                    name="Disabled",
                    enabled=False,
                ),
            ],
        )
        self.tickets = FakeTicketRepo(
            id_attr="ticket_id",
            next_id=TICKET_ID,
            save_label="save_ticket",
            calls=self.calls,
        )
        self.user_tickets = FakeRepo(
            id_attr="ticket_id",
            next_id=TICKET_USER_ID,
            save_label="save_ticket_user",
            calls=self.calls,
        )

    def __enter__(self) -> FakeUow:
        return self

    def __exit__(self, *args: object) -> bool:
        return False

    def commit(self) -> None:
        self.calls.append("commit")


class FakeActor:
    def __init__(self, users: FakeRepo) -> None:
        self.users = users

    def require_actor_user(
        self,
        *,
        actor_user_id: int,
        permission: UserPermission,
    ) -> object:
        if permission != UserPermission.TICKET_OPERATION:
            raise PermissionError(permission.value)
        return self.users.get(actor_user_id)


def make_service(uow: FakeUow) -> TicketUserApplicationService:
    service = TicketUserApplicationService(uow)
    service.actor = FakeActor(uow.users)
    return service


def make_create_dto(**overrides: object) -> TicketUserDTO:
    data: dict[str, object] = {
        "ticket_user_id": 0,
        "client_id": CLIENT_ID,
        "actor_user_id": USER_ID,
        "contact_user_id": CONTACT_USER_ID,
        "department_id": ENABLED_DEPARTMENT_ID,
        "is_remote": False,
        "text_of_ticket": "Need help",
        "description": "Description",
        "urgency_level": 2,
        "comment": "Initial comment",
    }
    data.update(overrides)
    return TicketUserDTO(**data)


def test_create_from_user_creates_linked_aggregates_with_correct_actors() -> None:
    uow = FakeUow()
    service = make_service(uow)

    result = service.create_from_user(
        ticket_user_dto=make_create_dto(),
    )

    ticket_user = uow.user_tickets.get(result.ticket_id)
    ticket = uow.tickets.get_by_user_ticket_id(ticket_user.ticket_id)

    assert ticket_user.current_status() == TicketUserStatus.CREATED
    assert ticket_user.current_status_record().actor_employee_id == USER_ID

    assert ticket.admin_id == 0
    assert ticket.current_status_record().status == (
        TicketStatus.CREATED_FROM_TICKET_USER
    )
    assert ticket.current_status_record().actor_employee_id == 0

    assert ticket.user_ticket_id == ticket_user.ticket_id
    assert ticket.client_id == ticket_user.client_id
    assert ticket.user_id == ticket_user.user_id
    assert ticket.contact_user_id == ticket_user.contact_user_id

    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_create_from_user_allows_zero_department() -> None:
    uow = FakeUow()
    service = make_service(uow)

    result = service.create_from_user(
        ticket_user_dto=make_create_dto(
            department_id=0,
        ),
    )

    ticket = uow.tickets.get_by_user_ticket_id(result.ticket_id)
    assert ticket.department_id == 0


def test_create_from_user_rejects_disabled_department_before_persistence() -> None:
    uow = FakeUow()
    service = make_service(uow)

    with pytest.raises(DomainOperationError, match="Department is disabled"):
        service.create_from_user(
            ticket_user_dto=make_create_dto(
                department_id=DISABLED_DEPARTMENT_ID,
            ),
        )

    assert uow.calls == []
    assert uow.user_tickets.get_all() == []
    assert uow.tickets.get_all() == []


def test_create_from_user_rejects_contact_from_other_client() -> None:
    uow = FakeUow()
    service = make_service(uow)

    with pytest.raises(DomainOperationError):
        service.create_from_user(
            ticket_user_dto=make_create_dto(
                contact_user_id=OUTSIDER_USER_ID,
            ),
        )

    assert uow.calls == []
