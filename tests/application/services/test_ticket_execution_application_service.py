from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_execution_service import (
    TicketExecutionApplicationService,
)
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import (
    TicketStatusRecord,
)
from src.domain.ticket import Ticket


ACTOR_ADMIN_ID = 10
EXECUTOR_ADMIN_ID = 11
OTHER_ADMIN_ID = 12

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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def future_datetime(*, hours: int) -> datetime:
    return utc_now() + timedelta(hours=hours)


def past_datetime(*, hours: int) -> datetime:
    return utc_now() - timedelta(hours=hours)


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
    ticket = make_ticket(
        department_id=department_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ACTOR_ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )
    )

    return ticket


def make_scheduled_ticket(
    *,
    department_id: int = DEPARTMENT_ID,
) -> Ticket:
    ticket = make_accepted_ticket(
        department_id=department_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ACTOR_ADMIN_ID,
            status=TicketStatus.SCHEDULED,
            planned_start_at=future_datetime(hours=2),
            planned_finish_at=future_datetime(hours=4),
        )
    )

    return ticket


def make_assigned_ticket(
    *,
    executor_id: int = EXECUTOR_ADMIN_ID,
    department_id: int = DEPARTMENT_ID,
) -> Ticket:
    ticket = make_accepted_ticket(
        department_id=department_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ACTOR_ADMIN_ID,
            status=TicketStatus.ASSIGNED,
            executor_id=executor_id,
        )
    )

    return ticket


def make_at_work_ticket(
    *,
    executor_id: int = EXECUTOR_ADMIN_ID,
    department_id: int = DEPARTMENT_ID,
) -> Ticket:
    ticket = make_assigned_ticket(
        executor_id=executor_id,
        department_id=department_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.AT_WORK,
            executor_id=executor_id,
            actual_started_at=past_datetime(hours=2),
        )
    )

    return ticket


def make_paused_ticket(
    *,
    executor_id: int = EXECUTOR_ADMIN_ID,
    department_id: int = DEPARTMENT_ID,
) -> Ticket:
    ticket = make_at_work_ticket(
        executor_id=executor_id,
        department_id=department_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.PAUSED,
            executor_id=executor_id,
            comment="Waiting for access",
        )
    )

    return ticket


def make_uow() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()

    uow.admins.add(
        ACTOR_ADMIN_ID,
        make_admin(employee_id=ACTOR_ADMIN_ID),
    )
    uow.admins.add(
        EXECUTOR_ADMIN_ID,
        make_admin(employee_id=EXECUTOR_ADMIN_ID),
    )
    uow.admins.add(
        OTHER_ADMIN_ID,
        make_admin(employee_id=OTHER_ADMIN_ID),
    )

    uow.departments.add(
        DEPARTMENT_ID,
        make_department(),
    )
    uow.departments.add(
        OTHER_DEPARTMENT_ID,
        make_department(
            department_id=OTHER_DEPARTMENT_ID,
        ),
    )

    return uow


def make_service(
    uow: FakeUnitOfWork,
    *,
    actor: object | None = None,
    actor_error: Exception | None = None,
) -> tuple[
    TicketExecutionApplicationService,
    FakeActorHelper,
]:
    service = TicketExecutionApplicationService(uow)

    fake_actor = FakeActorHelper(
        actor=actor or make_admin(
            employee_id=EXECUTOR_ADMIN_ID,
        ),
        error=actor_error,
    )
    service.actor = fake_actor  # type: ignore[assignment]

    return service, fake_actor


def assert_ticket_operation_required(
    actor_helper: FakeActorHelper,
    *,
    actor_admin_id: int,
) -> None:
    assert actor_helper.calls == [
        {
            "actor_admin_id": actor_admin_id,
            "permission": AdminPermission.TICKET_OPERATION,
        }
    ]


# -------------------------------------------------------------------
# take_to_work
# -------------------------------------------------------------------


def test_take_to_work_moves_assigned_ticket_to_at_work() -> None:
    uow = make_uow()
    ticket = make_assigned_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(
        uow,
        actor=make_admin(
            employee_id=EXECUTOR_ADMIN_ID,
        ),
    )

    result = service.take_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Work started",
        )
    )

    assert ticket.current_status() is TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].actor_employee_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].executor_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].actual_started_at is not None
    assert ticket.statuses[-1].comment == "Work started"

    assert result.statuses[-1]["status"] == TicketStatus.AT_WORK.value
    assert result.statuses[-1]["executor_id"] == EXECUTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(
        actor_helper,
        actor_admin_id=EXECUTOR_ADMIN_ID,
    )


