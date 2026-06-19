# tests/domain/test_ticket.py

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory
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


def make_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
    )


def make_comment(
    *,
    employee_id: int = 10,
    text: str = "Some comment",
) -> Comment:
    return Comment(
        employee_id=employee_id,
        comment=text,
    )


# ----------------------------
# create()
# ----------------------------


def test_create_creates_ticket_with_created_status() -> None:
    ticket = make_ticket()

    assert ticket.ticket_id == 1
    assert ticket.client_id == 100
    assert ticket.admin_id == 10
    assert ticket.text_of_ticket == "Fix internet connection"

    assert len(ticket.statuses) == 1
    assert ticket.current_status() == TicketStatus.CREATED
    assert ticket.current_status_record().actor_employee_id == 10

    assert not ticket.is_closed
    assert ticket.date_finished is None


def test_create_strips_ticket_text() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="  Fix router  ",
    )

    assert ticket.text_of_ticket == "Fix router"


def test_create_rejects_empty_ticket_text() -> None:
    with pytest.raises(DomainOperationError):
        Ticket.create(
            ticket_id=1,
            client_id=100,
            admin_id=10,
            text_of_ticket="   ",
        )


def test_create_adds_initial_comment_if_comment_is_not_empty() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
        comment="  Created by phone  ",
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == 10
    assert ticket.comments[0].comment == "Created by phone"


def test_create_does_not_add_empty_initial_comment() -> None:
    ticket = Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
        comment="   ",
    )

    assert ticket.comments == []


# ----------------------------
# rehydrate()
# ----------------------------


def test_rehydrate_requires_status_history() -> None:
    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=1,
            client_id=100,
            admin_id=10,
            text_of_ticket="Fix internet connection",
            statuses=[],
            date_created=NOW,
        )


def test_rehydrate_restores_ticket_with_status_history() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=10,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=10,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=10,
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
            actor_employee_id=10,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=10,
            status=TicketStatus.REJECTED,
            date_created=PAST_4H,
            comment="invalid request",
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=10,
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
        TicketStatusRecordFactory.accepted(
            actor_employee_id=10,
        )
    )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_current_executor_id_returns_executor_from_current_status_record() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecordFactory.accepted(
            actor_employee_id=10,
        )
    )
    ticket.append_status(
        TicketStatusRecordFactory.assigned(
            actor_employee_id=10,
            executor_id=20,
        )
    )

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == 20
    assert ticket.has_executor()


def test_current_executor_id_does_not_use_old_executor_from_history() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecordFactory.accepted(
            actor_employee_id=10,
        )
    )
    ticket.append_status(
        TicketStatusRecordFactory.ready_to_work(
            actor_employee_id=10,
            executor_id=20,
            planned_start_at=FUTURE_1H,
        )
    )

    assert ticket.current_executor_id() == 20

    ticket.append_status(
        TicketStatusRecordFactory.scheduled(
            actor_employee_id=10,
            planned_start_at=FUTURE_2H,
        )
    )

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0
    assert not ticket.has_executor()


# ----------------------------
# append_status()
# ----------------------------


def test_append_status_allows_valid_transition() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecordFactory.accepted(
            actor_employee_id=10,
        )
    )

    assert len(ticket.statuses) == 2
    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_append_status_rejects_invalid_transition() -> None:
    ticket = make_ticket()

    with pytest.raises(DomainOperationError):
        ticket.append_status(
            TicketStatusRecordFactory.cancelled(
                actor_employee_id=10,
                comment="client cancelled",
            )
        )

    assert ticket.current_status() == TicketStatus.CREATED


def test_append_status_rejects_change_after_terminal_status() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecordFactory.rejected(
            actor_employee_id=10,
            comment="invalid request",
        )
    )

    assert ticket.is_terminal()

    with pytest.raises(DomainOperationError):
        ticket.append_status(
            TicketStatusRecordFactory.accepted(
                actor_employee_id=10,
            )
        )


def test_append_terminal_status_closes_ticket() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecordFactory.accepted(
            actor_employee_id=10,
        )
    )
    ticket.append_status(
        TicketStatusRecordFactory.cancelled(
            actor_employee_id=10,
            comment="client cancelled",
        )
    )

    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_closed
    assert ticket.date_finished == ticket.current_status_record().date_created


# ----------------------------
# comments
# ----------------------------


