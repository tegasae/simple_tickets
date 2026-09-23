from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.adapters.repositories.mappers.admin_mapper import AdminMapper
from src.adapters.repositories.mappers.auxiliary import datetime_to_db, dt_from_sqlite, dt_to_sqlite_iso
from src.adapters.repositories.mappers.client_mapper import ClientMapper
from src.adapters.repositories.mappers.department_mapper import DepartmentMapper
from src.adapters.repositories.mappers.role_mapper import RoleMapper
from src.adapters.repositories.mappers.ticket_mapper import TicketMapper
from src.adapters.repositories.mappers.ticket_user_mapper import TicketUserMapper
from src.adapters.repositories.mappers.user_mapper import UserMapper
from src.domain.account import NoAccount
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment
from src.domain.ticket_user import TicketUser
from src.domain.statuses.ticket_user_status import TicketUserStatus, StatusRecordTicketUser

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("", None),
        ("   ", None),
        (BASE, BASE),
        (int(BASE.timestamp()), BASE),
        (BASE.isoformat(), BASE),
        (str(int(BASE.timestamp())), BASE),
    ],
)
def test_dt_from_sqlite_supported_values(value, expected) -> None:
    assert dt_from_sqlite(value) == expected


def test_dt_from_sqlite_normalizes_naive_and_non_utc() -> None:
    naive = datetime(2025, 1, 1, 12, 0)
    assert dt_from_sqlite(naive).tzinfo is UTC
    plus3 = datetime(2025, 1, 1, 15, 0, tzinfo=timezone(timedelta(hours=3)))
    assert dt_from_sqlite(plus3) == BASE


@pytest.mark.parametrize("value,exc", [("bad-date", ValueError), (1.2, TypeError)])
def test_dt_from_sqlite_rejects_invalid(value, exc) -> None:
    with pytest.raises(exc):
        dt_from_sqlite(value)


def test_datetime_to_db_none_and_utc_normalization() -> None:
    assert datetime_to_db(None) is None
    assert datetime_to_db(datetime(2025, 1, 1, 12, 0)) == BASE.isoformat()
    assert dt_to_sqlite_iso(BASE).startswith("2025-01-01T12:00:00")


def test_admin_mapper_roundtrip_core_account_and_department() -> None:
    admin = Admin.create(
        employee_id=10,
        first_name="Admin",
        last_name="User",
        email="admin@test.local",
        phone="12345",
        login="admin-login",
        password="Strong1!",
        job_title="Engineer",
        department_id=7,
    )
    employee = AdminMapper.employee_params(admin)
    admin_params = AdminMapper.admin_params(admin)
    account = AdminMapper.account_params(admin)
    assert employee["employee_id"] == 10 and employee["is_admin"] == 1
    assert admin_params == {"employee_id": 10, "job_title": "Engineer", "department_id": 7}
    assert account is not None and account["login"] == "admin-login"

    row = {
        **employee,
        **admin_params,
        "account_id": 5,
        "login": account["login"],
        "password": account["password"],
        "account_enabled": 1,
        "account_date_created": account["date_created"],
    }
    restored = AdminMapper.row_to_admin(row)
    assert restored.employee_id == 10
    assert restored.department_id == 7
    assert str(restored.account.login) == "admin-login"


def test_admin_mapper_no_account_maps_to_none_and_noaccount() -> None:
    admin = Admin.create(employee_id=10, first_name="Admin")
    assert AdminMapper.account_params(admin) is None
    row = {
        "employee_id": 10, "first_name": "Admin", "last_name": "", "email": "", "phone": "",
        "date_created": BASE.isoformat(), "enabled": 1, "version": 0, "job_title": "", "department_id": None,
        "account_id": None, "login": None, "password": None, "account_enabled": None, "account_date_created": None,
    }
    assert isinstance(AdminMapper.row_to_admin(row).account, NoAccount)


def test_user_mapper_roundtrip_core_and_account() -> None:
    user = User.create(
        employee_id=20,
        first_name="User",
        last_name="Name",
        client_id=100,
        login="user-login",
        password="Strong1!",
    )
    ep = UserMapper.employee_params(user)
    up = UserMapper.user_params(user)
    ap = UserMapper.account_params(user)
    assert ep["is_admin"] == 0 and up["client_id"] == 100
    assert ap is not None and ap["login"] == "user-login"
    row = {
        **ep, **up,
        "account_id": 6, "login": ap["login"], "password": ap["password"],
        "account_enabled": 1, "account_date_created": ap["date_created"],
    }
    restored = UserMapper.row_to_user(row)
    assert restored.employee_id == 20 and restored.client_id == 100
    assert str(restored.account.login) == "user-login"