def test_take_to_work_rejects_actor_who_is_not_current_executor() -> None:
    uow = make_uow()
    ticket = make_assigned_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=OTHER_ADMIN_ID,
        ),
    )

    with pytest.raises(DomainOperationError):
        service.take_to_work(
            ticket_dto=TicketDTO(
                actor_admin_id=OTHER_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.ASSIGNED
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# pause_work
# -------------------------------------------------------------------


def test_pause_work_moves_ticket_to_paused() -> None:
    uow = make_uow()
    ticket = make_at_work_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(
        uow,
        actor=make_admin(
            employee_id=EXECUTOR_ADMIN_ID,
        ),
    )

    result = service.pause_work(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Waiting for a replacement part",
        )
    )

    assert ticket.current_status() is TicketStatus.PAUSED
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].actor_employee_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].executor_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].comment == "Waiting for a replacement part"

    assert result.statuses[-1]["status"] == TicketStatus.PAUSED.value
    assert uow.tickets.saved == [ticket]

    assert_ticket_operation_required(
        actor_helper,
        actor_admin_id=EXECUTOR_ADMIN_ID,
    )


def test_pause_work_rejects_actor_who_is_not_current_executor() -> None:
    uow = make_uow()
    ticket = make_at_work_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=OTHER_ADMIN_ID,
        ),
    )

    with pytest.raises(DomainOperationError):
        service.pause_work(
            ticket_dto=TicketDTO(
                actor_admin_id=OTHER_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.AT_WORK
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# resume_work
# -------------------------------------------------------------------


def test_resume_work_moves_ticket_to_at_work() -> None:
    uow = make_uow()
    ticket = make_paused_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(
        uow,
        actor=make_admin(
            employee_id=EXECUTOR_ADMIN_ID,
        ),
    )

    result = service.resume_work(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Access restored",
        )
    )

    assert ticket.current_status() is TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].actor_employee_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].executor_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].actual_started_at is not None
    assert ticket.statuses[-1].comment == "Access restored"

    assert result.statuses[-1]["status"] == TicketStatus.AT_WORK.value
    assert uow.tickets.saved == [ticket]

    assert_ticket_operation_required(
        actor_helper,
        actor_admin_id=EXECUTOR_ADMIN_ID,
    )


# -------------------------------------------------------------------
# submit_for_review
# -------------------------------------------------------------------


def test_submit_for_review_moves_ticket_to_ready_for_review() -> None:
    uow = make_uow()
    ticket = make_at_work_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(
        uow,
        actor=make_admin(
            employee_id=EXECUTOR_ADMIN_ID,
        ),
    )

    result = service.submit_for_review(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Work completed",
        )
    )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].actor_employee_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].executor_id == EXECUTOR_ADMIN_ID
    assert ticket.statuses[-1].actual_started_at is None
    assert ticket.statuses[-1].actual_finished_at is not None
    assert ticket.statuses[-1].comment == "Work completed"

    assert result.statuses[-1]["status"] == (
        TicketStatus.READY_FOR_REVIEW.value
    )
    assert uow.tickets.saved == [ticket]

    assert_ticket_operation_required(
        actor_helper,
        actor_admin_id=EXECUTOR_ADMIN_ID,
    )


def test_submit_for_review_rejects_actor_who_is_not_current_executor() -> None:
    uow = make_uow()
    ticket = make_at_work_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=OTHER_ADMIN_ID,
        ),
    )

    with pytest.raises(DomainOperationError):
        service.submit_for_review(
            ticket_dto=TicketDTO(
                actor_admin_id=OTHER_ADMIN_ID,
                ticket_id=TICKET_ID,
                comment="Completed",
            )
        )

    assert ticket.current_status() is TicketStatus.AT_WORK
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# record_completed_work_for_review
# -------------------------------------------------------------------


def test_record_completed_work_for_review_registers_offline_work() -> None:
    uow = make_uow()
    ticket = make_scheduled_ticket()
    uow.tickets.add(ticket)

    actual_started_at = past_datetime(hours=4)
    actual_finished_at = past_datetime(hours=1)

    service, actor_helper = make_service(
        uow,
        actor=make_admin(
            employee_id=ACTOR_ADMIN_ID,
        ),
    )

    result = service.record_completed_work_for_review(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            executor_id=EXECUTOR_ADMIN_ID,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            comment="Offline work registered by dispatcher",
        )
    )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID

    record = ticket.statuses[-1]
    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.executor_id == EXECUTOR_ADMIN_ID
    assert record.actual_started_at == actual_started_at
    assert record.actual_finished_at == actual_finished_at
    assert record.comment == "Offline work registered by dispatcher"

    assert result.statuses[-1]["status"] == (
        TicketStatus.READY_FOR_REVIEW.value
    )
    assert result.statuses[-1]["executor_id"] == EXECUTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(
        actor_helper,
        actor_admin_id=ACTOR_ADMIN_ID,
    )