def test_add_comment_adds_plain_ticket_comment() -> None:
    ticket = make_ticket()

    ticket.add_comment(
        make_comment(
            employee_id=20,
            text="Need more details",
        )
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == 20
    assert ticket.comments[0].comment == "Need more details"


def test_add_comment_rejects_comment_after_terminal_status() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecordFactory.rejected(
            actor_employee_id=10,
            comment="invalid request",
        )
    )

    with pytest.raises(DomainOperationError):
        ticket.add_comment(
            make_comment(
                employee_id=20,
                text="Too late",
            )
        )


# ----------------------------
# new records
# ----------------------------


def test_new_statuses_returns_only_unsaved_statuses() -> None:
    saved_status = TicketStatusRecord(
        status_id=1,
        actor_employee_id=10,
        status=TicketStatus.CREATED,
        date_created=PAST_5H,
    )

    new_status = TicketStatusRecordFactory.accepted(
        actor_employee_id=10,
    )

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
        statuses=[saved_status, new_status],
        date_created=PAST_5H,
    )

    assert ticket.new_statuses() == [new_status]


def test_new_comments_returns_only_unsaved_comments() -> None:
    saved_comment = Comment(
        comment_id=1,
        employee_id=10,
        comment="Saved comment",
    )

    new_comment = Comment(
        employee_id=20,
        comment="New comment",
    )

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
        statuses=[
            TicketStatusRecord(
                status_id=1,
                actor_employee_id=10,
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


def test_working_time_counts_at_work_interval_until_next_status() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=10,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=10,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
        TicketStatusRecord(
            status_id=3,
            actor_employee_id=10,
            status=TicketStatus.ASSIGNED,
            executor_id=20,
            date_created=PAST_3H,
        ),
        TicketStatusRecord(
            status_id=4,
            actor_employee_id=20,
            status=TicketStatus.AT_WORK,
            executor_id=20,
            actual_started_at=PAST_2H,
            date_created=PAST_2H,
        ),
        TicketStatusRecord(
            status_id=5,
            actor_employee_id=20,
            status=TicketStatus.PAUSED,
            executor_id=20,
            date_created=PAST_1H,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.working_time() == 3600


def test_working_time_counts_offline_work_by_actual_times() -> None:
    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=10,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=10,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
        TicketStatusRecord(
            status_id=3,
            actor_employee_id=10,
            status=TicketStatus.ASSIGNED,
            executor_id=20,
            date_created=PAST_3H,
        ),
        TicketStatusRecord(
            status_id=4,
            actor_employee_id=20,
            status=TicketStatus.OFFLINE_WORK,
            executor_id=20,
            actual_started_at=PAST_2H,
            actual_finished_at=PAST_1H,
            date_created=NOW,
        ),
        TicketStatusRecord(
            status_id=5,
            actor_employee_id=20,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=20,
            actual_finished_at=PAST_1H,
            date_created=NOW,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.working_time() == 3600


def test_working_time_counts_at_work_current_status_until_now() -> None:
    started_at = datetime.now(timezone.utc) - timedelta(seconds=5)

    statuses = [
        TicketStatusRecord(
            status_id=1,
            actor_employee_id=10,
            status=TicketStatus.CREATED,
            date_created=PAST_5H,
        ),
        TicketStatusRecord(
            status_id=2,
            actor_employee_id=10,
            status=TicketStatus.ACCEPTED,
            date_created=PAST_4H,
        ),
        TicketStatusRecord(
            status_id=3,
            actor_employee_id=10,
            status=TicketStatus.ASSIGNED,
            executor_id=20,
            date_created=PAST_3H,
        ),
        TicketStatusRecord(
            status_id=4,
            actor_employee_id=20,
            status=TicketStatus.AT_WORK,
            executor_id=20,
            actual_started_at=started_at,
            date_created=started_at,
        ),
    ]

    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
        statuses=statuses,
        date_created=PAST_5H,
    )

    assert ticket.working_time() >= 5


# ----------------------------
# belong()
# ----------------------------


def test_belong_detects_admin_comment_actor_and_executor_references() -> None:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecordFactory.accepted(
            actor_employee_id=10,
        )
    )
    ticket.append_status(
        TicketStatusRecordFactory.assigned(
            actor_employee_id=10,
            executor_id=20,
        )
    )
    ticket.add_comment(
        make_comment(
            employee_id=30,
            text="Comment",
        )
    )

    assert ticket.belong(10)
    assert ticket.belong(20)
    assert ticket.belong(30)
    assert not ticket.belong(999)