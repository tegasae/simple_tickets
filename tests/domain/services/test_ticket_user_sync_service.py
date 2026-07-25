# tests/domain/services/test_ticket_user_sync_service.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_user_sync_service import TicketUserSyncService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_user import (
    StatusRecordTicketUser,
    TicketUser,
    TicketUserStatus,
)


CLIENT_ID = 10
OTHER_CLIENT_ID = 11

USER_ID = 101
OTHER_USER_ID = 102
CONTACT_USER_ID = 103

ADMIN_ID = 201
EXECUTOR_ID = 301

TICKET_ID = 1001
TICKET_USER_ID = 5001
OTHER_TICKET_USER_ID = 5002

BASE_TIME = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
SYNC_COMMENT = "Synced from internal ticket"


def minutes_after(minutes: int) -> datetime:
    return BASE_TIME + timedelta(minutes=minutes)


def make_ticket_status_record(
    status: TicketStatus,
    *,
    status_id: int,
    date_created: datetime,
    actor_employee_id: int | None = None,
) -> TicketStatusRecord:
    """
    Создаёт валидную TicketStatusRecord для нужного статуса.

    Здесь мы не тестируем TicketStatusRecord отдельно.
    Поэтому helper подставляет минимальный корректный payload
    для статусов, которым он нужен.
    """
    if actor_employee_id is None:
        actor_employee_id = (
            0
            if status in {
                TicketStatus.CREATED_FROM_TICKET_USER,
                TicketStatus.CANCELLED_BY_USER,
            }
            else ADMIN_ID
        )

    executor_id = 0
    planned_start_at = None
    planned_finish_at = None
    actual_started_at = None
    actual_finished_at = None
    comment = ""

    if status in {
        TicketStatus.DEFERRED,
        TicketStatus.REJECTED,
        TicketStatus.CANCELLED,
    }:
        comment = "Required comment"

    if status == TicketStatus.SCHEDULED:
        planned_start_at = minutes_after(30)

    if status == TicketStatus.ASSIGNED:
        executor_id = EXECUTOR_ID

    if status == TicketStatus.READY_TO_WORK:
        executor_id = EXECUTOR_ID
        planned_start_at = minutes_after(30)

    if status == TicketStatus.AT_WORK:
        executor_id = EXECUTOR_ID
        actual_started_at = date_created

    if status == TicketStatus.PAUSED:
        executor_id = EXECUTOR_ID

    if status == TicketStatus.READY_FOR_REVIEW:
        executor_id = EXECUTOR_ID
        actual_finished_at = date_created

    return TicketStatusRecord(
        status_id=status_id,
        actor_employee_id=actor_employee_id,
        status=status,
        date_created=date_created,
        executor_id=executor_id,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        actual_started_at=actual_started_at,
        actual_finished_at=actual_finished_at,
        comment=comment,
    )


