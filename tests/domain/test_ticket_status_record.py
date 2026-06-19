# tests/domain/test_ticket_status_record.py

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord

NOW = datetime.now(timezone.utc)
PAST_START = NOW - timedelta(hours=2)
PAST_FINISH = NOW - timedelta(hours=1)
FUTURE = NOW + timedelta(hours=1)


def make_record(
    *,
    status: TicketStatus,
    actor_employee_id: int = 1,
    executor_id: int = 0,
    planned_start_at: datetime | None = None,
    planned_finish_at: datetime | None = None,
    actual_started_at: datetime | None = None,
    actual_finished_at: datetime | None = None,
    comment: str = "",
) -> TicketStatusRecord:
    return TicketStatusRecord(
        actor_employee_id=actor_employee_id,
        status=status,
        executor_id=executor_id,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        actual_started_at=actual_started_at,
        actual_finished_at=actual_finished_at,
        comment=comment,
    )


def assert_invalid(**kwargs) -> None:
    with pytest.raises(ItemValidationError):
        make_record(**kwargs)


# ----------------------------
# SCHEDULED
# ----------------------------


def test_scheduled_requires_planned_start() -> None:
    assert_invalid(status=TicketStatus.SCHEDULED)


def test_scheduled_cannot_have_executor() -> None:
    assert_invalid(
        status=TicketStatus.SCHEDULED,
        executor_id=10,
        planned_start_at=PAST_START,
    )


def test_scheduled_cannot_have_actual_time() -> None:
    assert_invalid(
        status=TicketStatus.SCHEDULED,
        planned_start_at=PAST_START,
        actual_started_at=PAST_START,
    )


