from __future__ import annotations

from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit

from src.application.dto.ticket_dto import TicketDTO
from tests_pyramid.support.service_imports import TicketApplicationService
from src.domain.department import Department
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.statuses.ticket_user_status import TicketUserStatus

CLIENT_ID = 10
OTHER_CLIENT_ID = 11
CREATOR_ADMIN_ID = 101
OTHER_ADMIN_ID = 102
USER_ID = 201
CONTACT_USER_ID = 202
OTHER_CONTACT_USER_ID = 203
OUTSIDER_USER_ID = 204
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

    def save(
        self,
        item: object | None = None,
        **kwargs: object,
    ) -> object:
        if item is None:
            item = next(iter(kwargs.values()))

        if self.calls is not None and self.save_label:
            self.calls.append(self.save_label)

        current_id = getattr(item, self.id_attr)

        if current_id == 0:
            current_id = self.next_id
            self.next_id += 1
            setattr(item, self.id_attr, current_id)

        self.items[current_id] = item
        return item

    def delete(self, item_id: int) -> None:
        self.items.pop(item_id, None)


class FakeTicketRepo(FakeRepo):
    def get_by_user_ticket_id(self, user_ticket_id: int) -> object:
        for ticket in self.items.values():
            if getattr(ticket, "user_ticket_id", 0) == user_ticket_id:
                return ticket
        raise KeyError(user_ticket_id)