def make_ticket_status_history(
    current_status: TicketStatus,
) -> list[TicketStatusRecord]:
    """
    Собирает семантически правдоподобную историю Ticket
    с нужным текущим статусом.

    Для sync-тестов важен именно current_status,
    но история сделана нормальной, чтобы тесты не зависели
    от случайной слабости rehydrate().
    """
    if current_status == TicketStatus.CREATED:
        return [
            make_ticket_status_record(
                TicketStatus.CREATED,
                status_id=1,
                date_created=BASE_TIME,
                actor_employee_id=ADMIN_ID,
            ),
        ]

    if current_status == TicketStatus.CREATED_FROM_TICKET_USER:
        return [
            make_ticket_status_record(
                TicketStatus.CREATED_FROM_TICKET_USER,
                status_id=1,
                date_created=BASE_TIME,
                actor_employee_id=0,
            ),
        ]

    records = [
        make_ticket_status_record(
            TicketStatus.CREATED_FROM_TICKET_USER,
            status_id=1,
            date_created=BASE_TIME,
            actor_employee_id=0,
        ),
    ]

    if current_status in {
        TicketStatus.REJECTED,
        TicketStatus.CANCELLED_BY_USER,
    }:
        records.append(
            make_ticket_status_record(
                current_status,
                status_id=2,
                date_created=minutes_after(1),
            ),
        )
        return records

    records.append(
        make_ticket_status_record(
            TicketStatus.ACCEPTED,
            status_id=2,
            date_created=minutes_after(1),
            actor_employee_id=ADMIN_ID,
        ),
    )

    if current_status == TicketStatus.ACCEPTED:
        return records

    if current_status in {
        TicketStatus.DEFERRED,
        TicketStatus.SCHEDULED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_TO_WORK,
        TicketStatus.CANCELLED,
    }:
        records.append(
            make_ticket_status_record(
                current_status,
                status_id=3,
                date_created=minutes_after(2),
            ),
        )
        return records

    records.append(
        make_ticket_status_record(
            TicketStatus.READY_TO_WORK,
            status_id=3,
            date_created=minutes_after(2),
        ),
    )

    records.append(
        make_ticket_status_record(
            TicketStatus.AT_WORK,
            status_id=4,
            date_created=minutes_after(3),
            actor_employee_id=EXECUTOR_ID,
        ),
    )

    if current_status == TicketStatus.AT_WORK:
        return records

    if current_status == TicketStatus.PAUSED:
        records.append(
            make_ticket_status_record(
                TicketStatus.PAUSED,
                status_id=5,
                date_created=minutes_after(4),
                actor_employee_id=EXECUTOR_ID,
            ),
        )
        return records

    records.append(
        make_ticket_status_record(
            TicketStatus.READY_FOR_REVIEW,
            status_id=5,
            date_created=minutes_after(5),
            actor_employee_id=EXECUTOR_ID,
        ),
    )

    if current_status == TicketStatus.READY_FOR_REVIEW:
        return records

    if current_status == TicketStatus.EXECUTED:
        records.append(
            make_ticket_status_record(
                TicketStatus.EXECUTED,
                status_id=6,
                date_created=minutes_after(6),
                actor_employee_id=ADMIN_ID,
            ),
        )
        return records

    raise AssertionError(
        f"Unsupported TicketStatus in test helper: {current_status}",
    )


def make_ticket(
    current_status: TicketStatus,
    *,
    ticket_id: int = TICKET_ID,
    client_id: int = CLIENT_ID,
    user_id: int = USER_ID,
    user_ticket_id: int = TICKET_USER_ID,
) -> Ticket:
    admin_id = ADMIN_ID

    if current_status in {
        TicketStatus.CREATED_FROM_TICKET_USER,
        TicketStatus.REJECTED,
        TicketStatus.CANCELLED_BY_USER,
    }:
        admin_id = 0

    return Ticket.rehydrate(
        ticket_id=ticket_id,
        client_id=client_id,
        admin_id=admin_id,
        text_of_ticket="Need help",
        user_id=user_id,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=user_ticket_id,
        statuses=make_ticket_status_history(current_status),
        date_created=BASE_TIME,
    )


def make_ticket_user_status_record(
    status: TicketUserStatus,
    *,
    status_id: int,
    actor_employee_id: int,
    date_created: datetime,
    comment: str = "",
) -> StatusRecordTicketUser:
    return StatusRecordTicketUser(
        status_id=status_id,
        actor_employee_id=actor_employee_id,
        status=status,
        comment=comment,
        date_created=date_created,
    )


