from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.department import Department
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.services.admin_department_service import AdminDepartmentService
from src.domain.services.ticket_client_service import TicketClientService
from src.domain.services.ticket_execution_service import TicketExecutionService
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.services.ticket_review_service import TicketReviewService
from src.domain.services.ticket_user_sync_service import TicketUserSyncService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.statuses.ticket_user_status import TicketUserStatus

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def created_ticket(*, linked_user_ticket_id: int = 0, user_id: int = 0) -> Ticket:
    return Ticket.create(
        client_id=10,
        admin_id=100,
        user_id=user_id,
        user_ticket_id=linked_user_ticket_id,
        text_of_ticket="Need help",
        date_created=BASE,
    )


def accepted_ticket() -> Ticket:
    ticket = created_ticket()
    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=101,
        date_created=BASE + timedelta(minutes=1),
    )
    return ticket


def assigned_ticket(executor_id: int = 200) -> Ticket:
    ticket = accepted_ticket()
    TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=101,
        executor_id=executor_id,
        date_created=BASE + timedelta(minutes=2),
    )
    return ticket


def review_ticket(executor_id: int = 200) -> Ticket:
    ticket = assigned_ticket(executor_id)
    at_work = TicketStatusRecord.create_at_work(
        actor_employee_id=executor_id,
        executor_id=executor_id,
        date_created=BASE + timedelta(minutes=3),
    )
    ticket.append_status(at_work)
    review = TicketStatusRecord.create_ready_for_review_from_work(
        actor_employee_id=executor_id,
        executor_id=executor_id,
        date_created=BASE + timedelta(minutes=10),
    )
    ticket.append_status(review)
    return ticket


def test_admin_department_service_changes_and_removes_department() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin", department_id=1)
    department = Department.create(department_id=2, name="Other")
    AdminDepartmentService.change_department(
        admin=admin,
        department=department,
        has_at_work_tickets=False,
    )
    assert admin.department_id == 2
    AdminDepartmentService.remove_department(
        admin=admin,
        has_at_work_tickets=False,
    )
    assert admin.department_id == 0


def test_admin_department_service_rejects_disabled_department_or_working_ticket() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin", department_id=1)
    disabled = Department.create(department_id=2, name="Other", enabled=False)
    with pytest.raises(DomainOperationError, match="disabled"):
        AdminDepartmentService.change_department(
            admin=admin,
            department=disabled,
            has_at_work_tickets=False,
        )
    with pytest.raises(DomainOperationError, match="tickets in work"):
        AdminDepartmentService.remove_department(
            admin=admin,
            has_at_work_tickets=True,
        )


@pytest.mark.parametrize(
    "initial,expected",
    [
        (TicketStatus.CREATED, TicketStatus.REJECTED),
        (TicketStatus.ACCEPTED, TicketStatus.DEFERRED),
        (TicketStatus.SCHEDULED, TicketStatus.DEFERRED),
        (TicketStatus.ASSIGNED, TicketStatus.DEFERRED),
        (TicketStatus.READY_TO_WORK, TicketStatus.DEFERRED),
    ],
)
def test_ticket_client_service_handles_disable_for_actionable_states(initial: TicketStatus, expected: TicketStatus) -> None:
    ticket = created_ticket()
    if initial is not TicketStatus.CREATED:
        TicketManagementService.accept(ticket=ticket, actor_employee_id=101, date_created=BASE + timedelta(minutes=1))
    if initial is TicketStatus.SCHEDULED:
        TicketManagementService.schedule(ticket=ticket, actor_employee_id=101, planned_start_at=BASE + timedelta(days=1), date_created=BASE + timedelta(minutes=2))
    elif initial is TicketStatus.ASSIGNED:
        TicketManagementService.assign(ticket=ticket, actor_employee_id=101, executor_id=200, date_created=BASE + timedelta(minutes=2))
    elif initial is TicketStatus.READY_TO_WORK:
        TicketManagementService.ready_to_work(ticket=ticket, actor_employee_id=101, executor_id=200, planned_start_at=BASE + timedelta(days=1), date_created=BASE + timedelta(minutes=2))

    changed = TicketClientService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=101,
        comment="Client disabled",
        date_created=BASE + timedelta(minutes=3),
    )
    assert changed is True
    assert ticket.current_status_record().status is expected


def test_ticket_client_service_ignores_in_progress_and_terminal_states() -> None:
    ticket = assigned_ticket()
    ticket.append_status(TicketStatusRecord.create_at_work(actor_employee_id=200, executor_id=200, date_created=BASE + timedelta(minutes=3)))
    assert TicketClientService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=101,
        comment="Client disabled",
        date_created=BASE + timedelta(minutes=4),
    ) is False
    assert ticket.current_status_record().status is TicketStatus.AT_WORK