class FakeUow:
    def __init__(self) -> None:
        self.calls: list[str] = []

        self.admins = FakeRepo(
            id_attr="employee_id",
            items=[
                SimpleNamespace(
                    employee_id=CREATOR_ADMIN_ID,
                    enabled=True,
                    department_id=ENABLED_DEPARTMENT_ID,
                ),
                SimpleNamespace(
                    employee_id=OTHER_ADMIN_ID,
                    enabled=True,
                    department_id=ENABLED_DEPARTMENT_ID,
                ),
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
                    employee_id=OTHER_CONTACT_USER_ID,
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

        self.clients = FakeRepo(
            id_attr="client_id",
            items=[
                SimpleNamespace(client_id=CLIENT_ID, enabled=True),
                SimpleNamespace(client_id=OTHER_CLIENT_ID, enabled=True),
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
    def __init__(
        self,
        *,
        admins: FakeRepo,
        permissions: dict[int, set[AdminPermission]],
    ) -> None:
        self.admins = admins
        self.permissions = permissions

    def require_actor_admin(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> object:
        admin = self.admins.get(actor_admin_id)

        if permission not in self.permissions.get(actor_admin_id, set()):
            raise PermissionError(permission.value)

        return admin


def make_service(
    uow: FakeUow,
    *,
    creator_can_accept: bool = False,
    other_can_accept: bool = False,
) -> TicketApplicationService:
    service = TicketApplicationService(uow)

    permissions = {
        CREATOR_ADMIN_ID: {
            AdminPermission.TICKET_OPERATION,
            AdminPermission.TICKET_VIEW,
        },
        OTHER_ADMIN_ID: {
            AdminPermission.TICKET_OPERATION,
            AdminPermission.TICKET_VIEW,
        },
    }

    if creator_can_accept:
        permissions[CREATOR_ADMIN_ID].add(
            AdminPermission.TICKET_ACCEPTED,
        )

    if other_can_accept:
        permissions[OTHER_ADMIN_ID].add(
            AdminPermission.TICKET_ACCEPTED,
        )

    service.actor = FakeActor(
        admins=uow.admins,
        permissions=permissions,
    )
    return service


def make_create_dto(**overrides: object) -> TicketDTO:
    data: dict[str, object] = {
        "actor_admin_id": CREATOR_ADMIN_ID,
        "client_id": CLIENT_ID,
        "department_id": ENABLED_DEPARTMENT_ID,
        "text_of_ticket": "Need help",
        "description": "Description",
        "comment": "Initial comment",
    }
    data.update(overrides)
    return TicketDTO(**data)


def test_create_without_user_creates_only_internal_ticket() -> None:
    uow = FakeUow()
    service = make_service(uow)

    result = service.create_ticket(
        ticket_dto=make_create_dto(),
    )

    ticket = uow.tickets.get(result.ticket_id)

    assert ticket.admin_id == CREATOR_ADMIN_ID
    assert ticket.user_id == 0
    assert ticket.user_ticket_id == 0
    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
    ]
    assert ticket.statuses[0].actor_employee_id == CREATOR_ADMIN_ID
    assert uow.user_tickets.get_all() == []
    assert uow.calls == ["save_ticket", "commit"]


def test_create_with_user_represents_user_initiated_phone_request() -> None:
    uow = FakeUow()
    service = make_service(uow)

    result = service.create_ticket(
        ticket_dto=make_create_dto(
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            comment="Created from phone call",
        ),
    )

    ticket = uow.tickets.get(result.ticket_id)
    ticket_user = uow.user_tickets.get(ticket.user_ticket_id)

    assert ticket.admin_id == CREATOR_ADMIN_ID
    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
    ]
    assert ticket.statuses[0].actor_employee_id == CREATOR_ADMIN_ID

    assert ticket_user.user_id == USER_ID
    assert ticket_user.current_status() == TicketUserStatus.CREATED
    assert ticket_user.statuses[0].actor_employee_id == USER_ID

    assert ticket.user_ticket_id == ticket_user.ticket_id
    assert ticket.client_id == ticket_user.client_id
    assert ticket.user_id == ticket_user.user_id
    assert ticket.contact_user_id == ticket_user.contact_user_id
    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_create_with_accept_permission_keeps_created_then_accepted_history() -> None:
    uow = FakeUow()
    service = make_service(
        uow,
        creator_can_accept=True,
    )

    result = service.create_ticket(
        ticket_dto=make_create_dto(
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
        ),
    )

    ticket = uow.tickets.get(result.ticket_id)
    ticket_user = uow.user_tickets.get(ticket.user_ticket_id)

    assert ticket.admin_id == CREATOR_ADMIN_ID
    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
    ]
    assert [record.actor_employee_id for record in ticket.statuses] == [
        CREATOR_ADMIN_ID,
        CREATOR_ADMIN_ID,
    ]

    assert [record.status for record in ticket_user.statuses] == [
        TicketUserStatus.CREATED,
        TicketUserStatus.CONFIRMED_BY_ADMIN,
    ]
    assert [record.actor_employee_id for record in ticket_user.statuses] == [
        USER_ID,
        CREATOR_ADMIN_ID,
    ]


def test_explicit_accept_of_admin_created_ticket_does_not_change_creator() -> None:
    uow = FakeUow()
    service = make_service(
        uow,
        other_can_accept=True,
    )

    ticket = Ticket.create(
        client_id=CLIENT_ID,
        admin_id=CREATOR_ADMIN_ID,
        text_of_ticket="Need help",
        department_id=ENABLED_DEPARTMENT_ID,
    )
    uow.tickets.save(ticket)
    uow.calls.clear()

    service.accept(
        ticket_dto=TicketDTO(
            actor_admin_id=OTHER_ADMIN_ID,
            ticket_id=ticket.ticket_id,
            comment="Accepted",
        ),
    )

    assert ticket.admin_id == CREATOR_ADMIN_ID
    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
    ]
    assert ticket.statuses[-1].actor_employee_id == OTHER_ADMIN_ID


def test_explicit_accept_of_ticket_from_user_keeps_admin_id_zero() -> None:
    uow = FakeUow()
    service = make_service(
        uow,
        other_can_accept=True,
    )

    ticket_user = TicketUser.create(
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
    )
    uow.user_tickets.save(ticket_user)

    ticket = Ticket.create_from_ticket_user(
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=ticket_user.ticket_id,
        text_of_ticket="Need help",
        department_id=ENABLED_DEPARTMENT_ID,
    )
    uow.tickets.save(ticket)
    uow.calls.clear()

    service.accept(
        ticket_dto=TicketDTO(
            actor_admin_id=OTHER_ADMIN_ID,
            ticket_id=ticket.ticket_id,
            comment="Accepted",
        ),
    )

    assert ticket.admin_id == 0
    assert ticket.statuses[-1].status == TicketStatus.ACCEPTED
    assert ticket.statuses[-1].actor_employee_id == OTHER_ADMIN_ID
    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == OTHER_ADMIN_ID


def test_update_details_updates_linked_ticket_and_ticket_user_together() -> None:
    uow = FakeUow()
    service = make_service(uow)

    ticket_user = TicketUser.create(
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        description="Old",
    )
    uow.user_tickets.save(ticket_user)

    ticket = Ticket.create(
        client_id=CLIENT_ID,
        admin_id=CREATOR_ADMIN_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=ticket_user.ticket_id,
        text_of_ticket="Need help",
        description="Old",
        department_id=ENABLED_DEPARTMENT_ID,
    )
    uow.tickets.save(ticket)
    uow.calls.clear()

    service.update_details(
        ticket_dto=TicketDTO(
            actor_admin_id=CREATOR_ADMIN_ID,
            ticket_id=ticket.ticket_id,
            description="New description",
            contact_user_id=OTHER_CONTACT_USER_ID,
            is_remote=True,
        ),
    )

    assert ticket.description == "New description"
    assert ticket.contact_user_id == OTHER_CONTACT_USER_ID
    assert ticket.is_remote is True

    assert ticket_user.description == "New description"
    assert ticket_user.contact_user_id == OTHER_CONTACT_USER_ID
    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_create_rejects_disabled_department_before_persistence() -> None:
    uow = FakeUow()
    service = make_service(uow)

    with pytest.raises(DomainOperationError, match="Department is disabled"):
        service.create_ticket(
            ticket_dto=make_create_dto(
                department_id=DISABLED_DEPARTMENT_ID,
            ),
        )

    assert uow.calls == []
    assert uow.tickets.get_all() == []
    assert uow.user_tickets.get_all() == []


def test_change_department_rejects_disabled_department() -> None:
    uow = FakeUow()
    service = make_service(uow)

    ticket = Ticket.create(
        client_id=CLIENT_ID,
        admin_id=CREATOR_ADMIN_ID,
        text_of_ticket="Need help",
        department_id=ENABLED_DEPARTMENT_ID,
    )
    uow.tickets.save(ticket)
    uow.calls.clear()

    with pytest.raises(DomainOperationError, match="Department is disabled"):
        service.change_department(
            ticket_dto=TicketDTO(
                actor_admin_id=CREATOR_ADMIN_ID,
                ticket_id=ticket.ticket_id,
                department_id=DISABLED_DEPARTMENT_ID,
            ),
        )

    assert ticket.department_id == ENABLED_DEPARTMENT_ID
    assert uow.calls == []


def test_update_details_rejects_contact_user_from_other_client() -> None:
    uow = FakeUow()
    service = make_service(uow)

    ticket = Ticket.create(
        client_id=CLIENT_ID,
        admin_id=CREATOR_ADMIN_ID,
        text_of_ticket="Need help",
        department_id=ENABLED_DEPARTMENT_ID,
    )
    uow.tickets.save(ticket)
    uow.calls.clear()

    with pytest.raises(DomainOperationError):
        service.update_details(
            ticket_dto=TicketDTO(
                actor_admin_id=CREATOR_ADMIN_ID,
                ticket_id=ticket.ticket_id,
                contact_user_id=OUTSIDER_USER_ID,
            ),
        )
