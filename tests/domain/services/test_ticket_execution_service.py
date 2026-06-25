# tests/domain/services/test_ticket_execution_service.py

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_execution_service import (
    TicketExecutionService,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import (
    TicketStatusRecord,
)
from src.domain.ticket import Ticket


ADMIN_ID = 1
EXECUTOR_ID = 10
OTHER_EXECUTOR_ID = 20


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def make_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix customer issue",
    )


def accept_ticket(ticket: Ticket) -> None:
    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )
    )


def make_scheduled_ticket() -> Ticket:
    ticket = make_ticket()
    accept_ticket(ticket)

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.SCHEDULED,
            planned_start_at=now_utc() + timedelta(days=1),
        )
    )

    return ticket


def make_assigned_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_ticket()
    accept_ticket(ticket)

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
            planned_start_at=now_utc() + timedelta(days=1),
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
            actual_started_at=now_utc() - timedelta(minutes=30),
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
        )
    )

    return ticket


# ------------------------------------------------------------------
# take_to_work
# ------------------------------------------------------------------


def test_take_to_work_from_assigned() -> None:
    service = TicketExecutionService()
    ticket = make_assigned_ticket()

    record = service.take_to_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="Started investigation",
    )

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert record.status == TicketStatus.AT_WORK
    assert record.executor_id == EXECUTOR_ID
    assert record.actor_employee_id == EXECUTOR_ID
    assert record.actual_started_at is not None
    assert record.comment == "Started investigation"


def test_take_to_work_from_ready_to_work() -> None:
    service = TicketExecutionService()
    ticket = make_ready_to_work_ticket()

    record = service.take_to_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
    )

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at is not None


def test_take_to_work_rejects_non_executor() -> None:
    service = TicketExecutionService()
    ticket = make_assigned_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Only current executor",
    ):
        service.take_to_work(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED


def test_take_to_work_rejects_scheduled_ticket() -> None:
    service = TicketExecutionService()
    ticket = make_scheduled_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Cannot take ticket to work",
    ):
        service.take_to_work(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.SCHEDULED


# ------------------------------------------------------------------
# pause_work / resume_work
# ------------------------------------------------------------------


def test_pause_work() -> None:
    service = TicketExecutionService()
    ticket = make_at_work_ticket()

    record = service.pause_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="Waiting for access",
    )

    assert ticket.current_status() == TicketStatus.PAUSED
    assert record.status == TicketStatus.PAUSED
    assert record.executor_id == EXECUTOR_ID
    assert record.comment == "Waiting for access"


def test_pause_work_rejects_non_executor() -> None:
    service = TicketExecutionService()
    ticket = make_at_work_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Only current executor",
    ):
        service.pause_work(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


def test_pause_work_rejects_ticket_not_at_work() -> None:
    service = TicketExecutionService()
    ticket = make_assigned_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Cannot pause ticket work",
    ):
        service.pause_work(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED


def test_resume_work() -> None:
    service = TicketExecutionService()
    ticket = make_paused_ticket()

    record = service.resume_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="Access restored",
    )

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert record.status == TicketStatus.AT_WORK
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at is not None
    assert record.comment == "Access restored"


def test_resume_work_rejects_non_executor() -> None:
    service = TicketExecutionService()
    ticket = make_paused_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Only current executor",
    ):
        service.resume_work(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.PAUSED


# ------------------------------------------------------------------
# submit_for_review
# ------------------------------------------------------------------


def test_submit_for_review_from_at_work() -> None:
    service = TicketExecutionService()
    ticket = make_at_work_ticket()

    record = service.submit_for_review(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="Work completed",
    )

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.executor_id == EXECUTOR_ID

    # Начало уже есть в предыдущей записи AT_WORK.
    assert record.actual_started_at is None
    assert record.actual_finished_at is not None
    assert record.comment == "Work completed"


def test_submit_for_review_rejects_non_executor() -> None:
    service = TicketExecutionService()
    ticket = make_at_work_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Only current executor",
    ):
        service.submit_for_review(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


def test_submit_for_review_rejects_ticket_not_at_work() -> None:
    service = TicketExecutionService()
    ticket = make_paused_ticket()

    with pytest.raises(
        DomainOperationError,
        match="Cannot submit ticket for review",
    ):
        service.submit_for_review(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.PAUSED


# ------------------------------------------------------------------
# record_completed_work_for_review
# ------------------------------------------------------------------


def test_record_completed_work_for_review_from_scheduled() -> None:
    service = TicketExecutionService()
    ticket = make_scheduled_ticket()

    started_at = now_utc() - timedelta(hours=3)
    finished_at = now_utc() - timedelta(hours=1)

    record = service.record_completed_work_for_review(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        executor_id=EXECUTOR_ID,
        actual_started_at=started_at,
        actual_finished_at=finished_at,
        comment="Work was registered later",
    )

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.actor_employee_id == ADMIN_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at == started_at
    assert record.actual_finished_at == finished_at
    assert record.comment == "Work was registered later"


def test_record_completed_work_for_review_from_assigned() -> None:
    service = TicketExecutionService()
    ticket = make_assigned_ticket()

    started_at = now_utc() - timedelta(hours=2)
    finished_at = now_utc() - timedelta(minutes=30)

    record = service.record_completed_work_for_review(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        executor_id=EXECUTOR_ID,
        actual_started_at=started_at,
        actual_finished_at=finished_at,
    )

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at == started_at
    assert record.actual_finished_at == finished_at


def test_record_completed_work_for_review_from_ready_to_work() -> None:
    service = TicketExecutionService()
    ticket = make_ready_to_work_ticket()

    started_at = now_utc() - timedelta(hours=4)
    finished_at = now_utc() - timedelta(hours=2)

    record = service.record_completed_work_for_review(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        executor_id=EXECUTOR_ID,
        actual_started_at=started_at,
        actual_finished_at=finished_at,
    )

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.actual_started_at == started_at
    assert record.actual_finished_at == finished_at


def test_record_completed_work_rejects_at_work_ticket() -> None:
    service = TicketExecutionService()
    ticket = make_at_work_ticket()

    with pytest.raises(
            DomainOperationError,
            match=(
                    "Cannot record completed work for review "
                    "from at_work"
            ),
    ):
        service.record_completed_work_for_review(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
            executor_id=EXECUTOR_ID,
            actual_started_at=now_utc() - timedelta(hours=2),
            actual_finished_at=now_utc() - timedelta(hours=1),
        )
    assert ticket.current_status() == TicketStatus.AT_WORK


def test_record_completed_work_requires_executor() -> None:
    service = TicketExecutionService()
    ticket = make_scheduled_ticket()

    with pytest.raises(
        DomainOperationError,
        match="requires executor_id",
    ):
        service.record_completed_work_for_review(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            executor_id=0,
            actual_started_at=now_utc() - timedelta(hours=2),
            actual_finished_at=now_utc() - timedelta(hours=1),
        )

    assert ticket.current_status() == TicketStatus.SCHEDULED


def test_record_completed_work_requires_current_executor_match() -> None:
    service = TicketExecutionService()
    ticket = make_assigned_ticket(
        executor_id=EXECUTOR_ID,
    )

    with pytest.raises(
        DomainOperationError,
        match="must match the current ticket executor",
    ):
        service.record_completed_work_for_review(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
            executor_id=OTHER_EXECUTOR_ID,
            actual_started_at=now_utc() - timedelta(hours=2),
            actual_finished_at=now_utc() - timedelta(hours=1),
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID