# tests/domain/services/test_ticket_service_executor.py

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_execution_service import TicketExecutionService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


NOW = datetime.now(timezone.utc)

PAST_START = NOW - timedelta(hours=2)
PAST_FINISH = NOW - timedelta(hours=1)

FUTURE_START = NOW + timedelta(hours=1)
FUTURE_FINISH = NOW + timedelta(hours=2)


def make_created_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
    )


def make_accepted_ticket() -> Ticket:
    ticket = make_created_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.ACCEPTED,
        )
    )

    return ticket


def make_assigned_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.ASSIGNED,
            executor_id=executor_id,
        )
    )

    return ticket


def make_ready_to_work_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.READY_TO_WORK,
            executor_id=executor_id,
            planned_start_at=FUTURE_START,
            planned_finish_at=FUTURE_FINISH,
        )
    )

    return ticket


def make_at_work_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_assigned_ticket(executor_id=executor_id)

    TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=executor_id,
    )

    return ticket


def make_paused_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_at_work_ticket(executor_id=executor_id)

    TicketExecutionService.pause_work(
        ticket=ticket,
        actor_employee_id=executor_id,
        comment="temporary pause",
    )

    return ticket


def make_offline_work_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_assigned_ticket(executor_id=executor_id)

    TicketExecutionService.register_offline_work(
        ticket=ticket,
        actor_employee_id=executor_id,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
        comment="worked offline",
    )

    return ticket


# ----------------------------
# take_to_work()
# ----------------------------


def test_take_to_work_from_assigned() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    record = TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=20,
        comment="start work",
    )

    assert record.status == TicketStatus.AT_WORK
    assert record.actor_employee_id == 20
    assert record.executor_id == 20
    assert record.actual_started_at is not None
    assert record.comment == "start work"

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == 20


def test_take_to_work_from_ready_to_work() -> None:
    ticket = make_ready_to_work_ticket(executor_id=20)

    record = TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=20,
    )

    assert record.status == TicketStatus.AT_WORK
    assert record.executor_id == 20

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == 20


def test_take_to_work_rejects_actor_who_is_not_current_executor() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.take_to_work(
            ticket=ticket,
            actor_employee_id=999,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == 20


def test_take_to_work_rejects_ticket_without_executor() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(DomainOperationError):
        TicketExecutionService.take_to_work(
            ticket=ticket,
            actor_employee_id=20,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.current_executor_id() == 0


def test_take_to_work_rejects_scheduled_ticket_without_executor() -> None:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=10,
            status=TicketStatus.SCHEDULED,
            planned_start_at=FUTURE_START,
        )
    )

    with pytest.raises(DomainOperationError):
        TicketExecutionService.take_to_work(
            ticket=ticket,
            actor_employee_id=20,
        )

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


# ----------------------------
# pause_work()
# ----------------------------


def test_pause_work_from_at_work() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    record = TicketExecutionService.pause_work(
        ticket=ticket,
        actor_employee_id=20,
        comment="waiting for access",
    )

    assert record.status == TicketStatus.PAUSED
    assert record.actor_employee_id == 20
    assert record.executor_id == 20
    assert record.comment == "waiting for access"

    assert ticket.current_status() == TicketStatus.PAUSED
    assert ticket.current_executor_id() == 20


