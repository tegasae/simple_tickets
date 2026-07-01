

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.tickets.ticket_review_service import (
    TicketReviewApplicationService,
)
from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.rbac.permissions import AdminPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import (
    TicketStatusRecord,
)
from src.domain.ticket import Ticket


ACTOR_ADMIN_ID = 10
EXECUTOR_ADMIN_ID = 11
OTHER_EXECUTOR_ADMIN_ID = 12

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


def past_datetime(*, hours: int) -> datetime:
    return utc_now() - timedelta(hours=hours)


def future_datetime(*, hours: int) -> datetime:
    return utc_now() + timedelta(hours=hours)


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


def make_review_ticket(
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
            comment="Assigned to executor",
        )
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.AT_WORK,
            executor_id=executor_id,
            actual_started_at=past_datetime(hours=3),
            comment="Work started",
        )
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=executor_id,
            actual_finished_at=past_datetime(hours=1),
            comment="Work completed",
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
        OTHER_EXECUTOR_ADMIN_ID,
        make_admin(employee_id=OTHER_EXECUTOR_ADMIN_ID),
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
    TicketReviewApplicationService,
    FakeActorHelper,
]:
    service = TicketReviewApplicationService(uow)

    fake_actor = FakeActorHelper(
        actor=actor or make_admin(
            employee_id=ACTOR_ADMIN_ID,
        ),
        error=actor_error,
    )
    service.actor = fake_actor  # type: ignore[assignment]

    return service, fake_actor


def assert_ticket_operation_required(
    actor_helper: FakeActorHelper,
    *,
    actor_admin_id: int = ACTOR_ADMIN_ID,
) -> None:
    assert actor_helper.calls == [
        {
            "actor_admin_id": actor_admin_id,
            "permission": AdminPermission.TICKET_OPERATION,
        }
    ]


# -------------------------------------------------------------------
# confirm_execution
# -------------------------------------------------------------------


def test_confirm_execution_moves_ticket_to_executed() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.confirm_execution(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Execution confirmed",
        )
    )

    assert ticket.current_status() is TicketStatus.EXECUTED
    assert ticket.statuses[-1].actor_employee_id == ACTOR_ADMIN_ID
    assert ticket.statuses[-1].comment == "Execution confirmed"
    assert ticket.is_terminal() is True

    assert result.is_closed is True
    assert result.statuses[-1]["status"] == TicketStatus.EXECUTED.value

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


# -------------------------------------------------------------------
# return_to_work
# -------------------------------------------------------------------


def test_return_to_work_returns_ticket_to_current_executor() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.return_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Please fix the remaining issue",
        )
    )

    assert ticket.current_status() is TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ADMIN_ID

    record = ticket.statuses[-1]
    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.executor_id == EXECUTOR_ADMIN_ID
    assert record.actual_started_at is not None
    assert record.comment == "Please fix the remaining issue"

    assert result.statuses[-1]["status"] == TicketStatus.AT_WORK.value
    assert result.statuses[-1]["executor_id"] == EXECUTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


# -------------------------------------------------------------------
# return_to_assigned
# -------------------------------------------------------------------


def test_return_to_assigned_assigns_selected_executor() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.return_to_assigned(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            executor_id=OTHER_EXECUTOR_ADMIN_ID,
            comment="Assign to another specialist",
        )
    )

    assert ticket.current_status() is TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == OTHER_EXECUTOR_ADMIN_ID

    record = ticket.statuses[-1]
    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.executor_id == OTHER_EXECUTOR_ADMIN_ID
    assert record.comment == "Assign to another specialist"

    assert result.statuses[-1]["status"] == TicketStatus.ASSIGNED.value
    assert result.statuses[-1]["executor_id"] == OTHER_EXECUTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


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
            OTHER_EXECUTOR_ADMIN_ID,
            DEPARTMENT_ID,
            False,
            f"disabled admin {OTHER_EXECUTOR_ADMIN_ID}",
        ),
        (
            OTHER_EXECUTOR_ADMIN_ID,
            0,
            True,
            f"Admin {OTHER_EXECUTOR_ADMIN_ID} has no department",
        ),
        (
            OTHER_EXECUTOR_ADMIN_ID,
            OTHER_DEPARTMENT_ID,
            True,
            f"belongs to department {OTHER_DEPARTMENT_ID}",
        ),
    ],
)
def test_return_to_assigned_rejects_invalid_executor_reference(
    executor_id: int,
    executor_department_id: int,
    executor_enabled: bool,
    expected_error: str,
) -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    if executor_id > 0:
        uow.admins.add(
            OTHER_EXECUTOR_ADMIN_ID,
            make_admin(
                employee_id=OTHER_EXECUTOR_ADMIN_ID,
                department_id=executor_department_id,
                enabled=executor_enabled,
            ),
        )

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match=expected_error,
    ):
        service.return_to_assigned(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=executor_id,
            )
        )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert uow.tickets.saved == []