def test_management_service_happy_path_records_expected_payloads() -> None:
    ticket = created_ticket()
    accepted = TicketManagementService.accept(ticket=ticket, actor_employee_id=101, comment="ok", date_created=BASE + timedelta(minutes=1))
    assert accepted.status is TicketStatus.ACCEPTED
    scheduled = TicketManagementService.schedule(
        ticket=ticket,
        actor_employee_id=101,
        planned_start_at=BASE + timedelta(days=1),
        planned_finish_at=BASE + timedelta(days=2),
        comment="schedule",
        date_created=BASE + timedelta(minutes=2),
    )
    assert scheduled.status is TicketStatus.SCHEDULED
    assert scheduled.planned_finish_at == BASE + timedelta(days=2)
    assigned = TicketManagementService.assign(ticket=ticket, actor_employee_id=101, executor_id=200, date_created=BASE + timedelta(minutes=3))
    assert assigned.executor_id == 200


def test_management_service_cancel_by_user_only_works_for_ticket_from_user() -> None:
    ticket = Ticket.create_from_ticket_user(
        client_id=10,
        user_id=20,
        contact_user_id=0,
        user_ticket_id=30,
        text_of_ticket="Need help",
        date_created=BASE,
    )
    record = TicketManagementService.cancel_by_user(ticket=ticket, date_created=BASE + timedelta(minutes=1))
    assert record.status is TicketStatus.CANCELLED_BY_USER
    assert record.actor_employee_id == 0

    with pytest.raises(DomainOperationError):
        TicketManagementService.cancel_by_user(ticket=created_ticket(), date_created=BASE + timedelta(minutes=1))


def test_execution_service_only_current_executor_can_take_pause_resume_submit() -> None:
    ticket = assigned_ticket(executor_id=200)
    with pytest.raises(DomainOperationError, match="current executor"):
        TicketExecutionService.take_to_work(ticket=ticket, actor_employee_id=201)

    work = TicketExecutionService.take_to_work(ticket=ticket, actor_employee_id=200)
    assert work.status is TicketStatus.AT_WORK
    assert ticket.is_in_work()

    with pytest.raises(DomainOperationError, match="current executor"):
        TicketExecutionService.pause_work(ticket=ticket, actor_employee_id=201)
    pause = TicketExecutionService.pause_work(ticket=ticket, actor_employee_id=200)
    assert pause.status is TicketStatus.PAUSED

    resumed = TicketExecutionService.resume_work(ticket=ticket, actor_employee_id=200)
    assert resumed.status is TicketStatus.AT_WORK
    review = TicketExecutionService.submit_for_review(ticket=ticket, actor_employee_id=200)
    assert review.status is TicketStatus.READY_FOR_REVIEW


def test_execution_service_rejects_action_from_wrong_state() -> None:
    ticket = accepted_ticket()
    with pytest.raises(DomainOperationError):
        TicketExecutionService.take_to_work(ticket=ticket, actor_employee_id=200)
    with pytest.raises(DomainOperationError):
        TicketExecutionService.pause_work(ticket=ticket, actor_employee_id=200)


def test_retroactive_work_allows_unassigned_scheduled_executor_but_requires_current_executor_match_when_assigned() -> None:
    ticket = accepted_ticket()
    TicketManagementService.schedule(
        ticket=ticket,
        actor_employee_id=101,
        planned_start_at=BASE + timedelta(days=1),
        date_created=BASE + timedelta(minutes=2),
    )
    rec = TicketExecutionService.record_completed_work_for_review(
        ticket=ticket,
        actor_employee_id=101,
        executor_id=250,
        actual_started_at=BASE + timedelta(minutes=3),
        actual_finished_at=BASE + timedelta(minutes=4),
    )
    assert rec.executor_id == 250

    ticket2 = assigned_ticket(executor_id=200)
    with pytest.raises(DomainOperationError, match="must match"):
        TicketExecutionService.record_completed_work_for_review(
            ticket=ticket2,
            actor_employee_id=101,
            executor_id=201,
            actual_started_at=BASE + timedelta(minutes=3),
            actual_finished_at=BASE + timedelta(minutes=4),
        )


def test_review_service_requires_pending_review() -> None:
    with pytest.raises(DomainOperationError):
        TicketReviewService.confirm_execution(ticket=accepted_ticket(), actor_employee_id=101)


def test_review_service_confirm_execution_closes_ticket() -> None:
    ticket = review_ticket()
    record = TicketReviewService.confirm_execution(ticket=ticket, actor_employee_id=101, comment="ok")
    assert record.status is TicketStatus.EXECUTED
    assert ticket.is_closed


