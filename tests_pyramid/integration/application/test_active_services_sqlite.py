from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.application.dto.ticket_dto import TicketDTO, TicketUserDTO
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket_user import TicketUserStatus
from tests_pyramid.support.service_imports import (
    TicketApplicationService,
    TicketUserApplicationService,
)
from utils.db.connect import Connection

pytestmark = pytest.mark.integration


def _find_source_db() -> Path:
    candidates = [
        Path.cwd() / "db" / "admins.db",
        Path(__file__).resolve().parents[3] / "db" / "admins.db",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Cannot find db/admins.db; run pytest from project root")


def _clean_db(path: Path) -> None:
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA foreign_keys=OFF")
    tables = [
        row[0]
        for row in raw.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    for table in tables:
        raw.execute(f'DELETE FROM "{table}"')
    raw.execute("DELETE FROM sqlite_sequence")
    raw.commit()
    raw.close()


@pytest.fixture
def conn(tmp_path: Path):
    path = tmp_path / "services.sqlite3"
    shutil.copy2(_find_source_db(), path)
    _clean_db(path)
    connection = Connection.create_connection(str(path), engine=sqlite3)
    yield connection
    connection.close()


def _seed(conn: Connection) -> tuple[Admin, Client, User, User, Department]:
    with SQLiteUnitOfWork(conn) as uow:
        department = uow.departments.save(
            Department.create(department_id=0, name="Support", enabled=True)
        )
        admin = uow.admins.save(
            Admin.create(
                employee_id=0,
                first_name="Admin",
                department_id=department.department_id,
            )
        )
        client = uow.clients.save(
            Client.create(
                client_id=0,
                name="Acme",
                created_by_admin_id=admin.employee_id,
            )
        )
        user = uow.users.save(
            User.create(
                employee_id=0,
                first_name="User",
                client_id=client.client_id,
            )
        )
        contact = uow.users.save(
            User.create(
                employee_id=0,
                first_name="Contact",
                client_id=client.client_id,
            )
        )
    return admin, client, user, contact, department


class AdminActor:
    def __init__(self, admin: Admin, *, can_accept: bool = False) -> None:
        self.admin = admin
        self.can_accept = can_accept

    def require_actor_admin(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> Admin:
        assert actor_admin_id == self.admin.employee_id
        if permission is AdminPermission.TICKET_ACCEPTED and not self.can_accept:
            raise PermissionError("not allowed")
        return self.admin


class UserActor:
    def __init__(self, user: User) -> None:
        self.user = user

    def require_actor_user(
        self,
        *,
        actor_user_id: int,
        permission: UserPermission,
    ) -> User:
        assert actor_user_id == self.user.employee_id
        assert permission in {
            UserPermission.TICKET_OPERATION,
            UserPermission.TICKET_VIEW,
            UserPermission.TICKET_VIEW_ALL,
            UserPermission.TICKET_OPERATION_ALL,
        }
        return self.user


def test_ticket_user_create_from_user_persists_both_aggregates(conn: Connection) -> None:
    admin, client, user, contact, department = _seed(conn)
    service = TicketUserApplicationService(SQLiteUnitOfWork(conn))
    service.actor = UserActor(user)

    result = service.create_from_user(
        ticket_user_dto=TicketUserDTO(
            ticket_user_id=0,
            client_id=client.client_id,
            actor_user_id=user.employee_id,
            contact_user_id=contact.employee_id,
            department_id=department.department_id,
            text_of_ticket="VPN is down",
            description="Created from portal",
            urgency_level=2,
            is_remote=True,
            comment="Initial user comment",
        )
    )

    with SQLiteUnitOfWork(conn) as uow:
        ticket_user = uow.user_tickets.get(result.ticket_id)
        ticket = uow.tickets.get_by_user_ticket_id(result.ticket_id)

    assert ticket_user.current_status() is TicketUserStatus.CREATED
    assert ticket_user.current_status_record().actor_employee_id == user.employee_id
    assert ticket.admin_id == 0
    assert ticket.current_status_record().status is TicketStatus.CREATED_FROM_TICKET_USER
    assert ticket.current_status_record().actor_employee_id == 0
    assert ticket.user_ticket_id == ticket_user.ticket_id
    assert ticket.client_id == ticket_user.client_id
    assert ticket.user_id == ticket_user.user_id
    assert ticket.contact_user_id == ticket_user.contact_user_id


def test_admin_create_ticket_without_user_persists_creator_semantics(conn: Connection) -> None:
    admin, client, user, contact, department = _seed(conn)
    service = TicketApplicationService(SQLiteUnitOfWork(conn))
    service.actor = AdminActor(admin, can_accept=False)

    result = service.create_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=admin.employee_id,
            client_id=client.client_id,
            department_id=department.department_id,
            text_of_ticket="Printer is broken",
        )
    )

    with SQLiteUnitOfWork(conn) as uow:
        ticket = uow.tickets.get(result.ticket_id)

    assert ticket.admin_id == admin.employee_id
    assert ticket.user_ticket_id == 0
    assert [record.status for record in ticket.statuses] == [TicketStatus.CREATED]
    assert ticket.statuses[0].actor_employee_id == admin.employee_id


def test_admin_phone_request_with_accept_permission_persists_both_histories(conn: Connection) -> None:
    admin, client, user, contact, department = _seed(conn)
    service = TicketApplicationService(SQLiteUnitOfWork(conn))
    service.actor = AdminActor(admin, can_accept=True)

    result = service.create_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=admin.employee_id,
            client_id=client.client_id,
            user_id=user.employee_id,
            contact_user_id=contact.employee_id,
            department_id=department.department_id,
            text_of_ticket="User called about VPN",
            comment="Registered by phone",
        )
    )

    with SQLiteUnitOfWork(conn) as uow:
        ticket = uow.tickets.get(result.ticket_id)
        ticket_user = uow.user_tickets.get(ticket.user_ticket_id)

    assert ticket.admin_id == admin.employee_id
    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
    ]
    assert [record.actor_employee_id for record in ticket.statuses] == [
        admin.employee_id,
        admin.employee_id,
    ]
    assert ticket_user.statuses[0].status is TicketUserStatus.CREATED
    assert ticket_user.statuses[0].actor_employee_id == user.employee_id
    assert ticket_user.current_status() is TicketUserStatus.CONFIRMED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == admin.employee_id


def test_linked_update_details_roundtrips_to_sqlite(conn: Connection) -> None:
    admin, client, user, contact, department = _seed(conn)
    service = TicketApplicationService(SQLiteUnitOfWork(conn))
    service.actor = AdminActor(admin, can_accept=False)

    created = service.create_ticket(
        ticket_dto=TicketDTO(
            actor_admin_id=admin.employee_id,
            client_id=client.client_id,
            user_id=user.employee_id,
            contact_user_id=0,
            department_id=department.department_id,
            text_of_ticket="Phone request",
        )
    )

    updated = service.update_details(
        ticket_dto=TicketDTO(
            actor_admin_id=admin.employee_id,
            ticket_id=created.ticket_id,
            description="Updated together",
            contact_user_id=contact.employee_id,
            is_remote=True,
        )
    )

    with SQLiteUnitOfWork(conn) as uow:
        ticket = uow.tickets.get(updated.ticket_id)
        ticket_user = uow.user_tickets.get(ticket.user_ticket_id)

    assert ticket.description == "Updated together"
    assert ticket_user.description == "Updated together"
    assert ticket.contact_user_id == contact.employee_id
    assert ticket_user.contact_user_id == contact.employee_id
    assert ticket.is_remote is True