@pytest.mark.parametrize(
    (
        "actual_started_at",
        "actual_finished_at",
        "expected_error",
    ),
    [
        (
            None,
            past_datetime(hours=1),
            "actual_started_at is required",
        ),
        (
            past_datetime(hours=2),
            None,
            "actual_finished_at is required",
        ),
    ],
)
def test_record_completed_work_requires_actual_dates(
    actual_started_at: datetime | None,
    actual_finished_at: datetime | None,
    expected_error: str,
) -> None:
    uow = make_uow()
    ticket = make_scheduled_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=ACTOR_ADMIN_ID,
        ),
    )

    with pytest.raises(
        DomainOperationError,
        match=expected_error,
    ):
        service.record_completed_work_for_review(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=EXECUTOR_ADMIN_ID,
                actual_started_at=actual_started_at,
                actual_finished_at=actual_finished_at,
            )
        )

    assert ticket.current_status() is TicketStatus.SCHEDULED
    assert uow.tickets.saved == []


@pytest.mark.parametrize(
    (
        "executor_id",
        "executor_department_id",
        "executor_enabled",
        "expected_error",
    ),
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
def test_record_completed_work_rejects_invalid_executor_reference(
    executor_id: int,
    executor_department_id: int,
    executor_enabled: bool,
    expected_error: str,
) -> None:
    uow = make_uow()
    ticket = make_scheduled_ticket()
    uow.tickets.add(ticket)

    if executor_id > 0:
        uow.admins.add(
            EXECUTOR_ADMIN_ID,
            make_admin(
                employee_id=EXECUTOR_ADMIN_ID,
                department_id=executor_department_id,
                enabled=executor_enabled,
            ),
        )

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=ACTOR_ADMIN_ID,
        ),
    )

    with pytest.raises(
        DomainOperationError,
        match=expected_error,
    ):
        service.record_completed_work_for_review(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=executor_id,
                actual_started_at=past_datetime(hours=3),
                actual_finished_at=past_datetime(hours=1),
            )
        )

    assert ticket.current_status() is TicketStatus.SCHEDULED
    assert uow.tickets.saved == []


def test_record_completed_work_rejects_disabled_ticket_department() -> None:
    uow = make_uow()
    ticket = make_scheduled_ticket()
    uow.tickets.add(ticket)

    uow.departments.add(
        DEPARTMENT_ID,
        make_department(enabled=False),
    )

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=ACTOR_ADMIN_ID,
        ),
    )

    with pytest.raises(
        DomainOperationError,
        match=f"Department {DEPARTMENT_ID} is disabled",
    ):
        service.record_completed_work_for_review(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=EXECUTOR_ADMIN_ID,
                actual_started_at=past_datetime(hours=3),
                actual_finished_at=past_datetime(hours=1),
            )
        )

    assert ticket.current_status() is TicketStatus.SCHEDULED
    assert uow.tickets.saved == []


def test_record_completed_work_rejects_executor_different_from_current() -> None:
    uow = make_uow()
    ticket = make_assigned_ticket(
        executor_id=EXECUTOR_ADMIN_ID,
    )
    uow.tickets.add(ticket)

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=ACTOR_ADMIN_ID,
        ),
    )

    with pytest.raises(DomainOperationError):
        service.record_completed_work_for_review(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=OTHER_ADMIN_ID,
                actual_started_at=past_datetime(hours=3),
                actual_finished_at=past_datetime(hours=1),
            )
        )

    assert ticket.current_status() is TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# Application-layer boundaries
# -------------------------------------------------------------------


def test_execution_operation_does_not_need_client_lookup() -> None:
    """
    FakeUnitOfWork intentionally has no clients repository.

    Current executor must be able to complete in-progress work even
    when Client is disabled or its state changes independently.
    """
    uow = make_uow()
    ticket = make_at_work_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(
        uow,
        actor=make_admin(
            employee_id=EXECUTOR_ADMIN_ID,
        ),
    )

    service.pause_work(
        ticket_dto=TicketDTO(
            actor_admin_id=EXECUTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
        )
    )

    assert ticket.current_status() is TicketStatus.PAUSED
    assert uow.tickets.saved == [ticket]


def test_execution_operation_does_not_load_ticket_when_rbac_denies_actor() -> None:
    uow = make_uow()
    ticket = make_assigned_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(
        uow,
        actor_error=DomainOperationError("Permission denied"),
    )

    with pytest.raises(
        DomainOperationError,
        match="Permission denied",
    ):
        service.take_to_work(
            ticket_dto=TicketDTO(
                actor_admin_id=EXECUTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert uow.tickets.get_calls == []
    assert uow.tickets.saved == []

    assert_ticket_operation_required(
        actor_helper,
        actor_admin_id=EXECUTOR_ADMIN_ID,
    )