def make_ticket_user_status_history(
    current_status: TicketUserStatus,
) -> list[StatusRecordTicketUser]:
    records = [
        make_ticket_user_status_record(
            TicketUserStatus.CREATED,
            status_id=1,
            actor_employee_id=USER_ID,
            date_created=BASE_TIME,
        ),
    ]

    if current_status == TicketUserStatus.CREATED:
        return records

    if current_status == TicketUserStatus.CANCELLED_BY_USER:
        records.append(
            make_ticket_user_status_record(
                TicketUserStatus.CANCELLED_BY_USER,
                status_id=2,
                actor_employee_id=USER_ID,
                date_created=minutes_after(1),
                comment="Cancelled by user",
            ),
        )
        return records

    if current_status == TicketUserStatus.CANCELLED_BY_ADMIN:
        records.append(
            make_ticket_user_status_record(
                TicketUserStatus.CANCELLED_BY_ADMIN,
                status_id=2,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(1),
                comment="Cancelled by admin",
            ),
        )
        return records

    records.append(
        make_ticket_user_status_record(
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            status_id=2,
            actor_employee_id=ADMIN_ID,
            date_created=minutes_after(1),
        ),
    )

    if current_status == TicketUserStatus.CONFIRMED_BY_ADMIN:
        return records

    records.append(
        make_ticket_user_status_record(
            TicketUserStatus.IN_WORK,
            status_id=3,
            actor_employee_id=ADMIN_ID,
            date_created=minutes_after(2),
        ),
    )

    if current_status == TicketUserStatus.IN_WORK:
        return records

    records.append(
        make_ticket_user_status_record(
            TicketUserStatus.WAITING_FOR_CONFIRMATION,
            status_id=4,
            actor_employee_id=ADMIN_ID,
            date_created=minutes_after(3),
        ),
    )

    if current_status == TicketUserStatus.WAITING_FOR_CONFIRMATION:
        return records

    if current_status == TicketUserStatus.EXECUTION_CONFIRMED_BY_USER:
        records.append(
            make_ticket_user_status_record(
                TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
                status_id=5,
                actor_employee_id=USER_ID,
                date_created=minutes_after(4),
                comment="Confirmed by user",
            ),
        )
        return records

    if current_status == TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN:
        records.append(
            make_ticket_user_status_record(
                TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
                status_id=5,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(4),
                comment="Confirmed by admin",
            ),
        )
        return records

    raise AssertionError(
        f"Unsupported TicketUserStatus in test helper: {current_status}",
    )


def make_ticket_user(
    current_status: TicketUserStatus,
    *,
    ticket_id: int = TICKET_USER_ID,
    client_id: int = CLIENT_ID,
    user_id: int = USER_ID,
) -> TicketUser:
    return TicketUser.rehydrate(
        ticket_id=ticket_id,
        client_id=client_id,
        user_id=user_id,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        statuses=make_ticket_user_status_history(current_status),
        date_created=BASE_TIME,
    )


@pytest.mark.parametrize(
    (
        "ticket_status",
        "initial_ticket_user_status",
        "expected_ticket_user_status",
        "actor_employee_id",
    ),
    [
        (
            TicketStatus.ACCEPTED,
            TicketUserStatus.CREATED,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            ADMIN_ID,
        ),
        (
            TicketStatus.DEFERRED,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            TicketUserStatus.IN_WORK,
            ADMIN_ID,
        ),
        (
            TicketStatus.SCHEDULED,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            TicketUserStatus.IN_WORK,
            ADMIN_ID,
        ),
        (
            TicketStatus.ASSIGNED,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            TicketUserStatus.IN_WORK,
            ADMIN_ID,
        ),
        (
            TicketStatus.READY_TO_WORK,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            TicketUserStatus.IN_WORK,
            ADMIN_ID,
        ),
        (
            TicketStatus.AT_WORK,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            TicketUserStatus.IN_WORK,
            ADMIN_ID,
        ),
        (
            TicketStatus.PAUSED,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            TicketUserStatus.IN_WORK,
            ADMIN_ID,
        ),
        (
            TicketStatus.READY_FOR_REVIEW,
            TicketUserStatus.IN_WORK,
            TicketUserStatus.WAITING_FOR_CONFIRMATION,
            ADMIN_ID,
        ),
        (
            TicketStatus.EXECUTED,
            TicketUserStatus.WAITING_FOR_CONFIRMATION,
            TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
            ADMIN_ID,
        ),
        (
            TicketStatus.REJECTED,
            TicketUserStatus.CREATED,
            TicketUserStatus.CANCELLED_BY_ADMIN,
            ADMIN_ID,
        ),
        (
            TicketStatus.CANCELLED,
            TicketUserStatus.CREATED,
            TicketUserStatus.CANCELLED_BY_ADMIN,
            ADMIN_ID,
        ),
        (
            TicketStatus.CANCELLED_BY_USER,
            TicketUserStatus.CREATED,
            TicketUserStatus.CANCELLED_BY_USER,
            USER_ID,
        ),
    ],
)
def test_sync_maps_ticket_status_to_ticket_user_status(
    ticket_status: TicketStatus,
    initial_ticket_user_status: TicketUserStatus,
    expected_ticket_user_status: TicketUserStatus,
    actor_employee_id: int,
) -> None:
    ticket = make_ticket(ticket_status)
    ticket_user = make_ticket_user(initial_ticket_user_status)

    initial_status_count = len(ticket_user.statuses)

    changed = TicketUserSyncService.sync_from_ticket(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=actor_employee_id,
        comment=SYNC_COMMENT,
    )

    assert changed is True
    assert len(ticket_user.statuses) == initial_status_count + 1
    assert ticket_user.current_status() == expected_ticket_user_status
    assert ticket_user.current_status_record().actor_employee_id == actor_employee_id
    assert ticket_user.current_status_record().comment == SYNC_COMMENT