def test_pause_work_rejects_actor_who_is_not_current_executor() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.pause_work(
            ticket=ticket,
            actor_employee_id=999,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == 20


def test_pause_work_rejects_when_ticket_is_not_at_work() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.pause_work(
            ticket=ticket,
            actor_employee_id=20,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED


# ----------------------------
# resume_work()
# ----------------------------


def test_resume_work_from_paused() -> None:
    ticket = make_paused_ticket(executor_id=20)

    record = TicketExecutionService.resume_work(
        ticket=ticket,
        actor_employee_id=20,
        comment="resume work",
    )

    assert record.status == TicketStatus.AT_WORK
    assert record.actor_employee_id == 20
    assert record.executor_id == 20
    assert record.actual_started_at is not None
    assert record.comment == "resume work"

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == 20


def test_resume_work_rejects_actor_who_is_not_current_executor() -> None:
    ticket = make_paused_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.resume_work(
            ticket=ticket,
            actor_employee_id=999,
        )

    assert ticket.current_status() == TicketStatus.PAUSED
    assert ticket.current_executor_id() == 20


def test_resume_work_rejects_when_ticket_is_not_paused() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.resume_work(
            ticket=ticket,
            actor_employee_id=20,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


# ----------------------------
# register_offline_work()
# ----------------------------


def test_register_offline_work_from_assigned() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    record = TicketExecutionService.register_offline_work(
        ticket=ticket,
        actor_employee_id=20,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
        comment="worked offline",
    )

    assert record.status == TicketStatus.OFFLINE_WORK
    assert record.actor_employee_id == 20
    assert record.executor_id == 20
    assert record.actual_started_at == PAST_START
    assert record.actual_finished_at == PAST_FINISH
    assert record.comment == "worked offline"

    assert ticket.current_status() == TicketStatus.OFFLINE_WORK
    assert ticket.current_executor_id() == 20


def test_register_offline_work_from_ready_to_work() -> None:
    ticket = make_ready_to_work_ticket(executor_id=20)

    record = TicketExecutionService.register_offline_work(
        ticket=ticket,
        actor_employee_id=20,
        actual_started_at=PAST_START,
        actual_finished_at=PAST_FINISH,
    )

    assert record.status == TicketStatus.OFFLINE_WORK
    assert record.executor_id == 20
    assert record.actual_started_at == PAST_START
    assert record.actual_finished_at == PAST_FINISH

    assert ticket.current_status() == TicketStatus.OFFLINE_WORK
    assert ticket.current_executor_id() == 20


def test_register_offline_work_rejects_actor_who_is_not_current_executor() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.register_offline_work(
            ticket=ticket,
            actor_employee_id=999,
            actual_started_at=PAST_START,
            actual_finished_at=PAST_FINISH,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED


def test_register_offline_work_rejects_when_ticket_has_no_executor() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(DomainOperationError):
        TicketExecutionService.register_offline_work(
            ticket=ticket,
            actor_employee_id=20,
            actual_started_at=PAST_START,
            actual_finished_at=PAST_FINISH,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_register_offline_work_rejects_when_transition_is_not_allowed() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.register_offline_work(
            ticket=ticket,
            actor_employee_id=20,
            actual_started_at=PAST_START,
            actual_finished_at=PAST_FINISH,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


# ----------------------------
# submit_for_review()
# ----------------------------


def test_submit_for_review_from_at_work() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    before = datetime.now(timezone.utc)

    record = TicketExecutionService.submit_for_review(
        ticket=ticket,
        actor_employee_id=20,
        comment="done",
    )

    after = datetime.now(timezone.utc)

    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.actor_employee_id == 20
    assert record.executor_id == 20
    assert record.actual_finished_at is not None
    assert before <= record.actual_finished_at <= after
    assert record.comment == "done"

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == 20


def test_submit_for_review_from_offline_work_keeps_offline_actual_finish() -> None:
    ticket = make_offline_work_ticket(executor_id=20)

    record = TicketExecutionService.submit_for_review(
        ticket=ticket,
        actor_employee_id=20,
        comment="offline work done",
    )

    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.actor_employee_id == 20
    assert record.executor_id == 20
    assert record.actual_finished_at == PAST_FINISH
    assert record.comment == "offline work done"

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == 20


def test_submit_for_review_rejects_actor_who_is_not_current_executor() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.submit_for_review(
            ticket=ticket,
            actor_employee_id=999,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


def test_submit_for_review_rejects_when_ticket_is_not_at_work_or_offline_work() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.submit_for_review(
            ticket=ticket,
            actor_employee_id=20,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED