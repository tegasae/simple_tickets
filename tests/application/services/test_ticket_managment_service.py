from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_managment_service import TicketManagementApplicationService

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import (
    TicketStatusRecord,
)
from src.domain.ticket import Ticket


ACTOR_ADMIN_ID = 10
EXECUTOR_ADMIN_ID = 11
CLIENT_ID = 20
DEPARTMENT_ID = 30
OTHER_DEPARTMENT_ID = 31
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
        self.get_calls: list[int] = []
        self.saved: list[Ticket] = []

    def add(self, ticket: Ticket) -> None:
        self.items[ticket.ticket_id] = ticket

    def get(self, *, ticket_id: int) -> Ticket:
        self.get_calls.append(ticket_id)
        return self.items[ticket_id]

    def save(self, ticket: Ticket) -> Ticket:
        self.items[ticket.ticket_id] = ticket
        self.saved.append(ticket)
        return ticket


@dataclass
class FakeUnitOfWork:
    admins: FakeLookupRepository = field(
        default_factory=FakeLookupRepository,
    )
    clients: FakeLookupRepository = field(
        default_factory=FakeLookupRepository,
    )
    departments: FakeLookupRepository = field(
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


def future_datetime(*, hours: int = 1) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def make_admin(
    *,
    employee_id: int,
    department_id: int = DEPARTMENT_ID,
    enabled: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        employee_id=employee_id,
        department_id=department_id,
        enabled=enabled,
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


def make_department(
    *,
    department_id: int = DEPARTMENT_ID,
    enabled: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        department_id=department_id,
        enabled=enabled,
    )


def make_ticket(
    *,
    ticket_id: int = TICKET_ID,
    department_id: int = DEPARTMENT_ID,
) -> Ticket:
    return Ticket.create(
        ticket_id=ticket_id,
        client_id=CLIENT_ID,
        admin_id=ACTOR_ADMIN_ID,
        text_of_ticket="Printer is unavailable",
        department_id=department_id,
    )


def make_accepted_ticket(
    *,
    department_id: int = DEPARTMENT_ID,
) -> Ticket:
    ticket = make_ticket(department_id=department_id)

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ACTOR_ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )
    )

    return ticket


def make_uow() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()

    uow.clients.add(
        CLIENT_ID,
        make_client(),
    )
    uow.departments.add(
        DEPARTMENT_ID,
        make_department(),
    )
    uow.departments.add(
        OTHER_DEPARTMENT_ID,
        make_department(department_id=OTHER_DEPARTMENT_ID),
    )
    uow.admins.add(
        ACTOR_ADMIN_ID,
        make_admin(employee_id=ACTOR_ADMIN_ID),
    )
    uow.admins.add(
        EXECUTOR_ADMIN_ID,
        make_admin(employee_id=EXECUTOR_ADMIN_ID),
    )

    return uow


def make_service(
    uow: FakeUnitOfWork,
    *,
    actor: object | None = None,
    actor_error: Exception | None = None,
) -> tuple[
    TicketManagementApplicationService,
    FakeActorHelper,
]:
    service = TicketManagementApplicationService(uow)

    fake_actor = FakeActorHelper(
        actor=actor or make_admin(employee_id=ACTOR_ADMIN_ID),
        error=actor_error,
    )
    service.actor = fake_actor  # type: ignore[assignment]

    return service, fake_actor


def assert_ticket_operation_required(
    actor_helper: FakeActorHelper,
) -> None:
    assert actor_helper.calls == [
        {
            "actor_admin_id": ACTOR_ADMIN_ID,
            "permission": AdminPermission.TICKET_OPERATION,
        }
    ]


# -------------------------------------------------------------------
# accept_ticket
# -------------------------------------------------------------------


def test_accept_ticket_appends_accepted_status_and_saves() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.accept_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Accepted by dispatcher",
        )
    )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert ticket.statuses[-1].actor_employee_id == ACTOR_ADMIN_ID
    assert ticket.statuses[-1].comment == "Accepted by dispatcher"

    assert result.statuses[-1]["status"] == TicketStatus.ACCEPTED.value
    assert result.statuses[-1]["actor_id"] == ACTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


# -------------------------------------------------------------------
# reject_ticket
# -------------------------------------------------------------------


def test_reject_ticket_appends_rejected_status_and_saves() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.reject_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Duplicate request",
        )
    )

    assert ticket.current_status() is TicketStatus.REJECTED
    assert ticket.statuses[-1].comment == "Duplicate request"

    assert result.is_closed is True
    assert result.statuses[-1]["status"] == TicketStatus.REJECTED.value

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


def test_reject_ticket_requires_nonempty_comment() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        ItemValidationError,
        match="REJECTED requires comment",
    ):
        service.reject_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                comment="",
            )
        )

    assert ticket.current_status() is TicketStatus.CREATED
    assert uow.tickets.saved == []

# -------------------------------------------------------------------
# defer_ticket
# -------------------------------------------------------------------


def test_defer_ticket_appends_deferred_status_and_saves() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.defer_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Waiting for spare part",
        )
    )

    assert ticket.current_status() is TicketStatus.DEFERRED
    assert ticket.statuses[-1].comment == "Waiting for spare part"

    assert result.statuses[-1]["status"] == TicketStatus.DEFERRED.value
    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