@pytest.mark.parametrize(
    "ticket_status",
    [
        TicketStatus.CREATED,
        TicketStatus.CREATED_FROM_TICKET_USER,
    ],
)
def test_sync_does_nothing_for_unmapped_ticket_status(
    ticket_status: TicketStatus,
) -> None:
    ticket = make_ticket(ticket_status)
    ticket_user = make_ticket_user(TicketUserStatus.CREATED)

    initial_status_count = len(ticket_user.statuses)

    changed = TicketUserSyncService.sync_from_ticket(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=ADMIN_ID,
        comment=SYNC_COMMENT,
    )

    assert changed is False
    assert len(ticket_user.statuses) == initial_status_count
    assert ticket_user.current_status() == TicketUserStatus.CREATED


def test_sync_does_nothing_when_ticket_user_already_has_target_status() -> None:
    ticket = make_ticket(TicketStatus.ACCEPTED)
    ticket_user = make_ticket_user(TicketUserStatus.CONFIRMED_BY_ADMIN)

    initial_status_count = len(ticket_user.statuses)

    changed = TicketUserSyncService.sync_from_ticket(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=ADMIN_ID,
        comment=SYNC_COMMENT,
    )

    assert changed is False
    assert len(ticket_user.statuses) == initial_status_count
    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN


def test_sync_does_not_overwrite_terminal_ticket_user() -> None:
    ticket = make_ticket(TicketStatus.ACCEPTED)
    ticket_user = make_ticket_user(TicketUserStatus.CANCELLED_BY_USER)

    initial_status_count = len(ticket_user.statuses)

    changed = TicketUserSyncService.sync_from_ticket(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=ADMIN_ID,
        comment=SYNC_COMMENT,
    )

    assert changed is False
    assert len(ticket_user.statuses) == initial_status_count
    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_USER


def test_sync_rejects_unlinked_ticket() -> None:
    ticket = make_ticket(
        TicketStatus.ACCEPTED,
        user_ticket_id=0,
    )
    ticket_user = make_ticket_user(TicketUserStatus.CREATED)

    with pytest.raises(DomainOperationError):
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment=SYNC_COMMENT,
        )


def test_sync_rejects_different_ticket_user_id() -> None:
    ticket = make_ticket(
        TicketStatus.ACCEPTED,
        user_ticket_id=OTHER_TICKET_USER_ID,
    )
    ticket_user = make_ticket_user(TicketUserStatus.CREATED)

    with pytest.raises(DomainOperationError):
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment=SYNC_COMMENT,
        )


def test_sync_rejects_different_client_id() -> None:
    ticket = make_ticket(
        TicketStatus.ACCEPTED,
        client_id=OTHER_CLIENT_ID,
    )
    ticket_user = make_ticket_user(TicketUserStatus.CREATED)

    with pytest.raises(DomainOperationError):
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment=SYNC_COMMENT,
        )


def test_sync_rejects_different_user_id() -> None:
    ticket = make_ticket(
        TicketStatus.ACCEPTED,
        user_id=OTHER_USER_ID,
    )
    ticket_user = make_ticket_user(TicketUserStatus.CREATED)

    with pytest.raises(DomainOperationError):
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=ADMIN_ID,
            comment=SYNC_COMMENT,
        )


def test_sync_rejects_non_positive_actor_when_change_is_required() -> None:
    ticket = make_ticket(TicketStatus.ACCEPTED)
    ticket_user = make_ticket_user(TicketUserStatus.CREATED)

    with pytest.raises(DomainOperationError):
        TicketUserSyncService.sync_from_ticket(
            ticket=ticket,
            ticket_user=ticket_user,
            actor_employee_id=0,
            comment=SYNC_COMMENT,
        )