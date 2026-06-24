import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket_workflow_policy import TicketWorkflowPolicy
from src.domain.statuses.ticket_status import TicketStatus


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (TicketStatus.CREATED, TicketStatus.ACCEPTED),
        (TicketStatus.CREATED, TicketStatus.REJECTED),
        (TicketStatus.ACCEPTED, TicketStatus.DEFERRED),
        (TicketStatus.ACCEPTED, TicketStatus.SCHEDULED),
        (TicketStatus.ACCEPTED, TicketStatus.ASSIGNED),
        (TicketStatus.ACCEPTED, TicketStatus.READY_TO_WORK),
        (TicketStatus.ACCEPTED, TicketStatus.CANCELLED),
        (TicketStatus.DEFERRED, TicketStatus.ACCEPTED),
        (TicketStatus.DEFERRED, TicketStatus.SCHEDULED),
        (TicketStatus.SCHEDULED, TicketStatus.SCHEDULED),
        (TicketStatus.SCHEDULED, TicketStatus.READY_TO_WORK),
        (TicketStatus.SCHEDULED, TicketStatus.ASSIGNED),
        (TicketStatus.ASSIGNED, TicketStatus.AT_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.OFFLINE_WORK),
        (TicketStatus.READY_TO_WORK, TicketStatus.AT_WORK),
        (TicketStatus.READY_TO_WORK, TicketStatus.OFFLINE_WORK),
        (TicketStatus.AT_WORK, TicketStatus.PAUSED),
        (TicketStatus.AT_WORK, TicketStatus.READY_FOR_REVIEW),
        (TicketStatus.PAUSED, TicketStatus.AT_WORK),
        (TicketStatus.OFFLINE_WORK, TicketStatus.READY_FOR_REVIEW),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.EXECUTED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.AT_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.ASSIGNED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.SCHEDULED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.READY_TO_WORK),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.DEFERRED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.CANCELLED),
    ],
)
def test_ensure_can_change_status_allows_valid_transition(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    TicketWorkflowPolicy.ensure_can_change_status(
        current_status=current_status,
        new_status=new_status,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (TicketStatus.CREATED, TicketStatus.CANCELLED),
        (TicketStatus.CREATED, TicketStatus.AT_WORK),
        (TicketStatus.CREATED, TicketStatus.READY_FOR_REVIEW),
        (TicketStatus.ACCEPTED, TicketStatus.AT_WORK),
        (TicketStatus.ACCEPTED, TicketStatus.EXECUTED),
        (TicketStatus.DEFERRED, TicketStatus.AT_WORK),
        (TicketStatus.SCHEDULED, TicketStatus.AT_WORK),
        (TicketStatus.SCHEDULED, TicketStatus.OFFLINE_WORK),
        (TicketStatus.ASSIGNED, TicketStatus.READY_FOR_REVIEW),
        (TicketStatus.AT_WORK, TicketStatus.EXECUTED),
        (TicketStatus.PAUSED, TicketStatus.READY_FOR_REVIEW),
        (TicketStatus.OFFLINE_WORK, TicketStatus.EXECUTED),
        (TicketStatus.READY_FOR_REVIEW, TicketStatus.PAUSED),
    ],
)
def test_ensure_can_change_status_rejects_invalid_transition(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> None:
    with pytest.raises(DomainOperationError):
        TicketWorkflowPolicy.ensure_can_change_status(
            current_status=current_status,
            new_status=new_status,
        )


@pytest.mark.parametrize(
    "terminal_status",
    [
        TicketStatus.REJECTED,
        TicketStatus.EXECUTED,
        TicketStatus.CANCELLED,
    ],
)
def test_terminal_status_rejects_every_transition(
    terminal_status: TicketStatus,
) -> None:
    with pytest.raises(DomainOperationError):
        TicketWorkflowPolicy.ensure_can_change_status(
            current_status=terminal_status,
            new_status=TicketStatus.ACCEPTED,
        )


def test_can_change_status_returns_true_for_valid_transition() -> None:
    assert TicketWorkflowPolicy.can_change_status(
        current_status=TicketStatus.ASSIGNED,
        new_status=TicketStatus.AT_WORK,
    )


def test_can_change_status_returns_false_for_invalid_transition() -> None:
    assert not TicketWorkflowPolicy.can_change_status(
        current_status=TicketStatus.CREATED,
        new_status=TicketStatus.CANCELLED,
    )


def test_can_change_status_returns_false_for_terminal_status() -> None:
    assert not TicketWorkflowPolicy.can_change_status(
        current_status=TicketStatus.EXECUTED,
        new_status=TicketStatus.ACCEPTED,
    )