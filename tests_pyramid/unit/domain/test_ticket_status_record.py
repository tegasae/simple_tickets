from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_create_new_and_create_from_ticket_user_have_correct_actor_semantics() -> None:
    created = TicketStatusRecord.create_new(actor_employee_id=10, date_created=BASE)
    from_user = TicketStatusRecord.create_from_ticket_user(date_created=BASE)
    assert created.status is TicketStatus.CREATED
    assert created.actor_employee_id == 10
    assert from_user.status is TicketStatus.CREATED_FROM_TICKET_USER
    assert from_user.actor_employee_id == 0


@pytest.mark.parametrize(
    "status",
    [TicketStatus.CREATED_FROM_TICKET_USER, TicketStatus.CANCELLED_BY_USER],
)
def test_user_driven_status_requires_zero_actor(status: TicketStatus) -> None:
    TicketStatusRecord(actor_employee_id=0, status=status, date_created=BASE)
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(actor_employee_id=1, status=status, date_created=BASE)


@pytest.mark.parametrize(
    "factory,kwargs",
    [
        (TicketStatusRecord.create_accepted, {}),
        (TicketStatusRecord.create_rejected, {"comment": "reason"}),
        (TicketStatusRecord.create_deferred, {"comment": "reason"}),
        (TicketStatusRecord.create_scheduled, {"planned_start_at": BASE}),
        (TicketStatusRecord.create_assigned, {"executor_id": 20}),
        (TicketStatusRecord.create_ready_to_work, {"executor_id": 20, "planned_start_at": BASE}),
        (TicketStatusRecord.create_cancelled, {"comment": "reason"}),
        (TicketStatusRecord.create_at_work, {"executor_id": 20}),
        (TicketStatusRecord.create_paused, {"executor_id": 20}),
        (TicketStatusRecord.create_executed, {}),
    ],
)
def test_admin_factories_require_positive_actor(factory, kwargs) -> None:
    with pytest.raises(ItemValidationError):
        factory(actor_employee_id=0, date_created=BASE, **kwargs)


def test_required_comment_statuses_reject_blank_comment() -> None:
    for factory in (
        TicketStatusRecord.create_rejected,
        TicketStatusRecord.create_deferred,
        TicketStatusRecord.create_cancelled,
    ):
        with pytest.raises(ItemValidationError):
            factory(actor_employee_id=1, comment="   ", date_created=BASE)


def test_executor_payload_is_required_or_forbidden_by_state() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=1,
            status=TicketStatus.ASSIGNED,
            executor_id=0,
            date_created=BASE,
        )
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=1,
            status=TicketStatus.ACCEPTED,
            executor_id=2,
            date_created=BASE,
        )


def test_planned_payload_validation() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=1,
            status=TicketStatus.SCHEDULED,
            date_created=BASE,
        )
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=1,
            status=TicketStatus.ACCEPTED,
            planned_start_at=BASE,
            date_created=BASE,
        )


def test_actual_payload_validation_and_ranges() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=1,
            status=TicketStatus.AT_WORK,
            executor_id=2,
            date_created=BASE,
        )
    with pytest.raises(ItemValidationError):
        TicketStatusRecord.create_ready_for_review_retrospective(
            actor_employee_id=1,
            executor_id=2,
            actual_started_at=BASE,
            actual_finished_at=BASE - timedelta(seconds=1),
            date_created=BASE,
        )


def test_actual_times_cannot_be_after_record_time() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord.create_ready_for_review_retrospective(
            actor_employee_id=1,
            executor_id=2,
            actual_started_at=BASE,
            actual_finished_at=BASE + timedelta(seconds=1),
            date_created=BASE,
        )


def test_record_time_cannot_be_future() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord.create_accepted(
            actor_employee_id=1,
            date_created=datetime.now(timezone.utc) + timedelta(days=1),
        )


def test_datetime_normalization_to_utc() -> None:
    naive = datetime(2025, 1, 1, 12, 0)
    record = TicketStatusRecord.create_accepted(actor_employee_id=1, date_created=naive)
    assert record.date_created.tzinfo is timezone.utc


def test_comment_is_trimmed_and_limited() -> None:
    record = TicketStatusRecord.create_accepted(
        actor_employee_id=1,
        comment="  hello  ",
        date_created=BASE,
    )
    assert record.comment == "hello"
    with pytest.raises(ItemValidationError):
        TicketStatusRecord.create_accepted(
            actor_employee_id=1,
            comment="x" * 1001,
            date_created=BASE,
        )


def test_review_transition_from_at_work_forbids_duplicate_actual_start() -> None:
    previous = TicketStatusRecord.create_at_work(
        actor_employee_id=1,
        executor_id=2,
        date_created=BASE,
    )
    normal = TicketStatusRecord.create_ready_for_review_from_work(
        actor_employee_id=2,
        executor_id=2,
        date_created=BASE + timedelta(minutes=10),
    )
    previous.validate_review_transition(normal)

    retrospective = TicketStatusRecord.create_ready_for_review_retrospective(
        actor_employee_id=2,
        executor_id=2,
        actual_started_at=BASE,
        actual_finished_at=BASE + timedelta(minutes=10),
        date_created=BASE + timedelta(minutes=10),
    )
    with pytest.raises(DomainOperationError):
        previous.validate_review_transition(retrospective)


def test_review_transition_from_management_state_requires_actual_start() -> None:
    previous = TicketStatusRecord.create_assigned(
        actor_employee_id=1,
        executor_id=2,
        date_created=BASE,
    )
    normal = TicketStatusRecord.create_ready_for_review_from_work(
        actor_employee_id=2,
        executor_id=2,
        date_created=BASE + timedelta(minutes=10),
    )
    with pytest.raises(DomainOperationError):
        previous.validate_review_transition(normal)

    retrospective = TicketStatusRecord.create_ready_for_review_retrospective(
        actor_employee_id=2,
        executor_id=2,
        actual_started_at=BASE,
        actual_finished_at=BASE + timedelta(minutes=10),
        date_created=BASE + timedelta(minutes=10),
    )
    previous.validate_review_transition(retrospective)
