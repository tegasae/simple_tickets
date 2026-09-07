from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.client_dto import ClientDTO
from src.application.dto.department_dto import DepartmentDTO
from src.application.dto.employee_dto import UserDTO
from src.application.dto.ticket_dto import TicketDTO, TicketUserDTO
from src.application.services.client_service import ClientApplicationService
from src.application.services.department_service import DepartmentApplicationService
from src.application.services.ticket_service import TicketApplicationService
from src.application.services.ticket_user_service import TicketUserApplicationService
from src.application.services.user_service import UserApplicationService
from src.domain.employee import Admin
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket_user import TicketUserStatus
from utils.db.connect import Connection

pytestmark = pytest.mark.integration


def _source_db() -> Path:
    path = Path(__file__).resolve().parents[3] / "simple_tickets" / "db" / "admins.db"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _clean_db(path: Path) -> None:
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA foreign_keys=OFF")
    tables = [
        row[0]
        for row in raw.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    for table in tables:
        raw.execute(f'DELETE FROM "{table}"')
    raw.execute("DELETE FROM sqlite_sequence")
    raw.commit()
    raw.close()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "full_lifecycle.sqlite3"
    shutil.copy2(_source_db(), path)
    _clean_db(path)
    return path


def _connect(path: Path) -> Connection:
    return Connection.create_connection(str(path), engine=sqlite3)


def _seed_admins_and_roles(conn: Connection) -> tuple[Admin, Admin, int]:
    with SQLiteUnitOfWork(conn) as uow:
        admin_role = uow.roles_admin.add(
            Role(
                role_id=0,
                name="Ticket administrators",
                permissions=frozenset(
                    {
                        AdminPermission.CLIENT_OPERATION,
                        AdminPermission.ADMIN_OPERATION,
                        AdminPermission.USER_OPERATION,
                        AdminPermission.TICKET_OPERATION,
                        AdminPermission.TICKET_ACCEPTED,
                        AdminPermission.TICKET_VIEW,
                    }
                ),
            )
        )

        user_role = uow.roles_user.add(
            Role(
                role_id=0,
                name="Ticket users",
                permissions=frozenset(
                    {
                        UserPermission.TICKET_OPERATION,
                        UserPermission.TICKET_VIEW,
                    }
                ),
            )
        )

        operator = uow.admins.save(
            Admin.create(
                employee_id=0,
                first_name="Operator",
                roles={admin_role.role_id},
            )
        )

        executor = uow.admins.save(
            Admin.create(
                employee_id=0,
                first_name="Executor",
                roles={admin_role.role_id},
            )
        )

    return operator, executor, user_role.role_id


def test_full_user_ticket_lifecycle_survives_database_reopen(db_path: Path) -> None:
    conn = _connect(db_path)
    operator, executor, user_role_id = _seed_admins_and_roles(conn)

    # 1. Create Client through the real application service.
    client = ClientApplicationService(SQLiteUnitOfWork(conn)).create_client(
        ClientDTO(
            actor_admin_id=operator.employee_id,
            name="Acme",
        )
    )

    # 2. Create Department.
    department = DepartmentApplicationService(
        SQLiteUnitOfWork(conn)
    ).create_department(
        department_dto=DepartmentDTO(
            actor_admin_id=operator.employee_id,
            name="Support",
        )
    )

    # 3. Create User and assign a real User role.
    user = UserApplicationService(SQLiteUnitOfWork(conn)).create_user(
        user_dto=UserDTO(
            actor_admin_id=operator.employee_id,
            first_name="Alice",
            client_id=client.client_id,
            roles={user_role_id},
        )
    )

    # 4. User creates TicketUser. In the same transaction the service
    #    creates the linked internal Ticket.
    user_ticket_service = TicketUserApplicationService(
        SQLiteUnitOfWork(conn)
    )
    created_user_ticket = user_ticket_service.create_from_user(
        ticket_user_dto=TicketUserDTO(
            ticket_user_id=0,
            client_id=client.client_id,
            actor_user_id=user.employee_id,
            user_id=user.employee_id,
            text_of_ticket="VPN does not work",
            department_id=department.department_id,
            description="Created from user portal",
            comment="Initial request",
        )
    )

    ticket_user_id = created_user_ticket.ticket_id

    # 5. Verify both aggregates immediately from SQLite.
    with SQLiteUnitOfWork(conn) as uow:
        ticket_user = uow.user_tickets.get(ticket_user_id)
        ticket = uow.tickets.get_by_user_ticket_id(ticket_user_id)
        internal_ticket_id = ticket.ticket_id

    assert ticket_user.ticket_id == ticket_user_id
    assert ticket_user.client_id == client.client_id
    assert ticket_user.user_id == user.employee_id
    assert ticket_user.current_status() is TicketUserStatus.CREATED

    assert ticket.user_ticket_id == ticket_user_id
    assert ticket.client_id == ticket_user.client_id
    assert ticket.user_id == ticket_user.user_id
    assert ticket.contact_user_id == ticket_user.contact_user_id
    assert ticket.admin_id == 0
    assert ticket.current_status_record().status is TicketStatus.CREATED_FROM_TICKET_USER
    assert ticket.current_status_record().actor_employee_id == 0

    admin_ticket_service = TicketApplicationService(
        SQLiteUnitOfWork(conn)
    )

    # 6. Admin accepts the internal Ticket.
    admin_ticket_service.accept(
        ticket_dto=TicketDTO(
            actor_admin_id=operator.employee_id,
            ticket_id=internal_ticket_id,
            comment="Accepted",
        )
    )

    # 7. Admin assigns executor.
    admin_ticket_service.assign_executor(
        ticket_dto=TicketDTO(
            actor_admin_id=operator.employee_id,
            ticket_id=internal_ticket_id,
            executor_id=executor.employee_id,
            comment="Assigned",
        )
    )

    # 8. Executor starts work.
    admin_ticket_service.at_work(
        ticket_dto=TicketDTO(
            actor_admin_id=executor.employee_id,
            ticket_id=internal_ticket_id,
            comment="Work started",
        )
    )

    # 9. Executor submits result for review.
    admin_ticket_service.submit_for_review(
        ticket_dto=TicketDTO(
            actor_admin_id=executor.employee_id,
            ticket_id=internal_ticket_id,
            comment="Done, please confirm",
        )
    )

    # 10. User confirms execution. This must close both workflows with
    #     user-originated confirmation on TicketUser.
    user_ticket_service.confirm_execution_by_user(
        ticket_user_dto=TicketUserDTO(
            ticket_user_id=ticket_user_id,
            client_id=client.client_id,
            actor_user_id=user.employee_id,
            user_id=user.employee_id,
            text_of_ticket="",
            comment="Confirmed by user",
        )
    )

    # 11. Verify complete histories before reconnect.
    with SQLiteUnitOfWork(conn) as uow:
        ticket_before_reopen = uow.tickets.get(internal_ticket_id)
        ticket_user_before_reopen = uow.user_tickets.get(ticket_user_id)

    assert [record.status for record in ticket_before_reopen.statuses] == [
        TicketStatus.CREATED_FROM_TICKET_USER,
        TicketStatus.ACCEPTED,
        TicketStatus.ASSIGNED,
        TicketStatus.AT_WORK,
        TicketStatus.READY_FOR_REVIEW,
        TicketStatus.EXECUTED,
    ]

    assert [record.status for record in ticket_user_before_reopen.statuses] == [
        TicketUserStatus.CREATED,
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.IN_WORK,
        TicketUserStatus.WAITING_FOR_CONFIRMATION,
        TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
    ]

    assert ticket_before_reopen.is_closed is True
    assert ticket_user_before_reopen.is_closed is True

    # Ticket created automatically from TicketUser never acquires creator admin_id.
    assert ticket_before_reopen.admin_id == 0

    # 12. Simulate application/UoW restart: close the actual DB connection,
    #     open a fresh connection and rehydrate both aggregates from disk.
    conn.close()
    reopened_conn = _connect(db_path)

    try:
        with SQLiteUnitOfWork(reopened_conn) as uow:
            ticket_after_reopen = uow.tickets.get(internal_ticket_id)
            ticket_user_after_reopen = uow.user_tickets.get(ticket_user_id)

        assert [record.status for record in ticket_after_reopen.statuses] == [
            TicketStatus.CREATED_FROM_TICKET_USER,
            TicketStatus.ACCEPTED,
            TicketStatus.ASSIGNED,
            TicketStatus.AT_WORK,
            TicketStatus.READY_FOR_REVIEW,
            TicketStatus.EXECUTED,
        ]

        assert [record.status for record in ticket_user_after_reopen.statuses] == [
            TicketUserStatus.CREATED,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
            TicketUserStatus.IN_WORK,
            TicketUserStatus.WAITING_FOR_CONFIRMATION,
            TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
        ]

        assert ticket_after_reopen.user_ticket_id == ticket_user_after_reopen.ticket_id
        assert ticket_after_reopen.client_id == ticket_user_after_reopen.client_id
        assert ticket_after_reopen.user_id == ticket_user_after_reopen.user_id
        assert ticket_after_reopen.contact_user_id == ticket_user_after_reopen.contact_user_id
        assert ticket_after_reopen.admin_id == 0
        assert ticket_after_reopen.is_closed is True
        assert ticket_user_after_reopen.is_closed is True
    finally:
        reopened_conn.close()
