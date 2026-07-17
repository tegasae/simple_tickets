# tests/domain/test_ticket.py

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment

NOW = datetime.now(timezone.utc)

PAST_5H = NOW - timedelta(hours=5)
PAST_4H = NOW - timedelta(hours=4)
PAST_3H = NOW - timedelta(hours=3)
PAST_2H = NOW - timedelta(hours=2)
PAST_1H = NOW - timedelta(hours=1)

FUTURE_1H = NOW + timedelta(hours=1)
FUTURE_2H = NOW + timedelta(hours=2)

ADMIN_ID = 10
EXECUTOR_ID = 20
OTHER_EXECUTOR_ID = 30


# ----------------------------
# Fixtures / helpers
# ----------------------------


def make_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
    )


def make_comment(
    *,
    employee_id: int = ADMIN_ID,
    text: str = "Some comment",
) -> Comment:
    return Comment(
        employee_id=employee_id,
        comment=text,
    )


def accept_ticket(ticket: Ticket) -> Ticket:
    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )
    )
    return ticket


def make_accepted_ticket() -> Ticket:
    return accept_ticket(make_ticket())


def make_deferred_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.DEFERRED,
            comment="Waiting for additional information",
        )
    )

    return ticket


def make_scheduled_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.SCHEDULED,
            planned_start_at=FUTURE_1H,
        )
    )

    return ticket


def make_assigned_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ASSIGNED,
            executor_id=executor_id,
        )
    )

    return ticket


def make_ready_to_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.READY_TO_WORK,
            executor_id=executor_id,
            planned_start_at=FUTURE_1H,
        )
    )

    return ticket


def make_at_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.AT_WORK,
            executor_id=executor_id,
            actual_started_at=PAST_2H,
            date_created=PAST_2H,
        )
    )

    return ticket


def make_paused_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_at_work_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.PAUSED,
            executor_id=executor_id,
            date_created=PAST_1H,
        )
    )

    return ticket


def make_ready_for_review_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_at_work_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=executor_id,
            actual_finished_at=PAST_1H,
            date_created=PAST_1H,
        )
    )

    return ticket


def make_rejected_ticket() -> Ticket:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.REJECTED,
            comment="Invalid request",
        )
    )

    return ticket


def make_executed_ticket() -> Ticket:
    ticket = make_ready_for_review_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.EXECUTED,
        )
    )

    return ticket


def make_cancelled_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CANCELLED,
            comment="Client cancelled request",
        )
    )

    return ticket


# ----------------------------
# create()
# ----------------------------


def test_create_creates_ticket_with_created_status() -> None:
    ticket = make_ticket()

    assert ticket.ticket_id == 1
    assert ticket.client_id == 100
    assert ticket.admin_id == ADMIN_ID
    assert ticket.text_of_ticket == "Fix internet connection"

    assert len(ticket.statuses) == 1
    assert ticket.current_status() == TicketStatus.CREATED
    assert ticket.current_status_record().actor_employee_id == ADMIN_ID

    assert not ticket.is_closed
    assert ticket.date_finished is None


def test_create_strips_ticket_text() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="  Fix router  ",
    )

    assert ticket.text_of_ticket == "Fix router"


def test_create_rejects_empty_ticket_text() -> None:
    with pytest.raises(DomainOperationError):
        Ticket.create(
            ticket_id=1,
            client_id=100,
            admin_id=ADMIN_ID,
            text_of_ticket="   ",
        )


def test_create_adds_initial_comment_if_not_empty() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        comment="  Created by phone  ",
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == ADMIN_ID
    assert ticket.comments[0].comment == "Created by phone"


def test_create_does_not_add_empty_initial_comment() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        comment="   ",
    )

    assert ticket.comments == []


# ----------------------------
# rehydrate()
# ----------------------------


def test_rehydrate_requires_status_history() -> None:
    with pytest.raises(
        DomainOperationError,
        match="without status history",
    ):
        Ticket.rehydrate(
            ticket_id=1,
            client_id=100,
            admin_id=ADMIN_ID,
            text_of_ticket="Fix internet connection",
            statuses=[],
            date_created=NOW,
        )