def test_client_mapper_roundtrip_preserves_creator_and_version() -> None:
    client = Client.create(client_id=100, name="Acme", email="a@b.com", created_by_admin_id=10)
    client.version = 3
    params = ClientMapper.params(client)
    row = dict(params)
    restored = ClientMapper.row_to_client(row)
    assert restored.client_id == 100
    assert restored.created_by_admin_id == 10
    assert restored.version == 3
    assert str(restored.email) == "a@b.com"


def test_department_mapper_roundtrip_and_fallback_version() -> None:
    department = Department.create(department_id=3, name="Support")
    params = DepartmentMapper.params(department)
    restored = DepartmentMapper.row_to_department(params)
    assert restored == department
    params["version"] = None
    assert DepartmentMapper.row_to_department(params).version == 0


def test_role_mapper_roundtrip_and_stable_permission_serialization() -> None:
    role = Role(
        role_id=4,
        name="role",
        permissions=frozenset({AdminPermission.TICKET_VIEW, AdminPermission.ADMIN_OPERATION}),
        description="desc",
    )
    params = RoleMapper.role_params(role, is_admin=True)
    assert params["permissions"] == ",".join(sorted(p.value for p in role.permissions))
    restored = RoleMapper.row_to_role(params, AdminPermission)
    assert restored.permissions == role.permissions
    assert restored.name == role.name


def test_ticket_mapper_internal_ticket_roundtrip() -> None:
    ticket = Ticket.create(
        client_id=1,
        admin_id=10,
        user_id=20,
        contact_user_id=21,
        text_of_ticket="Need help",
        description="desc",
        department_id=3,
        is_remote=True,
        urgency_level=2,
        date_created=BASE,
    )
    ticket.ticket_id = 100
    root = TicketMapper.ticket_params(ticket)
    status = ticket.statuses[0]
    status.status_id = 11
    status_row = TicketMapper.status_record_params(ticket_id=100, record=status)
    restored_status = TicketMapper.row_to_status_record({"status_id": 11, **status_row})
    restored = TicketMapper.row_to_ticket(root, statuses=[restored_status], comments=[])
    assert restored.ticket_id == 100
    assert restored.admin_id == 10
    assert restored.contact_user_id == 21
    assert restored.current_status_record().status is TicketStatus.CREATED


def test_ticket_mapper_created_from_user_maps_zero_admin_and_actor_to_null() -> None:
    ticket = Ticket.create_from_ticket_user(
        client_id=1,
        user_id=20,
        contact_user_id=21,
        text_of_ticket="Need help",
        user_ticket_id=50,
        date_created=BASE,
    )
    ticket.ticket_id = 100
    params = TicketMapper.ticket_params(ticket)
    status_params = TicketMapper.status_record_params(ticket_id=100, record=ticket.statuses[0])
    assert params["admin_id"] is None
    assert status_params["actor_employee_id"] is None


def test_ticket_mapper_comment_roundtrip() -> None:
    comment = Comment(comment_id=7, employee_id=10, comment="text", date_created=BASE)
    params = TicketMapper.comment_params(ticket_id=100, comment=comment)
    restored = TicketMapper.row_to_comment({"ticket_comment_id": 7, **params})
    assert restored.comment_id == 7 and restored.comment == "text"


def test_ticket_user_mapper_roundtrip_status_comment_and_optional_contact() -> None:
    ticket_user = TicketUser.create(client_id=1, user_id=20, text_of_ticket="Need help", date_created=BASE)
    ticket_user.ticket_id = 50
    root = TicketUserMapper.ticket_params(ticket_user)
    assert root["contact_user_id"] is None
    record = ticket_user.statuses[0]
    record.status_id = 9
    sr = TicketUserMapper.status_record_params(ticket_id=50, record=record)
    restored_status = TicketUserMapper.row_to_status({"status_id": 9, **sr})
    restored = TicketUserMapper.row_to_ticket(root, statuses=[restored_status], comments=[])
    assert restored.ticket_id == 50
    assert restored.current_status() is TicketUserStatus.CREATED
    assert restored.statuses[0].status_comment == ""


def test_ticket_user_mapper_preserves_status_comment() -> None:
    record = StatusRecordTicketUser(
        status_id=1,
        actor_employee_id=20,
        status=TicketUserStatus.CREATED,
        status_comment="phone request",
        date_created=BASE,
    )
    params = TicketUserMapper.status_record_params(ticket_id=50, record=record)
    assert params["comment"] == "phone request"
    restored = TicketUserMapper.row_to_status({"status_id": 1, **params})
    assert restored.status_comment == "phone request"
