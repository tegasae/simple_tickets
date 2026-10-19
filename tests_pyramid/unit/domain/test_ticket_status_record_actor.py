from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.CREATED_FROM_TICKET_USER,
        TicketStatus.CANCELLED_BY_USER,
    ],
)
def test_user_driven_internal_status_requires_zero_actor(
    status: TicketStatus,
) -> None:
    record = TicketStatusRecord(
        actor_employee_id=0,
        status=status,
    )

    assert record.actor_employee_id == 0


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.CREATED_FROM_TICKET_USER,
        TicketStatus.CANCELLED_BY_USER,
    ],
)
def test_user_driven_internal_status_rejects_positive_actor(
    status: TicketStatus,
) -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=100,
            status=status,
        )


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
def test_admin_workflow_status_rejects_zero_actor(
    status: TicketStatus,
) -> None:
    with pytest.raises(ItemValidationError):
        TicketStatusRecord(
            actor_employee_id=0,
            status=status,
        )