def test_return_to_assigned_rejects_disabled_ticket_department() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
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
        service.return_to_assigned(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=OTHER_EXECUTOR_ADMIN_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# return_to_scheduled
# -------------------------------------------------------------------


def test_return_to_scheduled_moves_ticket_to_scheduled() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    planned_start_at = future_datetime(hours=2)
    planned_finish_at = future_datetime(hours=4)

    service, actor_helper = make_service(uow)

    result = service.return_to_scheduled(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="Schedule a new visit",
        )
    )

    assert ticket.current_status() is TicketStatus.SCHEDULED

    record = ticket.statuses[-1]
    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "Schedule a new visit"

    assert result.statuses[-1]["status"] == TicketStatus.SCHEDULED.value
    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


def test_return_to_scheduled_requires_planned_start_at() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match="planned_start_at is required",
    ):
        service.return_to_scheduled(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# return_to_ready_to_work
# -------------------------------------------------------------------


def test_return_to_ready_to_work_assigns_executor_and_plan() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    planned_start_at = future_datetime(hours=1)
    planned_finish_at = future_datetime(hours=3)

    service, actor_helper = make_service(uow)

    result = service.return_to_ready_to_work(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            executor_id=OTHER_EXECUTOR_ADMIN_ID,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment="Prepare for a repeat visit",
        )
    )

    assert ticket.current_status() is TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == OTHER_EXECUTOR_ADMIN_ID

    record = ticket.statuses[-1]
    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.executor_id == OTHER_EXECUTOR_ADMIN_ID
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "Prepare for a repeat visit"

    assert result.statuses[-1]["status"] == (
        TicketStatus.READY_TO_WORK.value
    )
    assert result.statuses[-1]["executor_id"] == OTHER_EXECUTOR_ADMIN_ID

    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


def test_return_to_ready_to_work_requires_planned_start_at() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        DomainOperationError,
        match="planned_start_at is required",
    ):
        service.return_to_ready_to_work(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                executor_id=OTHER_EXECUTOR_ADMIN_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# return_to_deferred
# -------------------------------------------------------------------


def test_return_to_deferred_moves_ticket_to_deferred() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(uow)

    result = service.return_to_deferred(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
            comment="Waiting for customer confirmation",
        )
    )

    assert ticket.current_status() is TicketStatus.DEFERRED

    record = ticket.statuses[-1]
    assert record.actor_employee_id == ACTOR_ADMIN_ID
    assert record.comment == "Waiting for customer confirmation"

    assert result.statuses[-1]["status"] == TicketStatus.DEFERRED.value
    assert uow.tickets.saved == [ticket]
    assert_ticket_operation_required(actor_helper)


def test_return_to_deferred_requires_nonempty_comment() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(
        ItemValidationError,
        match="DEFERRED requires comment",
    ):
        service.return_to_deferred(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
                comment="",
            )
        )

    assert ticket.current_status() is TicketStatus.READY_FOR_REVIEW
    assert uow.tickets.saved == []


# -------------------------------------------------------------------
# Application-layer boundaries
# -------------------------------------------------------------------


def test_review_operation_does_not_need_client_lookup() -> None:
    """
    FakeUnitOfWork intentionally has no clients repository.

    Review must remain possible even if Client is disabled later.
    """
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    service.confirm_execution(
        ticket_dto=TicketDTO(
            actor_admin_id=ACTOR_ADMIN_ID,
            ticket_id=TICKET_ID,
        )
    )

    assert ticket.current_status() is TicketStatus.EXECUTED
    assert uow.tickets.saved == [ticket]


def test_review_operation_does_not_save_when_ticket_is_not_in_review() -> None:
    uow = make_uow()
    ticket = make_accepted_ticket()
    uow.tickets.add(ticket)

    service, _ = make_service(uow)

    with pytest.raises(DomainOperationError):
        service.confirm_execution(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert ticket.current_status() is TicketStatus.ACCEPTED
    assert uow.tickets.saved == []


def test_review_operation_does_not_load_ticket_when_rbac_denies_actor() -> None:
    uow = make_uow()
    ticket = make_review_ticket()
    uow.tickets.add(ticket)

    service, actor_helper = make_service(
        uow,
        actor_error=DomainOperationError("Permission denied"),
    )

    with pytest.raises(
        DomainOperationError,
        match="Permission denied",
    ):
        service.confirm_execution(
            ticket_dto=TicketDTO(
                actor_admin_id=ACTOR_ADMIN_ID,
                ticket_id=TICKET_ID,
            )
        )

    assert uow.tickets.get_calls == []
    assert uow.tickets.saved == []

    assert_ticket_operation_required(actor_helper)

