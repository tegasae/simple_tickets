# tests/domain/test_ticket.py

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment


BASE_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

PAST_5H = BASE_TIME - timedelta(hours=5)
PAST_4H = BASE_TIME - timedelta(hours=4)
PAST_3H = BASE_TIME - timedelta(hours=3)
PAST_2H = BASE_TIME - timedelta(hours=2)
PAST_1H = BASE_TIME - timedelta(hours=1)

FUTURE_1H = BASE_TIME + timedelta(hours=1)
FUTURE_2H = BASE_TIME + timedelta(hours=2)

ADMIN_ID = 10
EXECUTOR_ID = 20
OTHER_EXECUTOR_ID = 30

CLIENT_ID = 100
USER_ID = 200
CONTACT_USER_ID = 201
USER_TICKET_ID = 300


# ----------------------------
# Fixtures / helpers
# ----------------------------


def make_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        date_created=BASE_TIME,
    )


def make_ticket_from_ticket_user() -> Ticket:
    return Ticket.create_from_ticket_user(
        ticket_id=1,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Fix internet connection",
        user_ticket_id=USER_TICKET_ID,
        date_created=BASE_TIME,
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


def append_status(
    ticket: Ticket,
    *,
    actor_employee_id: int,
    status: TicketStatus,
    executor_id: int = 0,
    planned_start_at: datetime | None = None,
    planned_finish_at: datetime | None = None,
    actual_started_at: datetime | None = None,
    actual_finished_at: datetime | None = None,
    comment: str = "",
    date_created: datetime | None = None,
) -> TicketStatusRecord:
    record = TicketStatusRecord(
        actor_employee_id=actor_employee_id,
        status=status,
        executor_id=executor_id,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        actual_started_at=actual_started_at,
        actual_finished_at=actual_finished_at,
        comment=comment,
        date_created=date_created or BASE_TIME,
    )

    ticket.append_status(record)

    return record


def accept_ticket(ticket: Ticket) -> Ticket:
    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.ACCEPTED,
        date_created=PAST_4H,
    )
    return ticket


def make_accepted_ticket() -> Ticket:
    return accept_ticket(make_ticket())


def make_scheduled_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.SCHEDULED,
        planned_start_at=FUTURE_1H,
        date_created=PAST_3H,
    )

    return ticket


def make_assigned_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_accepted_ticket()

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.ASSIGNED,
        executor_id=executor_id,
        date_created=PAST_3H,
    )

    return ticket


def make_ready_to_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(
        executor_id=executor_id,
    )

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.READY_TO_WORK,
        executor_id=executor_id,
        planned_start_at=FUTURE_1H,
        date_created=PAST_2H,
    )

    return ticket


def make_at_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(
        executor_id=executor_id,
    )

    append_status(
        ticket,
        actor_employee_id=executor_id,
        status=TicketStatus.AT_WORK,
        executor_id=executor_id,
        actual_started_at=PAST_2H,
        date_created=PAST_2H,
    )

    return ticket


def make_paused_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_at_work_ticket(
        executor_id=executor_id,
    )

    append_status(
        ticket,
        actor_employee_id=executor_id,
        status=TicketStatus.PAUSED,
        executor_id=executor_id,
        comment="Paused",
        date_created=PAST_1H,
    )

    return ticket


# ----------------------------
# create()
# ----------------------------


def test_create_creates_ticket_with_created_status() -> None:
    ticket = make_ticket()

    assert ticket.ticket_id == 1
    assert ticket.client_id == CLIENT_ID
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
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="  Fix router  ",
        date_created=BASE_TIME,
    )

    assert ticket.text_of_ticket == "Fix router"


def test_create_rejects_empty_ticket_text() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create(
            ticket_id=1,
            client_id=CLIENT_ID,
            admin_id=ADMIN_ID,
            text_of_ticket="   ",
            date_created=BASE_TIME,
        )


@pytest.mark.parametrize(
    "ticket_id, client_id, admin_id",
    [
        (0, CLIENT_ID, ADMIN_ID),
        (1, 0, ADMIN_ID),
        (1, CLIENT_ID, 0),
    ],
)
def test_create_rejects_invalid_required_ids(
    ticket_id: int,
    client_id: int,
    admin_id: int,
) -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create(
            ticket_id=ticket_id,
            client_id=client_id,
            admin_id=admin_id,
            text_of_ticket="Fix internet connection",
            date_created=BASE_TIME,
        )


def test_create_adds_initial_comment_if_not_empty() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        comment="  Created by phone  ",
        date_created=BASE_TIME,
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == ADMIN_ID
    assert ticket.comments[0].comment == "Created by phone"


def test_create_does_not_add_empty_initial_comment() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        comment="   ",
        date_created=BASE_TIME,
    )

    assert ticket.comments == []


# ----------------------------
# create_from_ticket_user()
# ----------------------------


def test_create_from_ticket_user_creates_user_driven_ticket() -> None:
    ticket = make_ticket_from_ticket_user()

    assert ticket.ticket_id == 1
    assert ticket.client_id == CLIENT_ID
    assert ticket.admin_id == 0
    assert ticket.user_id == USER_ID
    assert ticket.contact_user_id == CONTACT_USER_ID
    assert ticket.user_ticket_id == USER_TICKET_ID

    assert ticket.current_status() == TicketStatus.CREATED_FROM_TICKET_USER
    assert ticket.current_status_record().actor_employee_id == 0

    assert not ticket.is_closed
    assert ticket.date_finished is None