def test_rehydrate_restores_ticket_with_status_history() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
        version=3,
    )

    assert ticket.ticket_id == 1
    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.version == 3
    assert not ticket.is_closed
    assert ticket.date_finished is None


def test_rehydrate_recomputes_terminal_state() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.REJECTED,
            date_created=PAST_4H,
            comment="Invalid request",
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.is_closed
    assert ticket.date_finished == PAST_4H


# ----------------------------
# current status / executor
# ----------------------------


def test_current_status_returns_last_status() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )
    )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_current_executor_id_returns_executor_from_current_record() -> None:
    ticket = make_assigned_ticket()

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID
    assert ticket.has_executor()


def test_current_executor_id_does_not_use_old_executor_from_history() -> None:
    ticket = make_ready_to_work_ticket()

    assert ticket.current_executor_id() == EXECUTOR_ID

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.SCHEDULED,
            planned_start_at=FUTURE_2H,
        )
    )

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0
    assert not ticket.has_executor()


# ----------------------------
# can_change_status()
# ----------------------------


def test_can_change_status_returns_true_for_valid_transition() -> None:
    ticket = make_ticket()

    assert ticket.can_change_status(TicketStatus.ACCEPTED)
    assert ticket.can_change_status(TicketStatus.REJECTED)


def test_can_change_status_returns_false_for_invalid_transition() -> None:
    ticket = make_ticket()

    assert not ticket.can_change_status(TicketStatus.AT_WORK)
    assert not ticket.can_change_status(TicketStatus.CANCELLED)


def test_can_change_status_returns_false_for_terminal_ticket() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.REJECTED,
            comment="Invalid request",
        )
    )

    assert not ticket.can_change_status(TicketStatus.ACCEPTED)


# ----------------------------
# append_status()
# ----------------------------


def test_append_status_allows_valid_transition() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )
    )

    assert len(ticket.statuses) == 2
    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_append_status_rejects_invalid_transition() -> None:
    ticket = make_ticket()

    with pytest.raises(
        DomainOperationError,
        match="transition is not allowed",
    ):
        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.CANCELLED,
                comment="Client cancelled",
            )
        )

    assert ticket.current_status() == TicketStatus.CREATED


def test_append_status_rejects_change_after_terminal_status() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.REJECTED,
            comment="Invalid request",
        )
    )

    assert ticket.is_terminal()

    with pytest.raises(
        DomainOperationError,
        match="terminal status",
    ):
        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.ACCEPTED,
            )
        )


def test_append_terminal_status_closes_ticket() -> None:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CANCELLED,
            comment="Client cancelled",
        )
    )

    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_closed
    assert ticket.date_finished == ticket.current_status_record().date_created


# ----------------------------
# READY_FOR_REVIEW transitions
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
    ],
)
def test_retroactive_work_can_be_registered_for_review(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=EXECUTOR_ID,
            actual_started_at=PAST_2H,
            actual_finished_at=PAST_1H,
            comment="Work registered later",
        )
    )

    record = ticket.current_status_record()

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at == PAST_2H
    assert record.actual_finished_at == PAST_1H


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
    ],
)
def test_retroactive_work_requires_actual_started_at(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    with pytest.raises(
        DomainOperationError,
        match="Retrospective work registration requires",
    ):
        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.READY_FOR_REVIEW,
                executor_id=EXECUTOR_ID,
                actual_finished_at=PAST_1H,
            )
        )

    assert ticket.current_status() != TicketStatus.READY_FOR_REVIEW


def test_at_work_to_review_is_allowed_without_actual_started_at() -> None:
    ticket = make_at_work_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=EXECUTOR_ID,
            actual_finished_at=PAST_1H,
        )
    )

    record = ticket.current_status_record()

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert record.actual_started_at is None
    assert record.actual_finished_at == PAST_1H