# -------------------------------------------------------------------
# schedule_ticket
# -------------------------------------------------------------------


def test_schedule_ticket_appends_scheduled_status_and_saves() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    planned_start_at = future_datetime(hours=3)
    planned_finish_at = future_datetime(hours=5)

    service, actor_helper = make_service(uow)

    result = service.schedule_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="Visit scheduled",
        )
    )

    assert ticket.current_status() is TicketStatus.SCHEDULED
    assert ticket.statuses[-1].planned_start_at == planned_start_at
    assert ticket.statuses[-1].planned_finish_at == planned_finish_at
    assert ticket.statuses[-1].comment == "Visit scheduled"

    assert result.statuses[-1]["status"] == TicketStatus.SCHEDULED.value
    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


def test_schedule_ticket_requires_planned_start_at() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match="planned_start_at is required",
    ):
        service.schedule_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# assign_executor
# -------------------------------------------------------------------


def test_assign_executor_appends_assigned_status_and_saves() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.assign_executor(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            executor_id=EXECUTOR_ADMIN_ID,
            comment="Assigned to specialist",
        )
    )

    assert ticket.current_status() is TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].executor_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].comment == "Assigned to specialist"

    assert result.statuses[-1]["status"] == TicketStatus.ASSIGNED.value
    assert result.statuses[-1]["executor_id"] == EXECUTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


@pytest.mark.parametrize(
    ("executor_id", "admin_department_id", "admin_enabled", "expected_error"),
    [
        (
            0,
            DEPARTMENT_ID,
            True,
            "Executor id is required",
        ),
        (
            EXECUTOR_ADMIN_ID,
            DEPARTMENT_ID,
            False,
            f"disabled admin {EXECUTOR_ADMIN_ID}",
        ),
        (
            EXECUTOR_ADMIN_ID,
            0,
            True,
            f"Admin {EXECUTOR_ADMIN_ID} has no department",
        ),
        (
            EXECUTOR_ADMIN_ID,
            OTHER_DEPARTMENT_ID,
            True,
            f"belongs to department {OTHER_DEPARTMENT_ID}",
        ),
    ],
)
def test_assign_executor_rejects_invalid_executor_reference(
    executor_id: int,
    admin_department_id: int,
    admin_enabled: bool,
    expected_error: str,
) -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    if executor_id > 0:
        uow.admins.add(
            EXECUTOR_ADMIN_ID,
            make_admin(
                employee_id=EXECUTOR_ADMIN_ID,
                department_id=admin_department_id,
                enabled=admin_enabled,
            ),
        )

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=expected_error,
    ):
        service.assign_executor(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=executor_id,
            )
        )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert uow.tickets.saved == []


def test_assign_executor_rejects_ticket_without_department() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket(department_id=0)
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match="Ticket has no department",
    ):
        service.assign_executor(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=EXECUTOR_ADMIN_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert uow.tickets.saved == []


def test_assign_executor_rejects_disabled_ticket_department() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
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
        service.assign_executor(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=EXECUTOR_ADMIN_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# ready_to_work
# -------------------------------------------------------------------


def test_ready_to_work_appends_status_and_saves() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    planned_start_at = future_datetime(hours=2)
    planned_finish_at = future_datetime(hours=4)

    service, actor_helper = make_service(uow)

    result = service.ready_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            executor_id=EXECUTOR_ADMIN_ID,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="Everything is ready",
        )
    )

    assert ticket.current_status() is TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].planned_start_at == planned_start_at
    assert ticket.statuses[-1].planned_finish_at == planned_finish_at

    assert result.statuses[-1]["status"] == TicketStatus.READY_TO_WORK.value
    assert result.statuses[-1]["executor_id"] == EXECUTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


def test_ready_to_work_requires_planned_start_at() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match="planned_start_at is required",
    ):
        service.ready_to_work(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=EXECUTOR_ADMIN_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# cancel_ticket
# -------------------------------------------------------------------


def test_cancel_ticket_appends_cancelled_status_and_saves() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.cancel_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Cancelled by client request",
        )
    )

    assert ticket.current_status() is TicketStatus.CANCELLED
    assert ticket.statuses[-1].comment == "Cancelled by client request"

    assert result.is_closed is True
    assert result.statuses[-1]["status"] == TicketStatus.CANCELLED.value

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


# -------------------------------------------------------------------
# Application-layer boundaries
# -------------------------------------------------------------------


def test_management_operation_rejects_disabled_client() -> None:
    uow = make_uow()
    ticket = make_ticket()
    uow.tickets.add(ticket)

    uow.clients.add(
        CLIENT_ID,
        make_client(enabled=False),
    )

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=f"disabled client {CLIENT_ID}",
    ):
        service.accept_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.CREATED
    assert uow.tickets.saved == []


def test_management_operation_does_not_save_when_domain_transition_is_invalid() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(DomainOperationError):
        service.accept_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert uow.tickets.saved == []


def test_management_operation_does_not_load_ticket_when_rbac_denies_actor() -> None:
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
        service.accept_ticket(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert uow.tickets.get_calls == []
    assert uow.tickets.saved == []
    assert_ticket_operation_required(actor_helper)