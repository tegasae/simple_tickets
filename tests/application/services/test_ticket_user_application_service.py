from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import src.application.services.ticket_user_service as service_module

from src.application.services.ticket_user_service import TicketUserApplicationService
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import UserPermission


CLIENT_ID = 10
OTHER_CLIENT_ID = 20

USER_ID = 101
OTHER_USER_ID = 102
OUTSIDER_USER_ID = 201

TICKET_ID = 1001
TICKET_USER_ID = 5001


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

        if items:
            for item in items:
                self.items[getattr(item, id_attr)] = item

        self.next_id = next_id
        self.save_label = save_label
        self.calls = calls

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
        item: object,
    ) -> object:
        if self.calls is not None and self.save_label:
            self.calls.append(self.save_label)

        current_id = getattr(item, self.id_attr)

        if current_id == 0:
            setattr(item, self.id_attr, self.next_id)
            current_id = self.next_id
            self.next_id += 1

        self.items[current_id] = item

        return item


class FakeUow:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.committed = False

        self.clients = FakeRepo(
            id_attr="client_id",
            items=[
                make_client(CLIENT_ID),
                make_client(OTHER_CLIENT_ID),
            ],
        )

        self.users = FakeRepo(
            id_attr="employee_id",
            items=[
                make_user(USER_ID, CLIENT_ID),
                make_user(OTHER_USER_ID, CLIENT_ID),
                make_user(OUTSIDER_USER_ID, OTHER_CLIENT_ID),
            ],
        )

        self.departments = FakeRepo(
            id_attr="department_id",
            items=[
                SimpleNamespace(
                    department_id=1,
                    enabled=True,
                ),
            ],
        )

        self.tickets = FakeRepo(
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
        self.committed = True


class FakeActor:
    def __init__(
        self,
        *,
        users: FakeRepo,
    ) -> None:
        self.users = users
        self.calls: list[tuple[int, UserPermission]] = []

    def require_actor_user(
        self,
        *,
        actor_user_id: int,
        permission: UserPermission,
    ) -> object:
        self.calls.append(
            (
                actor_user_id,
                permission,
            ),
        )

        return self.users.get(actor_user_id)


def make_client(
    client_id: int,
) -> object:
    return SimpleNamespace(
        client_id=client_id,
        enabled=True,
    )


def make_user(
    employee_id: int,
    client_id: int,
) -> object:
    return SimpleNamespace(
        employee_id=employee_id,
        client_id=client_id,
        enabled=True,
    )


def make_ticket_user(
    *,
    ticket_user_id: int = TICKET_USER_ID,
    client_id: int = CLIENT_ID,
    user_id: int = USER_ID,
    contact_user_id: int = 0,
) -> object:
    return SimpleNamespace(
        ticket_id=ticket_user_id,
        client_id=client_id,
        user_id=user_id,
        contact_user_id=contact_user_id,
        confirm_execution_by_user=Mock(),
    )


def make_ticket(
    *,
    ticket_id: int = TICKET_ID,
    client_id: int = CLIENT_ID,
    user_id: int = USER_ID,
    contact_user_id: int = 0,
    user_ticket_id: int = TICKET_USER_ID,
) -> object:
    return SimpleNamespace(
        ticket_id=ticket_id,
        client_id=client_id,
        user_id=user_id,
        contact_user_id=contact_user_id,
        user_ticket_id=user_ticket_id,
    )


def make_dto(
    **overrides: object,
) -> object:
    data = {
        "ticket_id": TICKET_ID,
        "ticket_user_id": TICKET_USER_ID,
        "client_id": CLIENT_ID,
        "actor_user_id": USER_ID,
        "user_id": USER_ID,
        "contact_user_id": 0,
        "department_id": 0,
        "is_remote": False,
        "text_of_ticket": "Need help",
        "description": "",
        "urgency_level": 0,
        "comment": "",
    }

    data.update(overrides)

    return SimpleNamespace(**data)


@pytest.fixture
def uow() -> FakeUow:
    return FakeUow()


@pytest.fixture
def service(
    uow: FakeUow,
) -> TicketUserApplicationService:
    app_service = TicketUserApplicationService(uow)
    app_service.actor = FakeActor(users=uow.users)
    return app_service


@pytest.fixture(autouse=True)
def patch_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_client_enabled",
        staticmethod(lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_user_enabled",
        staticmethod(lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_user_belongs_to_client",
        staticmethod(lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_contact_user_belongs_to_client",
        staticmethod(lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_ticket_matches_ticket_user",
        staticmethod(lambda *args, **kwargs: None),
    )


@pytest.fixture(autouse=True)
def patch_assembler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service_module.TicketUserAssembler,
        "to_dto",
        staticmethod(
            lambda ticket_user: {
                "ticket_user_id": ticket_user.ticket_id,
                "client_id": ticket_user.client_id,
                "user_id": ticket_user.user_id,
            },
        ),
    )


def test_create_from_user_rejects_nonzero_ticket_id(
    service: TicketUserApplicationService,
) -> None:
    dto = make_dto(
        ticket_id=123,
        ticket_user_id=0,
    )

    with pytest.raises(DomainOperationError):
        service.create_from_user(
            ticket_user_dto=dto,
        )


def test_create_from_user_rejects_nonzero_ticket_user_id(
    service: TicketUserApplicationService,
) -> None:
    dto = make_dto(
        ticket_id=0,
        ticket_user_id=123,
    )

    with pytest.raises(DomainOperationError):
        service.create_from_user(
            ticket_user_dto=dto,
        )


def test_create_from_user_creates_ticket_user_first_and_links_ticket(
    service: TicketUserApplicationService,
    uow: FakeUow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_ticket_user_kwargs: dict[str, object] = {}
    created_ticket_kwargs: dict[str, object] = {}

    def fake_ticket_user_create(
        **kwargs: object,
    ) -> object:
        created_ticket_user_kwargs.update(kwargs)

        return make_ticket_user(
            ticket_user_id=0,
            client_id=kwargs["client_id"],
            user_id=kwargs["user_id"],
            contact_user_id=kwargs["contact_user_id"],
        )

    def fake_ticket_create_from_ticket_user(
        **kwargs: object,
    ) -> object:
        created_ticket_kwargs.update(kwargs)

        return make_ticket(
            ticket_id=0,
            client_id=kwargs["client_id"],
            user_id=kwargs["user_id"],
            contact_user_id=kwargs["contact_user_id"],
            user_ticket_id=kwargs["user_ticket_id"],
        )

    monkeypatch.setattr(
        service_module.TicketUser,
        "create",
        staticmethod(fake_ticket_user_create),
    )
    monkeypatch.setattr(
        service_module.Ticket,
        "create_from_ticket_user",
        staticmethod(fake_ticket_create_from_ticket_user),
    )

    dto = make_dto(
        ticket_id=0,
        ticket_user_id=0,
        actor_user_id=USER_ID,
        client_id=CLIENT_ID,
    )

    result = service.create_from_user(
        ticket_user_dto=dto,
    )

    assert result["ticket_user_id"] == TICKET_USER_ID

    assert created_ticket_user_kwargs["ticket_id"] == 0
    assert created_ticket_user_kwargs["user_id"] == USER_ID

    assert created_ticket_kwargs["ticket_id"] == 0
    assert created_ticket_kwargs["user_ticket_id"] == TICKET_USER_ID

    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]

    assert service.actor.calls == [
        (
            USER_ID,
            UserPermission.TICKET_OPERATION,
        ),
    ]


def test_cancel_by_owner_uses_ticket_operation_and_syncs(
    service: TicketUserApplicationService,
    uow: FakeUow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    ticket = make_ticket(
        ticket_id=TICKET_ID,
        user_ticket_id=TICKET_USER_ID,
    )

    uow.user_tickets.items[TICKET_USER_ID] = ticket_user
    uow.tickets.items[TICKET_ID] = ticket

    cancel_call = Mock()
    sync_call = Mock(return_value=True)

    monkeypatch.setattr(
        service_module.TicketManagementService,
        "cancel_by_user",
        staticmethod(cancel_call),
    )
    monkeypatch.setattr(
        service_module.TicketUserSyncService,
        "sync_from_ticket",
        staticmethod(sync_call),
    )

    dto = make_dto(
        ticket_id=TICKET_ID,
        ticket_user_id=TICKET_USER_ID,
        actor_user_id=USER_ID,
        comment="Cancel it",
    )

    service.cancel_by_user(
        ticket_user_dto=dto,
    )

    assert service.actor.calls == [
        (
            USER_ID,
            UserPermission.TICKET_OPERATION,
        ),
    ]

    cancel_call.assert_called_once_with(
        ticket=ticket,
        comment="Cancel it",
    )
    sync_call.assert_called_once_with(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=USER_ID,
        comment="Cancel it",
    )

    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_cancel_by_other_user_requires_ticket_operation_all(
    service: TicketUserApplicationService,
    uow: FakeUow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    ticket = make_ticket(
        ticket_id=TICKET_ID,
        user_ticket_id=TICKET_USER_ID,
    )

    uow.user_tickets.items[TICKET_USER_ID] = ticket_user
    uow.tickets.items[TICKET_ID] = ticket

    monkeypatch.setattr(
        service_module.TicketManagementService,
        "cancel_by_user",
        staticmethod(Mock()),
    )
    monkeypatch.setattr(
        service_module.TicketUserSyncService,
        "sync_from_ticket",
        staticmethod(Mock(return_value=True)),
    )

    dto = make_dto(
        ticket_id=TICKET_ID,
        ticket_user_id=TICKET_USER_ID,
        actor_user_id=OTHER_USER_ID,
    )

    service.cancel_by_user(
        ticket_user_dto=dto,
    )

    assert service.actor.calls == [
        (
            OTHER_USER_ID,
            UserPermission.TICKET_OPERATION_ALL,
        ),
    ]


def test_confirm_execution_by_user_changes_ticket_user_and_ticket_without_sync(
    service: TicketUserApplicationService,
    uow: FakeUow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    ticket = make_ticket(
        ticket_id=TICKET_ID,
        user_ticket_id=TICKET_USER_ID,
    )

    uow.user_tickets.items[TICKET_USER_ID] = ticket_user
    uow.tickets.items[TICKET_ID] = ticket

    confirm_ticket_call = Mock()
    sync_call = Mock()

    monkeypatch.setattr(
        service_module.TicketReviewService,
        "confirm_execution",
        staticmethod(confirm_ticket_call),
    )
    monkeypatch.setattr(
        service_module.TicketUserSyncService,
        "sync_from_ticket",
        staticmethod(sync_call),
    )

    dto = make_dto(
        ticket_id=TICKET_ID,
        ticket_user_id=TICKET_USER_ID,
        actor_user_id=USER_ID,
        comment="Done",
    )

    service.confirm_execution_by_user(
        ticket_user_dto=dto,
    )

    ticket_user.confirm_execution_by_user.assert_called_once_with(
        actor_employee_id=USER_ID,
        comment="Done",
    )

    confirm_ticket_call.assert_called_once_with(
        ticket=ticket,
        actor_employee_id=USER_ID,
        comment="Done",
    )

    sync_call.assert_not_called()

    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_get_all_requires_view_all_and_filters_by_client(
    service: TicketUserApplicationService,
    uow: FakeUow,
) -> None:
    uow.user_tickets.items = {
        1: make_ticket_user(
            ticket_user_id=1,
            client_id=CLIENT_ID,
            user_id=USER_ID,
        ),
        2: make_ticket_user(
            ticket_user_id=2,
            client_id=OTHER_CLIENT_ID,
            user_id=OUTSIDER_USER_ID,
        ),
        3: make_ticket_user(
            ticket_user_id=3,
            client_id=CLIENT_ID,
            user_id=OTHER_USER_ID,
        ),
    }

    dto = make_dto(
        actor_user_id=OTHER_USER_ID,
        client_id=CLIENT_ID,
    )

    result = service.get_all(
        ticket_user_dto=dto,
    )

    assert [item["ticket_user_id"] for item in result] == [
        1,
        3,
    ]

    assert service.actor.calls == [
        (
            OTHER_USER_ID,
            UserPermission.TICKET_VIEW_ALL,
        ),
    ]


def test_get_by_user_owner_requires_view(
    service: TicketUserApplicationService,
    uow: FakeUow,
) -> None:
    uow.user_tickets.items = {
        1: make_ticket_user(
            ticket_user_id=1,
            client_id=CLIENT_ID,
            user_id=USER_ID,
        ),
        2: make_ticket_user(
            ticket_user_id=2,
            client_id=CLIENT_ID,
            user_id=OTHER_USER_ID,
        ),
    }

    dto = make_dto(
        actor_user_id=USER_ID,
        user_id=USER_ID,
        client_id=CLIENT_ID,
    )

    result = service.get_by_user(
        ticket_user_dto=dto,
    )

    assert [item["ticket_user_id"] for item in result] == [
        1,
    ]

    assert service.actor.calls == [
        (
            USER_ID,
            UserPermission.TICKET_VIEW,
        ),
    ]


def test_get_by_user_other_user_requires_view_all(
    service: TicketUserApplicationService,
    uow: FakeUow,
) -> None:
    uow.user_tickets.items = {
        1: make_ticket_user(
            ticket_user_id=1,
            client_id=CLIENT_ID,
            user_id=USER_ID,
        ),
        2: make_ticket_user(
            ticket_user_id=2,
            client_id=CLIENT_ID,
            user_id=OTHER_USER_ID,
        ),
    }

    dto = make_dto(
        actor_user_id=OTHER_USER_ID,
        user_id=USER_ID,
        client_id=CLIENT_ID,
    )

    result = service.get_by_user(
        ticket_user_dto=dto,
    )

    assert [item["ticket_user_id"] for item in result] == [
        1,
    ]

    assert service.actor.calls == [
        (
            OTHER_USER_ID,
            UserPermission.TICKET_VIEW_ALL,
        ),
    ]


def test_get_by_id_owner_requires_view(
    service: TicketUserApplicationService,
    uow: FakeUow,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    uow.user_tickets.items[TICKET_USER_ID] = ticket_user

    dto = make_dto(
        ticket_user_id=TICKET_USER_ID,
        actor_user_id=USER_ID,
    )

    result = service.get_by_id(
        ticket_user_dto=dto,
    )

    assert result["ticket_user_id"] == TICKET_USER_ID

    assert service.actor.calls == [
        (
            USER_ID,
            UserPermission.TICKET_VIEW,
        ),
    ]


def test_get_by_id_other_user_requires_view_all(
    service: TicketUserApplicationService,
    uow: FakeUow,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    uow.user_tickets.items[TICKET_USER_ID] = ticket_user

    dto = make_dto(
        ticket_user_id=TICKET_USER_ID,
        actor_user_id=OTHER_USER_ID,
    )

    result = service.get_by_id(
        ticket_user_dto=dto,
    )

    assert result["ticket_user_id"] == TICKET_USER_ID

    assert service.actor.calls == [
        (
            OTHER_USER_ID,
            UserPermission.TICKET_VIEW_ALL,
        ),
    ]