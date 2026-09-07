from __future__ import annotations

import pytest

from src.domain.statuses.ticket_status import TicketStatus, _validate_ticket_states

pytestmark = pytest.mark.unit


def test_every_ticket_status_has_matching_state() -> None:
    for status in TicketStatus:
        assert status.state.status is status
    _validate_ticket_states()


@pytest.mark.parametrize(
    "status",
    [
        TicketStatus.REJECTED,
        TicketStatus.EXECUTED,
        TicketStatus.CANCELLED,
        TicketStatus.CANCELLED_BY_USER,
    ],
)
def test_terminal_states_have_no_outgoing_transitions(status: TicketStatus) -> None:
    assert status.state.terminal
    assert status.state.allowed_next == frozenset()


def test_only_initial_statuses_are_first_statuses() -> None:
    first = {status for status in TicketStatus if status.state.first_status}
    assert first == {
        TicketStatus.CREATED,
        TicketStatus.CREATED_FROM_TICKET_USER,
    }


def test_execution_capabilities_match_expected_states() -> None:
    assert TicketStatus.ASSIGNED.state.can_take_to_work
    assert TicketStatus.READY_TO_WORK.state.can_take_to_work
    assert TicketStatus.AT_WORK.state.can_pause_work
    assert TicketStatus.AT_WORK.state.can_submit_for_review
    assert TicketStatus.PAUSED.state.can_resume_work
    assert TicketStatus.READY_FOR_REVIEW.state.can_review_result


def test_retroactive_work_is_allowed_only_from_management_states() -> None:
    allowed = {
        status
        for status in TicketStatus
        if status.state.can_record_completed_work
    }
    assert allowed == {
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
    }


def test_known_transition_graph_examples() -> None:
    assert TicketStatus.CREATED.state.allows_transition_to(TicketStatus.ACCEPTED)
    assert not TicketStatus.CREATED.state.allows_transition_to(TicketStatus.AT_WORK)
    assert TicketStatus.CREATED_FROM_TICKET_USER.state.allows_transition_to(TicketStatus.CANCELLED_BY_USER)
    assert TicketStatus.READY_FOR_REVIEW.state.allows_transition_to(TicketStatus.EXECUTED)
