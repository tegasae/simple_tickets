# tests/domain/statuses/test_ticket_status_record.py

from __future__ import annotations

import pytest

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord


def test_created_from_ticket_user_allows_zero_actor_employee_id() -> None:
    record = TicketStatusRecord(
        actor_employee_id=0,
        status=TicketStatus.CREATED_FROM_TICKET_USER,
    )

    assert record.actor_employee_id == 0
    assert record.status == TicketStatus.CREATED_FROM_TICKET_USER


def test_cancelled_by_user_allows_zero_actor_employee_id() -> None:
    record = TicketStatusRecord(
        actor_employee_id=0,
        status=TicketStatus.CANCELLED_BY_USER,
    )

    assert record.actor_employee_id == 0
    assert record.status == TicketStatus.CANCELLED_BY_USER


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
        TicketStatus.REJECTED,
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.AT_WORK,
        TicketStatus.PAUSED,
        TicketStatus.READY_FOR_REVIEW,
        TicketStatus.EXECUTED,
        TicketStatus.CANCELLED,
    ],
)
def test_zero_actor_employee_id_is_rejected_for_internal_admin_statuses(
    status: TicketStatus,
) -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=0,
            status=status,
        )


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.CREATED_FROM_TICKET_USER,
        TicketStatus.CANCELLED_BY_USER,
    ],
)
def test_positive_actor_employee_id_is_rejected_for_user_driven_statuses(
    status: TicketStatus,
) -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=100,
            status=status,
        )


def test_negative_actor_employee_id_is_rejected() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=-1,
            status=TicketStatus.CREATED,
        )


def test_negative_status_id_is_rejected() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            status_id=-1,
            actor_employee_id=100,
            status=TicketStatus.CREATED,
        )


def test_negative_executor_id_is_rejected() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=100,
            executor_id=-1,
            status=TicketStatus.ASSIGNED,
        )


def test_comment_is_required_for_deferred() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=100,
            status=TicketStatus.DEFERRED,
            comment="",
        )


def test_comment_is_required_for_rejected() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=100,
            status=TicketStatus.REJECTED,
            comment="",
        )


def test_comment_is_required_for_cancelled() -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=100,
            status=TicketStatus.CANCELLED,
            comment="",
        )


def test_comment_is_not_required_for_created_from_ticket_user() -> None:
    record = TicketStatusRecord(
        actor_employee_id=0,
        status=TicketStatus.CREATED_FROM_TICKET_USER,
        comment="",
    )

    assert record.status == TicketStatus.CREATED_FROM_TICKET_USER
    assert record.comment == ""


def test_comment_is_not_required_for_cancelled_by_user() -> None:
    record = TicketStatusRecord(
        actor_employee_id=0,
        status=TicketStatus.CANCELLED_BY_USER,
        comment="",
    )

    assert record.status == TicketStatus.CANCELLED_BY_USER
    assert record.comment == ""


def test_comment_is_stripped() -> None:
    record = TicketStatusRecord(
        actor_employee_id=100,
        status=TicketStatus.CANCELLED,
        comment="  reason  ",
    )

    assert record.comment == "reason"