def test_scheduled_can_have_planned_start_without_executor() -> None:
    record = make_record(
        status=TicketStatus.SCHEDULED,
        planned_start_at=PAST_START,
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.executor_id == 0
    assert record.planned_start_at == PAST_START


def test_scheduled_can_have_planned_start_and_planned_finish() -> None:
    record = make_record(
        status=TicketStatus.SCHEDULED,
        planned_start_at=PAST_START,
        planned_finish_at=PAST_FINISH,
    )

    assert record.planned_start_at == PAST_START
    assert record.planned_finish_at == PAST_FINISH


# ----------------------------
# ASSIGNED
# ----------------------------


def test_assigned_requires_executor() -> None:
    assert_invalid(status=TicketStatus.ASSIGNED)


def test_assigned_cannot_have_planned_time() -> None:
    assert_invalid(
        status=TicketStatus.ASSIGNED,
        executor_id=10,
        planned_start_at=PAST_START,
    )


def test_assigned_cannot_have_actual_time() -> None:
    assert_invalid(
        status=TicketStatus.ASSIGNED,
        executor_id=10,
        actual_started_at=PAST_START,
    )


def test_assigned_can_have_executor_without_planned_time() -> None:
    record = make_record(
        status=TicketStatus.ASSIGNED,
        executor_id=10,
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.executor_id == 10
    assert record.planned_start_at is None


# ----------------------------
# READY_TO_WORK
# ----------------------------


def test_ready_to_work_requires_executor() -> None:
    assert_invalid(
        status=TicketStatus.READY_TO_WORK,
        planned_start_at=PAST_START,
    )


def test_ready_to_work_requires_planned_start() -> None:
    assert_invalid(
        status=TicketStatus.READY_TO_WORK,
        executor_id=10,
    )


def test_ready_to_work_cannot_have_actual_time() -> None:
    assert_invalid(
        status=TicketStatus.READY_TO_WORK,
        executor_id=10,
        planned_start_at=PAST_START,
        actual_started_at=PAST_START,
    )


def test_ready_to_work_requires_executor_and_planned_start() -> None:
    record = make_record(
        status=TicketStatus.READY_TO_WORK,
        executor_id=10,
        planned_start_at=PAST_START,
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == 10
    assert record.planned_start_at == PAST_START


def test_ready_to_work_can_have_planned_finish() -> None:
    record = make_record(
        status=TicketStatus.READY_TO_WORK,
        executor_id=10,
        planned_start_at=PAST_START,
        planned_finish_at=PAST_FINISH,
    )

    assert record.planned_finish_at == PAST_FINISH


# ----------------------------
# AT_WORK
# ----------------------------


def test_at_work_requires_executor() -> None:
    assert_invalid(
        status=TicketStatus.AT_WORK,
        actual_started_at=PAST_START,
    )


def test_at_work_requires_actual_start() -> None:
    assert_invalid(
        status=TicketStatus.AT_WORK,
        executor_id=10,
    )


def test_at_work_cannot_have_actual_finish() -> None:
    assert_invalid(
        status=TicketStatus.AT_WORK,
        executor_id=10,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
    )


def test_at_work_cannot_have_planned_time() -> None:
    assert_invalid(
        status=TicketStatus.AT_WORK,
        executor_id=10,
        planned_start_at=PAST_START,
        actual_started_at=PAST_START,
    )


def test_at_work_can_have_executor_and_actual_start() -> None:
    record = make_record(
        status=TicketStatus.AT_WORK,
        executor_id=10,
        actual_started_at=PAST_START,
    )

    assert record.status == TicketStatus.AT_WORK
    assert record.executor_id == 10
    assert record.actual_started_at == PAST_START


# ----------------------------
# PAUSED
# ----------------------------


def test_paused_requires_executor() -> None:
    assert_invalid(status=TicketStatus.PAUSED)


def test_paused_cannot_have_planned_time() -> None:
    assert_invalid(
        status=TicketStatus.PAUSED,
        executor_id=10,
        planned_start_at=PAST_START,
    )


def test_paused_cannot_have_actual_time() -> None:
    assert_invalid(
        status=TicketStatus.PAUSED,
        executor_id=10,
        actual_started_at=PAST_START,
    )


def test_paused_can_have_executor() -> None:
    record = make_record(
        status=TicketStatus.PAUSED,
        executor_id=10,
    )

    assert record.status == TicketStatus.PAUSED
    assert record.executor_id == 10


# ----------------------------
# OFFLINE_WORK
# ----------------------------


def test_offline_work_requires_executor() -> None:
    assert_invalid(
        status=TicketStatus.OFFLINE_WORK,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
    )


def test_offline_work_requires_actual_start() -> None:
    assert_invalid(
        status=TicketStatus.OFFLINE_WORK,
        executor_id=10,
        actual_finished_at=PAST_FINISH,
    )


def test_offline_work_requires_actual_finish() -> None:
    assert_invalid(
        status=TicketStatus.OFFLINE_WORK,
        executor_id=10,
        actual_started_at=PAST_START,
    )


def test_offline_work_cannot_have_planned_time() -> None:
    assert_invalid(
        status=TicketStatus.OFFLINE_WORK,
        executor_id=10,
        planned_start_at=PAST_START,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
    )


def test_offline_work_can_have_executor_actual_start_and_actual_finish() -> None:
    record = make_record(
        status=TicketStatus.OFFLINE_WORK,
        executor_id=10,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
    )

    assert record.status == TicketStatus.OFFLINE_WORK
    assert record.executor_id == 10
    assert record.actual_started_at == PAST_START
    assert record.actual_finished_at == PAST_FINISH


# ----------------------------
# READY_FOR_REVIEW
# ----------------------------


def test_ready_for_review_requires_executor() -> None:
    assert_invalid(
        status=TicketStatus.READY_FOR_REVIEW,
        actual_finished_at=PAST_FINISH,
    )


def test_ready_for_review_requires_actual_finish() -> None:
    assert_invalid(
        status=TicketStatus.READY_FOR_REVIEW,
        executor_id=10,
    )


def test_ready_for_review_cannot_have_planned_time() -> None:
    assert_invalid(
        status=TicketStatus.READY_FOR_REVIEW,
        executor_id=10,
        planned_start_at=PAST_START,
        actual_finished_at=PAST_FINISH,
    )


def test_ready_for_review_can_have_executor_and_actual_finish() -> None:
    record = make_record(
        status=TicketStatus.READY_FOR_REVIEW,
        executor_id=10,
        actual_finished_at=PAST_FINISH,
    )

    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.executor_id == 10
    assert record.actual_finished_at == PAST_FINISH


# ----------------------------
# Non-work statuses
# ----------------------------


NON_WORK_STATUSES = [
    TicketStatus.CREATED,
    TicketStatus.ACCEPTED,
    TicketStatus.REJECTED,
    TicketStatus.DEFERRED,
    TicketStatus.EXECUTED,
    TicketStatus.CANCELLED,
]


@pytest.mark.parametrize("status", NON_WORK_STATUSES)
def test_non_work_statuses_cannot_have_executor(status: TicketStatus) -> None:
    assert_invalid(
        status=status,
        executor_id=10,
    )


@pytest.mark.parametrize("status", NON_WORK_STATUSES)
def test_non_work_statuses_cannot_have_planned_time(status: TicketStatus) -> None:
    assert_invalid(
        status=status,
        planned_start_at=PAST_START,
    )


@pytest.mark.parametrize("status", NON_WORK_STATUSES)
def test_non_work_statuses_cannot_have_actual_time(status: TicketStatus) -> None:
    assert_invalid(
        status=status,
        actual_started_at=PAST_START,
    )


@pytest.mark.parametrize("status", NON_WORK_STATUSES)
def test_non_work_statuses_can_be_created_without_work_payload(
    status: TicketStatus,
) -> None:
    record = make_record(status=status)

    assert record.status == status
    assert record.executor_id == 0
    assert record.planned_start_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None


# ----------------------------
# Common validation
# ----------------------------


def test_actor_employee_id_must_be_positive() -> None:
    assert_invalid(
        status=TicketStatus.CREATED,
        actor_employee_id=0,
    )


def test_executor_id_cannot_be_negative() -> None:
    assert_invalid(
        status=TicketStatus.CREATED,
        executor_id=-1,
    )


def test_status_id_cannot_be_negative() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            status_id=-1,
            actor_employee_id=1,
            status=TicketStatus.CREATED,
        )


def test_comment_is_stripped() -> None:
    record = make_record(
        status=TicketStatus.CREATED,
        comment="  hello  ",
    )

    assert record.comment == "hello"


def test_comment_cannot_be_too_long() -> None:
    assert_invalid(
        status=TicketStatus.CREATED,
        comment="x" * 1001,
    )


def test_planned_finish_cannot_be_before_planned_start() -> None:
    assert_invalid(
        status=TicketStatus.SCHEDULED,
        planned_start_at=PAST_FINISH,
        planned_finish_at=PAST_START,
    )


def test_actual_finish_cannot_be_before_actual_start() -> None:
    assert_invalid(
        status=TicketStatus.OFFLINE_WORK,
        executor_id=10,
        actual_started_at=PAST_FINISH,
        actual_finished_at=PAST_START,
    )


def test_actual_start_cannot_be_in_future() -> None:
    assert_invalid(
        status=TicketStatus.AT_WORK,
        executor_id=10,
        actual_started_at=FUTURE,
    )


def test_actual_finish_cannot_be_in_future() -> None:
    assert_invalid(
        status=TicketStatus.OFFLINE_WORK,
        executor_id=10,
        actual_started_at=PAST_START,
        actual_finished_at=FUTURE,
    )