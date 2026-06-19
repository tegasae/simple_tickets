# tests/domain/test_ticket_status_record_factory.py

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory

NOW = datetime.now(timezone.utc)
PAST_START = NOW - timedelta(hours=2)
PAST_FINISH = NOW - timedelta(hours=1)
FUTURE_START = NOW + timedelta(days=1)
FUTURE_FINISH = NOW + timedelta(days=1, hours=1)


# ----------------------------
# CREATED / ACCEPTED
# ----------------------------


def test_created_creates_created_status_record() -> None:
    record = TicketStatusRecordFactory.created(
        actor_employee_id=1,
    )

    assert record.status == TicketStatus.CREATED
    assert record.actor_employee_id == 1
    assert record.executor_id == 0
    assert record.planned_start_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None
    assert record.is_new()


def test_created_can_have_comment() -> None:
    record = TicketStatusRecordFactory.created(
        actor_employee_id=1,
        comment="  created by phone  ",
    )

    assert record.status == TicketStatus.CREATED
    assert record.comment == "created by phone"


def test_accepted_creates_accepted_status_record() -> None:
    record = TicketStatusRecordFactory.accepted(
        actor_employee_id=1,
    )

    assert record.status == TicketStatus.ACCEPTED
    assert record.actor_employee_id == 1
    assert record.executor_id == 0
    assert record.planned_start_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None
    assert record.is_new()


# ----------------------------
# REJECTED / DEFERRED / CANCELLED
# ----------------------------


def test_rejected_requires_comment() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.rejected(
            actor_employee_id=1,
            comment="",
        )


def test_rejected_creates_rejected_status_record() -> None:
    record = TicketStatusRecordFactory.rejected(
        actor_employee_id=1,
        comment="invalid request",
    )

    assert record.status == TicketStatus.REJECTED
    assert record.actor_employee_id == 1
    assert record.comment == "invalid request"


def test_deferred_requires_comment() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.deferred(
            actor_employee_id=1,
            comment="",
        )


def test_deferred_creates_deferred_status_record() -> None:
    record = TicketStatusRecordFactory.deferred(
        actor_employee_id=1,
        comment="waiting for client data",
    )

    assert record.status == TicketStatus.DEFERRED
    assert record.actor_employee_id == 1
    assert record.comment == "waiting for client data"


def test_cancelled_requires_comment() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.cancelled(
            actor_employee_id=1,
            comment="",
        )


def test_cancelled_creates_cancelled_status_record() -> None:
    record = TicketStatusRecordFactory.cancelled(
        actor_employee_id=1,
        comment="client cancelled request",
    )

    assert record.status == TicketStatus.CANCELLED
    assert record.actor_employee_id == 1
    assert record.comment == "client cancelled request"


# ----------------------------
# SCHEDULED
# ----------------------------