def test_review_service_return_paths() -> None:
    # Each case uses a fresh review ticket because one transition changes current state.
    ticket = review_ticket()
    assert TicketReviewService.return_to_work(ticket=ticket, actor_employee_id=101).status is TicketStatus.AT_WORK

    ticket = review_ticket()
    assert TicketReviewService.return_to_assigned(ticket=ticket, actor_employee_id=101, executor_id=201).status is TicketStatus.ASSIGNED

    ticket = review_ticket()
    assert TicketReviewService.return_to_scheduled(ticket=ticket, actor_employee_id=101, planned_start_at=datetime.now(timezone.utc)).status is TicketStatus.SCHEDULED

    ticket = review_ticket()
    assert TicketReviewService.return_to_ready_to_work(ticket=ticket, actor_employee_id=101, executor_id=201, planned_start_at=datetime.now(timezone.utc)).status is TicketStatus.READY_TO_WORK

    ticket = review_ticket()
    assert TicketReviewService.return_to_deferred(ticket=ticket, actor_employee_id=101, comment="later").status is TicketStatus.DEFERRED


def linked_pair() -> tuple[Ticket, TicketUser]:
    ticket_user = TicketUser.create(
        client_id=10,
        user_id=20,
        text_of_ticket="Need help",
        date_created=BASE,
    )
    ticket_user.ticket_id = 30
    ticket = Ticket.create_from_ticket_user(
        client_id=10,
        user_id=20,
        contact_user_id=0,
        user_ticket_id=30,
        text_of_ticket="Need help",
        date_created=BASE,
    )
    ticket.ticket_id = 40
    return ticket, ticket_user


def test_ticket_user_sync_mapping_happy_path() -> None:
    ticket, ticket_user = linked_pair()
    TicketManagementService.accept(ticket=ticket, actor_employee_id=100, date_created=BASE + timedelta(minutes=1))
    assert TicketUserSyncService.sync_from_ticket(ticket=ticket, ticket_user=ticket_user, actor_employee_id=100)
    assert ticket_user.current_status() is TicketUserStatus.CONFIRMED_BY_ADMIN

    TicketManagementService.assign(ticket=ticket, actor_employee_id=100, executor_id=200, date_created=BASE + timedelta(minutes=2))
    assert TicketUserSyncService.sync_from_ticket(ticket=ticket, ticket_user=ticket_user, actor_employee_id=100)
    assert ticket_user.current_status() is TicketUserStatus.IN_WORK

    ticket.append_status(TicketStatusRecord.create_at_work(actor_employee_id=200, executor_id=200, date_created=BASE + timedelta(minutes=3)))
    # Target is still IN_WORK: no redundant self transition.
    assert TicketUserSyncService.sync_from_ticket(ticket=ticket, ticket_user=ticket_user, actor_employee_id=200) is False

    ticket.append_status(TicketStatusRecord.create_ready_for_review_from_work(actor_employee_id=200, executor_id=200, date_created=BASE + timedelta(minutes=4)))
    assert TicketUserSyncService.sync_from_ticket(ticket=ticket, ticket_user=ticket_user, actor_employee_id=200)
    assert ticket_user.current_status() is TicketUserStatus.WAITING_FOR_CONFIRMATION

    TicketReviewService.confirm_execution(ticket=ticket, actor_employee_id=100)
    assert TicketUserSyncService.sync_from_ticket(ticket=ticket, ticket_user=ticket_user, actor_employee_id=100)
    assert ticket_user.current_status() is TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN


def test_ticket_user_sync_does_not_overwrite_terminal_user_confirmation() -> None:
    ticket, ticket_user = linked_pair()
    ticket_user.confirm_by_admin(actor_employee_id=100)
    ticket_user.mark_in_work(actor_employee_id=100)
    ticket_user.mark_waiting_for_confirmation(actor_employee_id=100)
    ticket_user.confirm_execution_by_user(actor_employee_id=20)

    TicketManagementService.accept(ticket=ticket, actor_employee_id=100, date_created=BASE + timedelta(minutes=1))
    assert TicketUserSyncService.sync_from_ticket(ticket=ticket, ticket_user=ticket_user, actor_employee_id=100) is False
    assert ticket_user.current_status() is TicketUserStatus.EXECUTION_CONFIRMED_BY_USER


def test_ticket_user_sync_rejects_broken_link() -> None:
    ticket, ticket_user = linked_pair()
    ticket.user_ticket_id = 999
    with pytest.raises(DomainOperationError):
        TicketUserSyncService.sync_from_ticket(ticket=ticket, ticket_user=ticket_user, actor_employee_id=100)