def test_create_from_ticket_user_rejects_invalid_user_id() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create_from_ticket_user(
            ticket_id=1,
            client_id=CLIENT_ID,
            user_id=0,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Fix internet connection",
            user_ticket_id=USER_TICKET_ID,
            date_created=BASE_TIME,
        )


def test_create_from_ticket_user_rejects_invalid_user_ticket_id() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create_from_ticket_user(
            ticket_id=1,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Fix internet connection",
            user_ticket_id=0,
            date_created=BASE_TIME,
        )


def test_created_from_ticket_user_accept_sets_admin_id() -> None:
    ticket = make_ticket_from_ticket_user()

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.ACCEPTED,
    )

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.admin_id == ADMIN_ID


def test_created_from_ticket_user_can_be_cancelled_by_user_marker() -> None:
    ticket = make_ticket_from_ticket_user()

    record = append_status(
        ticket,
        actor_employee_id=0,
        status=TicketStatus.CANCELLED_BY_USER,
    )

    assert ticket.current_status() == TicketStatus.CANCELLED_BY_USER
    assert ticket.current_status_record().actor_employee_id == 0
    assert ticket.is_closed
    assert ticket.date_finished == record.date_created


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
            client_id=CLIENT_ID,
            admin_id=ADMIN_ID,
            text_of_ticket="Fix internet connection",
            statuses=[],
            date_created=BASE_TIME,
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
        client_id=CLIENT_ID,
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
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.is_closed
    assert ticket.date_finished == PAST_4H


def test_rehydrate_user_driven_ticket_accept_keeps_admin_id() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=0,
            status=TicketStatus.CREATED_FROM_TICKET_USER,
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
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=USER_TICKET_ID,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.admin_id == ADMIN_ID
    assert ticket.user_ticket_id == USER_TICKET_ID


# ----------------------------
# current status / executor
# ----------------------------


def test_current_status_returns_last_status() -> None:
    ticket = make_ticket()

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.ACCEPTED,
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

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.SCHEDULED,
        planned_start_at=FUTURE_2H,
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

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.REJECTED,
        comment="Invalid request",
    )

    assert not ticket.can_change_status(TicketStatus.ACCEPTED)


# ----------------------------
# append_status()
# ----------------------------


def test_append_status_allows_valid_transition() -> None:
    ticket = make_ticket()

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.ACCEPTED,
    )

    assert len(ticket.statuses) == 2
    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_append_status_rejects_invalid_transition() -> None:
    ticket = make_ticket()

    with pytest.raises(
        DomainOperationError,
        match="transition is not allowed",
    ):
        append_status(
            ticket,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CANCELLED,
            comment="Client cancelled",
        )

    assert ticket.current_status() == TicketStatus.CREATED


def test_append_status_rejects_change_after_terminal_status() -> None:
    ticket = make_ticket()

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.REJECTED,
        comment="Invalid request",
    )

    assert ticket.is_terminal()

    with pytest.raises(
        DomainOperationError,
        match="terminal status",
    ):
        append_status(
            ticket,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )


def test_append_terminal_status_closes_ticket() -> None:
    ticket = make_accepted_ticket()

    record = append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.CANCELLED,
        comment="Client cancelled",
    )

    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_closed
    assert ticket.date_finished == record.date_created


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

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.READY_FOR_REVIEW,
        executor_id=EXECUTOR_ID,
        actual_started_at=PAST_2H,
        actual_finished_at=PAST_1H,
        comment="Work registered later",
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
        append_status(
            ticket,
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=EXECUTOR_ID,
            actual_finished_at=PAST_1H,
        )

    assert ticket.current_status() != TicketStatus.READY_FOR_REVIEW


def test_at_work_to_review_is_allowed_without_actual_started_at() -> None:
    ticket = make_at_work_ticket()

    append_status(
        ticket,
        actor_employee_id=EXECUTOR_ID,
        status=TicketStatus.READY_FOR_REVIEW,
        executor_id=EXECUTOR_ID,
        actual_finished_at=PAST_1H,
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
        append_status(
            ticket,
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=EXECUTOR_ID,
            actual_started_at=PAST_2H,
            actual_finished_at=PAST_1H,
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


def test_add_comment_rejects_comment_after_terminal_status() -> None:
    ticket = make_ticket()

    append_status(
        ticket,
        actor_employee_id=ADMIN_ID,
        status=TicketStatus.REJECTED,
        comment="Invalid request",
    )

    with pytest.raises(
        DomainOperationError,
        match="terminal status",
    ):
        ticket.add_comment(
            make_comment(
                employee_id=EXECUTOR_ID,
                text="Too late",
            )
        )


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
        date_created=PAST_4H,
    )

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=CLIENT_ID,
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
        client_id=CLIENT_ID,
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
        client_id=CLIENT_ID,
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
            date_created=BASE_TIME,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=CLIENT_ID,
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
        client_id=CLIENT_ID,
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
        client_id=CLIENT_ID,
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



def test_belong_ignores_zero_actor_marker() -> None:
    ticket = make_ticket_from_ticket_user()

    append_status(
        ticket,
        actor_employee_id=0,
        status=TicketStatus.CANCELLED_BY_USER,
    )

    assert not ticket.belong(0)
    assert not ticket.belong(-1)