def test_scheduled_creates_scheduled_without_executor() -> None:
    record = TicketStatusRecordFactory.scheduled(
        actor_employee_id=1,
        planned_start_at=FUTURE_START,
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.actor_employee_id == 1
    assert record.executor_id == 0
    assert record.planned_start_at == FUTURE_START
    assert record.planned_finish_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None


def test_scheduled_can_have_planned_finish() -> None:
    record = TicketStatusRecordFactory.scheduled(
        actor_employee_id=1,
        planned_start_at=FUTURE_START,
        planned_finish_at=FUTURE_FINISH,
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.planned_start_at == FUTURE_START
    assert record.planned_finish_at == FUTURE_FINISH


# ----------------------------
# ASSIGNED
# ----------------------------


def test_assigned_requires_executor() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.assigned(
            actor_employee_id=1,
            executor_id=0,
        )


def test_assigned_creates_assigned_without_planned_time() -> None:
    record = TicketStatusRecordFactory.assigned(
        actor_employee_id=1,
        executor_id=10,
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.actor_employee_id == 1
    assert record.executor_id == 10
    assert record.planned_start_at is None
    assert record.planned_finish_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None


# ----------------------------
# READY_TO_WORK
# ----------------------------


def test_ready_to_work_requires_executor() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.ready_to_work(
            actor_employee_id=1,
            executor_id=0,
            planned_start_at=FUTURE_START,
        )


def test_ready_to_work_creates_ready_to_work_with_executor_and_planned_start() -> None:
    record = TicketStatusRecordFactory.ready_to_work(
        actor_employee_id=1,
        executor_id=10,
        planned_start_at=FUTURE_START,
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.actor_employee_id == 1
    assert record.executor_id == 10
    assert record.planned_start_at == FUTURE_START
    assert record.planned_finish_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None


def test_ready_to_work_can_have_planned_finish() -> None:
    record = TicketStatusRecordFactory.ready_to_work(
        actor_employee_id=1,
        executor_id=10,
        planned_start_at=FUTURE_START,
        planned_finish_at=FUTURE_FINISH,
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == 10
    assert record.planned_start_at == FUTURE_START
    assert record.planned_finish_at == FUTURE_FINISH


# ----------------------------
# AT_WORK
# ----------------------------


def test_at_work_requires_executor() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.at_work(
            actor_employee_id=1,
            executor_id=0,
        )


def test_at_work_creates_at_work_and_sets_actual_started_at() -> None:
    before = datetime.now(timezone.utc)

    record = TicketStatusRecordFactory.at_work(
        actor_employee_id=1,
        executor_id=10,
    )

    after = datetime.now(timezone.utc)

    assert record.status == TicketStatus.AT_WORK
    assert record.actor_employee_id == 1
    assert record.executor_id == 10
    assert record.actual_started_at is not None
    assert before <= record.actual_started_at <= after
    assert record.actual_finished_at is None
    assert record.planned_start_at is None
    assert record.planned_finish_at is None


# ----------------------------
# PAUSED
# ----------------------------


def test_paused_requires_executor() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.paused(
            actor_employee_id=1,
            executor_id=0,
        )


def test_paused_creates_paused_with_executor() -> None:
    record = TicketStatusRecordFactory.paused(
        actor_employee_id=1,
        executor_id=10,
    )

    assert record.status == TicketStatus.PAUSED
    assert record.actor_employee_id == 1
    assert record.executor_id == 10
    assert record.planned_start_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None


# ----------------------------
# OFFLINE_WORK
# ----------------------------


def test_offline_work_requires_executor() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.offline_work(
            actor_employee_id=1,
            executor_id=0,
            actual_started_at=PAST_START,
            actual_finished_at=PAST_FINISH,
        )


def test_offline_work_creates_offline_work_with_actual_start_and_finish() -> None:
    record = TicketStatusRecordFactory.offline_work(
        actor_employee_id=1,
        executor_id=10,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
    )

    assert record.status == TicketStatus.OFFLINE_WORK
    assert record.actor_employee_id == 1
    assert record.executor_id == 10
    assert record.actual_started_at == PAST_START
    assert record.actual_finished_at == PAST_FINISH
    assert record.planned_start_at is None
    assert record.planned_finish_at is None


def test_offline_work_rejects_future_actual_start() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.offline_work(
            actor_employee_id=1,
            executor_id=10,
            actual_started_at=FUTURE_START,
            actual_finished_at=FUTURE_FINISH,
        )


def test_offline_work_rejects_finish_before_start() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.offline_work(
            actor_employee_id=1,
            executor_id=10,
            actual_started_at=PAST_FINISH,
            actual_finished_at=PAST_START,
        )


# ----------------------------
# READY_FOR_REVIEW
# ----------------------------


def test_ready_for_review_requires_executor() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecordFactory.ready_for_review(
            actor_employee_id=1,
            executor_id=0,
        )


def test_ready_for_review_sets_actual_finished_at_automatically() -> None:
    before = datetime.now(timezone.utc)

    record = TicketStatusRecordFactory.ready_for_review(
        actor_employee_id=1,
        executor_id=10,
    )

    after = datetime.now(timezone.utc)

    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.actor_employee_id == 1
    assert record.executor_id == 10
    assert record.actual_finished_at is not None
    assert before <= record.actual_finished_at <= after
    assert record.planned_start_at is None
    assert record.planned_finish_at is None


def test_ready_for_review_can_use_explicit_actual_finished_at() -> None:
    record = TicketStatusRecordFactory.ready_for_review(
        actor_employee_id=1,
        executor_id=10,
        actual_finished_at=PAST_FINISH,
    )

    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.executor_id == 10
    assert record.actual_finished_at == PAST_FINISH


# ----------------------------
# EXECUTED
# ----------------------------


def test_executed_creates_executed_status_record() -> None:
    record = TicketStatusRecordFactory.executed(
        actor_employee_id=1,
    )

    assert record.status == TicketStatus.EXECUTED
    assert record.actor_employee_id == 1
    assert record.executor_id == 0
    assert record.planned_start_at is None
    assert record.actual_started_at is None
    assert record.actual_finished_at is None


def test_executed_can_have_comment() -> None:
    record = TicketStatusRecordFactory.executed(
        actor_employee_id=1,
        comment="confirmed by client",
    )

    assert record.status == TicketStatus.EXECUTED
    assert record.comment == "confirmed by client"