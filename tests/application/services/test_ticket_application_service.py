from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import src.application.services.ticket_service as service_module

from src.application.services.ticket_service import TicketApplicationService
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission


CLIENT_ID = 10

ADMIN_ID = 101
OTHER_ADMIN_ID = 102
USER_ID = 201
CONTACT_USER_ID = 202

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
            item: object | None = None,
            **kwargs: object,
    ) -> object:
        if item is None:
            if not kwargs:
                raise TypeError("save() requires item")

            item = next(iter(kwargs.values()))

        if self.calls is not None and self.save_label:
            self.calls.append(self.save_label)

        current_id = getattr(item, self.id_attr)

        if current_id == 0:
            setattr(item, self.id_attr, self.next_id)
            current_id = self.next_id
            self.next_id += 1

        self.items[current_id] = item

        return item
    def delete(
        self,
        item_id: int,
) -> None:
        self.items.pop(item_id, None)


class FakeUow:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.committed = False

        self.admins = FakeRepo(
            id_attr="employee_id",
            items=[
                make_admin(ADMIN_ID),
                make_admin(OTHER_ADMIN_ID),
            ],
        )

        self.users = FakeRepo(
            id_attr="employee_id",
            items=[
                make_user(USER_ID, CLIENT_ID),
                make_user(CONTACT_USER_ID, CLIENT_ID),
            ],
        )

        self.clients = FakeRepo(
            id_attr="client_id",
            items=[
                make_client(CLIENT_ID),
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
            admins: FakeRepo,
    ) -> None:
        self.admins = admins
        self.calls: list[tuple[int, AdminPermission]] = []

    def require_actor_admin(
            self,
            *,
            actor_admin_id: int,
            permission: AdminPermission,
    ) -> object:
        self.calls.append(
            (
                actor_admin_id,
                permission,
            ),
        )

        return self.admins.get(actor_admin_id)


def make_admin(
        employee_id: int,
) -> object:
    return SimpleNamespace(
        employee_id=employee_id,
        enabled=True,
        department_id=1,
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


def make_client(
        client_id: int,
) -> object:
    return SimpleNamespace(
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
    )


def make_ticket(
        *,
        ticket_id: int = TICKET_ID,
        client_id: int = CLIENT_ID,
        admin_id: int = ADMIN_ID,
        user_id: int = 0,
        contact_user_id: int = 0,
        user_ticket_id: int = 0,
) -> object:
    return SimpleNamespace(
        ticket_id=ticket_id,
        client_id=client_id,
        admin_id=admin_id,
        user_id=user_id,
        contact_user_id=contact_user_id,
        user_ticket_id=user_ticket_id,
        department_id=1,
        add_comment=Mock(),
    )


def make_dto(
        **overrides: object,
) -> object:
    data = {
        "ticket_id": TICKET_ID,
        "user_ticket_id": 0,
        "client_id": CLIENT_ID,
        "actor_admin_id": ADMIN_ID,
        "admin_id": 0,
        "user_id": 0,
        "contact_user_id": 0,
        "department_id": 1,
        "executor_id": OTHER_ADMIN_ID,
        "is_remote": False,
        "text_of_ticket": "Need help",
        "description": "",
        "urgency_level": 0,
        "comment": "",
        "planned_start_at": None,
        "planned_finish_at": None,
        "actual_started_at": None,
        "actual_finished_at": None,
    }

    data.update(overrides)

    return SimpleNamespace(**data)


@pytest.fixture
def uow() -> FakeUow:
    return FakeUow()


@pytest.fixture
def service(
        uow: FakeUow,
) -> TicketApplicationService:
    app_service = TicketApplicationService(uow)
    app_service.actor = FakeActor(admins=uow.admins)
    return app_service


@pytest.fixture(autouse=True)
def patch_policy(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_admin_enabled",
        staticmethod(lambda *args, **kwargs: None),
    )
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
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_ticket_has_no_admin_yet",
        staticmethod(lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(
        service_module.TicketPolicy,
        "ensure_ticket_has_no_ticket_user",
        staticmethod(lambda *args, **kwargs: None),
    )


@pytest.fixture(autouse=True)
def patch_assembler(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service_module.TicketAssembler,
        "to_dto",
        staticmethod(
            lambda ticket: {
                "ticket_id": ticket.ticket_id,
                "client_id": ticket.client_id,
                "admin_id": ticket.admin_id,
                "user_id": ticket.user_id,
                "user_ticket_id": ticket.user_ticket_id,
            },
        ),
    )


def test_create_ticket_rejects_nonzero_ticket_id(
        service: TicketApplicationService,
) -> None:
    dto = make_dto(
        ticket_id=123,
        user_ticket_id=0,
    )

    with pytest.raises(DomainOperationError):
        service.create_ticket(
            ticket_dto=dto,
        )


def test_create_ticket_rejects_nonzero_user_ticket_id(
        service: TicketApplicationService,
) -> None:
    dto = make_dto(
        ticket_id=0,
        user_ticket_id=123,
    )

    with pytest.raises(DomainOperationError):
        service.create_ticket(
            ticket_dto=dto,
        )


def test_create_ticket_without_user_creates_only_internal_ticket(
        service: TicketApplicationService,
        uow: FakeUow,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_ticket_kwargs: dict[str, object] = {}
    ticket_user_create_call = Mock()

    def fake_ticket_create(
            **kwargs: object,
    ) -> object:
        created_ticket_kwargs.update(kwargs)

        return make_ticket(
            ticket_id=kwargs["ticket_id"],
            client_id=kwargs["client_id"],
            admin_id=kwargs["admin_id"],
            user_id=kwargs["user_id"],
            contact_user_id=kwargs["contact_user_id"],
            user_ticket_id=kwargs["user_ticket_id"],
        )

    monkeypatch.setattr(
        service_module.Ticket,
        "create",
        staticmethod(fake_ticket_create),
    )
    monkeypatch.setattr(
        service_module.TicketUser,
        "create",
        staticmethod(ticket_user_create_call),
    )

    dto = make_dto(
        ticket_id=0,
        user_id=0,
        contact_user_id=CONTACT_USER_ID,
        admin_id=0,
    )

    result = service.create_ticket(
        ticket_dto=dto,
    )

    assert result["ticket_id"] == TICKET_ID
    assert result["admin_id"] == ADMIN_ID
    assert result["user_id"] == 0
    assert result["user_ticket_id"] == 0

    assert created_ticket_kwargs["ticket_id"] == 0
    assert created_ticket_kwargs["admin_id"] == ADMIN_ID
    assert created_ticket_kwargs["user_id"] == 0
    assert created_ticket_kwargs["contact_user_id"] == CONTACT_USER_ID
    assert created_ticket_kwargs["user_ticket_id"] == 0

    ticket_user_create_call.assert_not_called()

    assert uow.calls == [
        "save_ticket",
        "commit",
    ]

    assert service.actor.calls == [
        (
            ADMIN_ID,
            AdminPermission.TICKET_OPERATION,
        ),
    ]


def test_create_ticket_with_user_creates_ticket_user_first_and_links_ticket(
        service: TicketApplicationService,
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
            ticket_user_id=kwargs["ticket_id"],
            client_id=kwargs["client_id"],
            user_id=kwargs["user_id"],
            contact_user_id=kwargs["contact_user_id"],
        )

    def fake_ticket_create(
            **kwargs: object,
    ) -> object:
        created_ticket_kwargs.update(kwargs)

        return make_ticket(
            ticket_id=kwargs["ticket_id"],
            client_id=kwargs["client_id"],
            admin_id=kwargs["admin_id"],
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
        "create",
        staticmethod(fake_ticket_create),
    )

    dto = make_dto(
        ticket_id=0,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        admin_id=OTHER_ADMIN_ID,
        comment="Created from phone call",
    )

    result = service.create_ticket(
        ticket_dto=dto,
    )

    assert result["ticket_id"] == TICKET_ID
    assert result["admin_id"] == OTHER_ADMIN_ID
    assert result["user_id"] == USER_ID
    assert result["user_ticket_id"] == TICKET_USER_ID

    assert created_ticket_user_kwargs["ticket_id"] == 0
    assert created_ticket_user_kwargs["client_id"] == CLIENT_ID
    assert created_ticket_user_kwargs["user_id"] == USER_ID
    assert created_ticket_user_kwargs["contact_user_id"] == CONTACT_USER_ID
    assert created_ticket_user_kwargs["comment"] == "Created from phone call"

    assert created_ticket_kwargs["ticket_id"] == 0
    assert created_ticket_kwargs["admin_id"] == OTHER_ADMIN_ID
    assert created_ticket_kwargs["user_id"] == USER_ID
    assert created_ticket_kwargs["contact_user_id"] == CONTACT_USER_ID
    assert created_ticket_kwargs["user_ticket_id"] == TICKET_USER_ID

    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_accept_changes_ticket_and_syncs_linked_ticket_user(
        service: TicketApplicationService,
        uow: FakeUow,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    ticket = make_ticket(
        ticket_id=TICKET_ID,
        user_id=USER_ID,
        user_ticket_id=TICKET_USER_ID,
    )

    uow.user_tickets.items[TICKET_USER_ID] = ticket_user
    uow.tickets.items[TICKET_ID] = ticket

    accept_call = Mock()
    sync_call = Mock(return_value=True)

    monkeypatch.setattr(
        service_module.TicketManagementService,
        "accept",
        staticmethod(accept_call),
    )
    monkeypatch.setattr(
        service_module.TicketUserSyncService,
        "sync_from_ticket",
        staticmethod(sync_call),
    )

    dto = make_dto(
        ticket_id=TICKET_ID,
        actor_admin_id=ADMIN_ID,
        comment="Accepted",
    )

    service.accept(
        ticket_dto=dto,
    )

    accept_call.assert_called_once_with(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Accepted",
    )

    sync_call.assert_called_once_with(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=ADMIN_ID,
        comment="Accepted",
    )

    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_confirm_execution_syncs_linked_ticket_user(
        service: TicketApplicationService,
        uow: FakeUow,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    ticket = make_ticket(
        ticket_id=TICKET_ID,
        user_id=USER_ID,
        user_ticket_id=TICKET_USER_ID,
    )

    uow.user_tickets.items[TICKET_USER_ID] = ticket_user
    uow.tickets.items[TICKET_ID] = ticket

    confirm_call = Mock()
    sync_call = Mock(return_value=True)

    monkeypatch.setattr(
        service_module.TicketReviewService,
        "confirm_execution",
        staticmethod(confirm_call),
    )
    monkeypatch.setattr(
        service_module.TicketUserSyncService,
        "sync_from_ticket",
        staticmethod(sync_call),
    )

    dto = make_dto(
        ticket_id=TICKET_ID,
        actor_admin_id=ADMIN_ID,
        comment="Approved",
    )

    service.confirm_execution(
        ticket_dto=dto,
    )

    confirm_call.assert_called_once_with(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Approved",
    )

    sync_call.assert_called_once_with(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=ADMIN_ID,
        comment="Approved",
    )

    assert uow.calls == [
        "save_ticket_user",
        "save_ticket",
        "commit",
    ]


def test_add_comment_does_not_sync_ticket_user(
        service: TicketApplicationService,
        uow: FakeUow,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticket_user = make_ticket_user(
        ticket_user_id=TICKET_USER_ID,
        user_id=USER_ID,
    )
    ticket = make_ticket(
        ticket_id=TICKET_ID,
        user_id=USER_ID,
        user_ticket_id=TICKET_USER_ID,
    )

    uow.user_tickets.items[TICKET_USER_ID] = ticket_user
    uow.tickets.items[TICKET_ID] = ticket

    sync_call = Mock()

    monkeypatch.setattr(
        service_module.TicketUserSyncService,
        "sync_from_ticket",
        staticmethod(sync_call),
    )

    dto = make_dto(
        ticket_id=TICKET_ID,
        actor_admin_id=ADMIN_ID,
        comment="Internal comment",
    )

    service.add_comment(
        ticket_dto=dto,
    )

    ticket.add_comment.assert_called_once()

    sync_call.assert_not_called()

    assert uow.calls == [
        "save_ticket",
        "commit",
    ]