def test_at_work_to_review_rejects_new_actual_started_at() -> None:
    ticket = make_at_work_ticket()

    with pytest.raises(
        DomainOperationError,
        match="must not provide actual_started_at",
    ):
        ticket.append_status(
            TicketStatusRecord(
                actor_employee_id=EXECUTOR_ID,
                status=TicketStatus.READY_FOR_REVIEW,
                executor_id=EXECUTOR_ID,
                actual_started_at=PAST_2H,
                actual_finished_at=PAST_1H,
            )
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


# ----------------------------
# comments
# ----------------------------


def test_add_comment_adds_plain_ticket_comment() -> None:
    ticket = make_ticket()

    ticket.add_comment(
        make_comment(
            employee_id=EXECUTOR_ID,
            text="Need more details",
        )
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == EXECUTOR_ID
    assert ticket.comments[0].comment == "Need more details"


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_rejected_ticket,
        make_executed_ticket,
        make_cancelled_ticket,
    ],
    ids=[
        "rejected",
        "executed",
        "cancelled",
    ],
)
def test_add_comment_is_allowed_after_terminal_status(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    ticket.add_comment(
        make_comment(
            employee_id=ADMIN_ID,
            text="Administrative note after closure.",
        )
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].comment == "Administrative note after closure."
# ----------------------------
# department
# ----------------------------


def test_change_department_is_allowed_before_executor_assignment() -> None:
    ticket = make_scheduled_ticket()

    ticket.change_department(department_id=5)

    assert ticket.department_id == 5


def test_change_department_is_rejected_after_executor_assignment() -> None:
    ticket = make_assigned_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Cannot change ticket department",
    ):
        ticket.change_department(department_id=5)


# ----------------------------
# ticket text
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_ticket,
        make_accepted_ticket,
    ],
    ids=[
        "created",
        "accepted",
    ],
)
def test_update_ticket_text_is_allowed_only_in_created_and_accepted(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    ticket.update_ticket_text(
        text_of_ticket="Fix VPN connection",
    )

    assert ticket.text_of_ticket == "Fix VPN connection"


def test_update_ticket_text_strips_new_text() -> None:
    ticket = make_ticket()

    ticket.update_ticket_text(
        text_of_ticket="  Fix VPN connection  ",
    )

    assert ticket.text_of_ticket == "Fix VPN connection"


def test_update_ticket_text_rejects_empty_text() -> None:
    ticket = make_ticket()
    original_text = ticket.text_of_ticket

    with pytest.raises(DomainOperationError):
        ticket.update_ticket_text(
            text_of_ticket="   ",
        )

    assert ticket.text_of_ticket == original_text


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_rejected_ticket,
        make_deferred_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
        make_executed_ticket,
        make_cancelled_ticket,
    ],
    ids=[
        "rejected",
        "deferred",
        "scheduled",
        "assigned",
        "ready_to_work",
        "at_work",
        "paused",
        "ready_for_review",
        "executed",
        "cancelled",
    ],
)
def test_update_ticket_text_is_rejected_in_other_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()
    original_text = ticket.text_of_ticket

    with pytest.raises(DomainOperationError):
        ticket.update_ticket_text(
            text_of_ticket="Fix VPN connection",
        )

    assert ticket.text_of_ticket == original_text


# ----------------------------
# description
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_ticket,
        make_accepted_ticket,
        make_deferred_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
    ],
    ids=[
        "created",
        "accepted",
        "deferred",
        "scheduled",
        "assigned",
        "ready_to_work",
        "at_work",
        "paused",
        "ready_for_review",
    ],
)
def test_update_description_is_allowed_in_all_non_terminal_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    ticket.update_description(
        description=(
            "Room 305. Enter through the north entrance. "
            "Call the contact before arrival."
        ),
    )

    assert ticket.description == (
        "Room 305. Enter through the north entrance. "
        "Call the contact before arrival."
    )


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_rejected_ticket,
        make_executed_ticket,
        make_cancelled_ticket,
    ],
    ids=[
        "rejected",
        "executed",
        "cancelled",
    ],
)
def test_update_description_is_rejected_for_terminal_ticket(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()
    original_description = ticket.description

    with pytest.raises(DomainOperationError):
        ticket.update_description(
            description="New access instructions",
        )

    assert ticket.description == original_description


# ----------------------------
# new records
# ----------------------------


def test_new_statuses_returns_only_unsaved_statuses() -> None:
    saved_status = TicketStatusRecord(
        status_id=1,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.CREATED,
        date_created=PAST_5H,
    )

    new_status = TicketStatusRecord(
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.ACCEPTED,
    )

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=[saved_status, new_status],
        date_created=PAST_5H,
    )

    assert ticket.new_statuses() == [new_status]


