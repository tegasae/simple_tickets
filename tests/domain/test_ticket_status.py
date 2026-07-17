# tests/domain/test_ticket_status.py

from dataclasses import dataclass

import pytest

from src.domain.statuses.ticket_status import TicketStatus, get_ticket_state


@dataclass(frozen=True, slots=True)
class ExpectedTicketState:
    terminal: bool
    requires_executor: bool
    requires_planned_start: bool
    work_started: bool
    locks_department_change: bool
    allows_ticket_text_update: bool
    allowed_next: frozenset[TicketStatus]


EXPECTED_STATES: dict[TicketStatus, ExpectedTicketState] = {
    TicketStatus.CREATED: ExpectedTicketState(
        terminal=False,
        requires_executor=False,
        requires_planned_start=False,
        work_started=False,
        locks_department_change=False,
        allows_ticket_text_update=True,
        allowed_next=frozenset(
            {
                TicketStatus.ACCEPTED,
                TicketStatus.REJECTED,
            }
        ),
    ),
    TicketStatus.REJECTED: ExpectedTicketState(
        terminal=True,
        requires_executor=False,
        requires_planned_start=False,
        work_started=False,
        locks_department_change=False,
        allows_ticket_text_update=False,
        allowed_next=frozenset(),
    ),
    TicketStatus.ACCEPTED: ExpectedTicketState(
        terminal=False,
        requires_executor=False,
        requires_planned_start=False,
        work_started=False,
        locks_department_change=False,
        allows_ticket_text_update=True,
        allowed_next=frozenset(
            {
                TicketStatus.DEFERRED,
                TicketStatus.SCHEDULED,
                TicketStatus.ASSIGNED,
                TicketStatus.READY_TO_WORK,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.DEFERRED: ExpectedTicketState(
        terminal=False,
        requires_executor=False,
        requires_planned_start=False,
        work_started=False,
        locks_department_change=False,
        allows_ticket_text_update=False,
        allowed_next=frozenset(
            {
                TicketStatus.ACCEPTED,
                TicketStatus.SCHEDULED,
                TicketStatus.ASSIGNED,
                TicketStatus.READY_TO_WORK,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.SCHEDULED: ExpectedTicketState(
        terminal=False,
        requires_executor=False,
        requires_planned_start=True,
        work_started=False,
        locks_department_change=False,
        allows_ticket_text_update=False,
        allowed_next=frozenset(
            {
                TicketStatus.SCHEDULED,
                TicketStatus.ACCEPTED,
                TicketStatus.DEFERRED,
                TicketStatus.ASSIGNED,
                TicketStatus.READY_TO_WORK,
                TicketStatus.READY_FOR_REVIEW,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.ASSIGNED: ExpectedTicketState(
        terminal=False,
        requires_executor=True,
        requires_planned_start=False,
        work_started=False,
        locks_department_change=True,
        allows_ticket_text_update=False,
        allowed_next=frozenset(
            {
                TicketStatus.ASSIGNED,
                TicketStatus.ACCEPTED,
                TicketStatus.DEFERRED,
                TicketStatus.SCHEDULED,
                TicketStatus.READY_TO_WORK,
                TicketStatus.AT_WORK,
                TicketStatus.READY_FOR_REVIEW,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.READY_TO_WORK: ExpectedTicketState(
        terminal=False,
        requires_executor=True,
        requires_planned_start=True,
        work_started=False,
        locks_department_change=True,
        allows_ticket_text_update=False,
        allowed_next=frozenset(
            {
                TicketStatus.READY_TO_WORK,
                TicketStatus.ACCEPTED,
                TicketStatus.DEFERRED,
                TicketStatus.SCHEDULED,
                TicketStatus.ASSIGNED,
                TicketStatus.AT_WORK,
                TicketStatus.READY_FOR_REVIEW,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.AT_WORK: ExpectedTicketState(
        terminal=False,
        requires_executor=True,
        requires_planned_start=False,
        work_started=True,
        locks_department_change=True,
        allows_ticket_text_update=False,
        allowed_next=frozenset(
            {
                TicketStatus.PAUSED,
                TicketStatus.READY_FOR_REVIEW,
                TicketStatus.DEFERRED,
                TicketStatus.SCHEDULED,
                TicketStatus.ASSIGNED,
                TicketStatus.READY_TO_WORK,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.PAUSED: ExpectedTicketState(
        terminal=False,
        requires_executor=True,
        requires_planned_start=False,
        work_started=True,
        locks_department_change=True,
        allows_ticket_text_update=False,
        allowed_next=frozenset(
            {
                TicketStatus.AT_WORK,
                TicketStatus.DEFERRED,
                TicketStatus.SCHEDULED,
                TicketStatus.ASSIGNED,
                TicketStatus.READY_TO_WORK,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.READY_FOR_REVIEW: ExpectedTicketState(
        terminal=False,
        requires_executor=True,
        requires_planned_start=False,
        work_started=True,
        locks_department_change=True,
        allows_ticket_text_update=False,
        allowed_next=frozenset(
            {
                TicketStatus.EXECUTED,
                TicketStatus.AT_WORK,
                TicketStatus.ASSIGNED,
                TicketStatus.SCHEDULED,
                TicketStatus.READY_TO_WORK,
                TicketStatus.DEFERRED,
                TicketStatus.CANCELLED,
            }
        ),
    ),
    TicketStatus.EXECUTED: ExpectedTicketState(
        terminal=True,
        requires_executor=False,
        requires_planned_start=False,
        work_started=False,
        locks_department_change=False,
        allows_ticket_text_update=False,
        allowed_next=frozenset(),
    ),
    TicketStatus.CANCELLED: ExpectedTicketState(
        terminal=True,
        requires_executor=False,
        requires_planned_start=False,
        work_started=False,
        locks_department_change=False,
        allows_ticket_text_update=False,
        allowed_next=frozenset(),
    ),
}


# ----------------------------
# TicketStatus enum
# ----------------------------


@pytest.mark.parametrize(
    ("status", "value"),
    [
        (TicketStatus.CREATED, "created"),
        (TicketStatus.REJECTED, "rejected"),
        (TicketStatus.ACCEPTED, "accepted"),
        (TicketStatus.DEFERRED, "deferred"),
        (TicketStatus.SCHEDULED, "scheduled"),
        (TicketStatus.ASSIGNED, "assigned"),
        (TicketStatus.READY_TO_WORK, "ready_to_work"),
        (TicketStatus.AT_WORK, "at_work"),
        (TicketStatus.PAUSED, "paused"),
        (TicketStatus.READY_FOR_REVIEW, "ready_for_review"),
        (TicketStatus.EXECUTED, "executed"),
        (TicketStatus.CANCELLED, "cancelled"),
    ],
)
def test_ticket_status_has_stable_value(
    status: TicketStatus,
    value: str,
) -> None:
    assert status.value == value


def test_expected_state_catalog_contains_all_ticket_statuses() -> None:
    assert set(EXPECTED_STATES) == set(TicketStatus)


# ----------------------------
# get_ticket_state()
# ----------------------------


@pytest.mark.parametrize("status", list(TicketStatus))
def test_get_ticket_state_returns_state_for_every_status(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.status == status


# ----------------------------
# State metadata
# ----------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    list(EXPECTED_STATES.items()),
)
def test_ticket_state_has_expected_metadata(
    status: TicketStatus,
    expected: ExpectedTicketState,
) -> None:
    state = get_ticket_state(status)

    assert state.terminal is expected.terminal
    assert state.requires_executor is expected.requires_executor
    assert state.requires_planned_start is expected.requires_planned_start
    assert state.work_started is expected.work_started
    assert state.locks_department_change is expected.locks_department_change
    assert (
        state.allows_ticket_text_update
        is expected.allows_ticket_text_update
    )


# ----------------------------
# Ticket text update policy
# ----------------------------


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
    ],
)
def test_created_and_accepted_allow_ticket_text_update(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.allows_ticket_text_update is True


@pytest.mark.parametrize(
    "status",
    [
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
def test_other_statuses_do_not_allow_ticket_text_update(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.allows_ticket_text_update is False


# ----------------------------
# Department change policy
# ----------------------------


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
    ],
)
def test_pre_assignment_statuses_do_not_lock_department_change(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.locks_department_change is False


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.AT_WORK,
        TicketStatus.PAUSED,
        TicketStatus.READY_FOR_REVIEW,
    ],
)
def test_assignment_and_work_statuses_lock_department_change(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.locks_department_change is True


# ----------------------------
# Work started
# ----------------------------


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.AT_WORK,
        TicketStatus.PAUSED,
        TicketStatus.READY_FOR_REVIEW,
    ],
)
def test_work_statuses_are_marked_as_work_started(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.work_started is True


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.CREATED,
        TicketStatus.REJECTED,
        TicketStatus.ACCEPTED,
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.EXECUTED,
        TicketStatus.CANCELLED,
    ],
)
def test_other_statuses_are_not_marked_as_work_started(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.work_started is False


# ----------------------------
# Allowed transition graph
# ----------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    list(EXPECTED_STATES.items()),
)
def test_ticket_state_has_expected_allowed_next_statuses(
    status: TicketStatus,
    expected: ExpectedTicketState,
) -> None:
    state = get_ticket_state(status)

    assert state.allowed_next == expected.allowed_next


@pytest.mark.parametrize(
    ("status", "expected"),
    list(EXPECTED_STATES.items()),
)
def test_ticket_state_allows_exactly_expected_transitions(
    status: TicketStatus,
    expected: ExpectedTicketState,
) -> None:
    state = get_ticket_state(status)

    for target_status in TicketStatus:
        assert state.allows_transition_to(target_status) is (
            target_status in expected.allowed_next
        )


# ----------------------------
# Terminal statuses
# ----------------------------


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.REJECTED,
        TicketStatus.EXECUTED,
        TicketStatus.CANCELLED,
    ],
)
def test_terminal_statuses_have_no_allowed_next_statuses(
    status: TicketStatus,
) -> None:
    state = get_ticket_state(status)

    assert state.terminal is True
    assert state.allowed_next == frozenset()

    for target_status in TicketStatus:
        assert state.allows_transition_to(target_status) is False