def test_new_comments_returns_only_unsaved_comments() -> None:
    saved_comment = Comment(
        comment_id=1,
        employee_id=ADMIN_ID,
        comment="Saved comment",
    )

    new_comment = Comment(
        employee_id=EXECUTOR_ID,
        comment="New comment",
    )

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=[
            TicketStatusRecord(
                status_id=1,
                actor_employee_id=ADMIN_ID,
                status=TicketStatus.CREATED,
                date_created=PAST_5H,
            )
        ],
        comments=[saved_comment, new_comment],
        date_created=PAST_5H,
    )

    assert ticket.new_comments() == [new_comment]


# ----------------------------
# working_time()
# ----------------------------


def test_working_time_counts_at_work_until_next_status() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
        TicketStatusRecord(
            status_id=3,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ASSIGNED,
            executor_id=EXECUTOR_ID,
            date_created=PAST_3H,
        ),
        TicketStatusRecord(
            status_id=4,
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.AT_WORK,
            executor_id=EXECUTOR_ID,
            actual_started_at=PAST_2H,
            date_created=PAST_2H,
        ),
        TicketStatusRecord(
            status_id=5,
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.PAUSED,
            executor_id=EXECUTOR_ID,
            date_created=PAST_1H,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.working_time() == 3600


def test_working_time_counts_retroactive_work_by_actual_times() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
        TicketStatusRecord(
            status_id=3,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ASSIGNED,
            executor_id=EXECUTOR_ID,
            date_created=PAST_3H,
        ),
        TicketStatusRecord(
            status_id=4,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=EXECUTOR_ID,
            actual_started_at=PAST_2H,
            actual_finished_at=PAST_1H,
            date_created=NOW,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.working_time() == 3600


def test_working_time_counts_online_work_until_review() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
        TicketStatusRecord(
            status_id=3,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ASSIGNED,
            executor_id=EXECUTOR_ID,
            date_created=PAST_3H,
        ),
        TicketStatusRecord(
            status_id=4,
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.AT_WORK,
            executor_id=EXECUTOR_ID,
            actual_started_at=PAST_2H,
            date_created=PAST_2H,
        ),
        TicketStatusRecord(
            status_id=5,
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=EXECUTOR_ID,
            actual_finished_at=PAST_1H,
            date_created=PAST_1H,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.working_time() == 3600


def test_working_time_counts_current_at_work_until_now() -> None:
    started_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
        TicketStatusRecord(
            status_id=3,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ASSIGNED,
            executor_id=EXECUTOR_ID,
            date_created=PAST_3H,
        ),
        TicketStatusRecord(
            status_id=4,
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.AT_WORK,
            executor_id=EXECUTOR_ID,
            actual_started_at=started_at,
            date_created=started_at,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.working_time() >= 10


# ----------------------------
# belong()
# ----------------------------


def test_belong_detects_admin_comment_actor_and_executor_references() -> None:
    ticket = make_assigned_ticket()

    ticket.add_comment(
        make_comment(
            employee_id=OTHER_EXECUTOR_ID,
            text="Comment",
        )
    )

    assert ticket.belong(ADMIN_ID)
    assert ticket.belong(EXECUTOR_ID)
    assert ticket.belong(OTHER_EXECUTOR_ID)
    assert not ticket.belong(999)