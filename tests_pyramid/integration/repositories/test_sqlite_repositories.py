from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from src.adapters.repositories.account import AccountRepositorySQLite
from src.adapters.repositories.admin import AdminRepositorySQLite
from src.adapters.repositories.client_repository import ClientRepositorySQLite
from src.adapters.repositories.department_repository import DepartmentRepositorySQLite
from src.adapters.repositories.exceptions import OptimisticLockError
from src.adapters.repositories.role_repository import RoleRepositorySQLite
from src.adapters.repositories.ticket_repository import TicketRepositorySQLite
from src.adapters.repositories.ticket_user_repository import TicketUserRepositorySQLite
from src.adapters.repositories.user_repository import UserRepositorySQLite
from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.exceptions import ItemNotFoundError
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.ticket import Comment, Ticket
from src.domain.ticket_user import TicketUser
from utils.db.connect import Connection

pytestmark = pytest.mark.integration

def _find_source_db() -> Path:
    candidates = [
        Path.cwd() / "db" / "admins.db",
        Path(__file__).resolve().parents[3] / "db" / "admins.db",
        Path(__file__).resolve().parents[2] / "db" / "admins.db",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Cannot find db/admins.db. Run pytest from the project root "
        "or place tests_pyramid inside the project root."
    )


SOURCE_DB = _find_source_db()


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
    path = tmp_path / "repo.sqlite3"
    shutil.copy2(SOURCE_DB, path)
    _clean_db(path)
    connection = Connection.create_connection(str(path), engine=sqlite3)
    yield connection
    connection.close()


def save_admin(conn: Connection, *, department_id: int = 0, login: str = "") -> Admin:
    admin = Admin.create(
        employee_id=0,
        first_name="Admin",
        last_name="Tester",
        department_id=department_id,
        login=login,
        password="Strong1!" if login else "",
    )
    return AdminRepositorySQLite(conn).save(admin)


def save_client(conn: Connection, *, admin_id: int = 0) -> Client:
    return ClientRepositorySQLite(conn).save(
        Client.create(client_id=0, name="Acme Client", created_by_admin_id=admin_id)
    )


def save_user(conn: Connection, *, client_id: int, login: str = "") -> User:
    return UserRepositorySQLite(conn).save(
        User.create(
            employee_id=0,
            first_name="User",
            last_name="Tester",
            client_id=client_id,
            login=login,
            password="Strong2!" if login else "",
        )
    )


def test_department_repository_crud_and_optimistic_lock(conn: Connection) -> None:
    repo = DepartmentRepositorySQLite(conn)
    saved = repo.save(Department.create(department_id=0, name="Support"))
    assert saved.department_id > 0
    loaded = repo.get(saved.department_id)
    assert str(loaded.name) == "Support"
    a = repo.get(saved.department_id)
    b = repo.get(saved.department_id)
    a.rename("Support A")
    repo.save(a)
    b.rename("Support B")
    with pytest.raises(OptimisticLockError):
        repo.save(b)
    assert repo.exists(saved.department_id)
    repo.delete(saved.department_id)
    assert not repo.exists(saved.department_id)


def test_admin_repository_roundtrip_account_department_roles(conn: Connection) -> None:
    department = DepartmentRepositorySQLite(conn).save(Department.create(department_id=0, name="Support"))
    role_repo = RoleRepositorySQLite(conn=conn, permission_cls=AdminPermission, is_admin=True)
    role = role_repo.add(Role(role_id=0, name="admin-view", permissions=frozenset({AdminPermission.TICKET_VIEW})))
    admin = Admin.create(
        employee_id=0,
        first_name="Admin",
        last_name="Tester",
        department_id=department.department_id,
        login="admin-int",
        password="Strong1!",
        roles={role.role_id},
    )
    repo = AdminRepositorySQLite(conn)
    saved = repo.save(admin)
    loaded = repo.get(saved.employee_id)
    assert loaded.employee_id == saved.employee_id
    assert loaded.department_id == department.department_id
    assert loaded.role_ids() == frozenset({role.role_id})
    assert str(loaded.account.login) == "admin-int"
    assert repo.exist_login("admin-int")
    loaded.job_title = "Engineer"
    repo.save(loaded)
    assert str(repo.get(saved.employee_id).job_title) == "Engineer"
    repo.delete(saved.employee_id)
    with pytest.raises(ItemNotFoundError):
        repo.get(saved.employee_id)


def test_client_repository_roundtrip_reference_and_optimistic_lock(conn: Connection) -> None:
    admin = save_admin(conn)
    repo = ClientRepositorySQLite(conn)
    client = repo.save(Client.create(client_id=0, name="Acme Client", created_by_admin_id=admin.employee_id))
    assert repo.has_created_by_admin(admin_id=admin.employee_id)
    assert repo.get(client.client_id).created_by_admin_id == admin.employee_id
    a = repo.get(client.client_id); b = repo.get(client.client_id)
    a.update_contact_info(name="Acme One")
    repo.save(a)
    b.update_contact_info(name="Acme Two")
    with pytest.raises(OptimisticLockError):
        repo.save(b)


def test_user_repository_roundtrip_account_roles_and_client_filter(conn: Connection) -> None:
    admin = save_admin(conn)
    client = save_client(conn, admin_id=admin.employee_id)
    role_repo = RoleRepositorySQLite(conn=conn, permission_cls=UserPermission, is_admin=False)
    role = role_repo.add(Role(role_id=0, name="user-view", permissions=frozenset({UserPermission.TICKET_VIEW})))
    user = User.create(
        employee_id=0,
        first_name="User",
        last_name="Tester",
        client_id=client.client_id,
        login="user-int",
        password="Strong2!",
        roles={role.role_id},
    )
    repo = UserRepositorySQLite(conn)
    saved = repo.save(user)
    loaded = repo.get(saved.employee_id)
    assert loaded.client_id == client.client_id
    assert loaded.role_ids() == frozenset({role.role_id})
    assert str(loaded.account.login) == "user-int"
    assert repo.exist_login("user-int")
    assert [u.employee_id for u in repo.get_all_by_client_id(client.client_id)] == [saved.employee_id]
    assert repo.does_client_exist(client.client_id)


def test_role_repository_separates_admin_and_user_realms(conn: Connection) -> None:
    admin_repo = RoleRepositorySQLite(conn=conn, permission_cls=AdminPermission, is_admin=True)
    user_repo = RoleRepositorySQLite(conn=conn, permission_cls=UserPermission, is_admin=False)
    ar = admin_repo.add(Role(role_id=0, name="ar", permissions=frozenset({AdminPermission.TICKET_VIEW})))
    ur = user_repo.add(Role(role_id=0, name="ur", permissions=frozenset({UserPermission.TICKET_VIEW})))
    assert admin_repo.get(ar.role_id).permissions == frozenset({AdminPermission.TICKET_VIEW})
    assert user_repo.get(ur.role_id).permissions == frozenset({UserPermission.TICKET_VIEW})
    assert {r.role_id for r in admin_repo.all()} == {ar.role_id}
    assert {r.role_id for r in user_repo.all()} == {ur.role_id}


def test_ticket_repository_roundtrip_append_history_comments_and_creator_semantics(conn: Connection) -> None:
    admin = save_admin(conn)
    client = save_client(conn, admin_id=admin.employee_id)
    repo = TicketRepositorySQLite(conn)
    ticket = Ticket.create(client_id=client.client_id, admin_id=admin.employee_id, text_of_ticket="Need help")
    ticket.add_comment(Comment(employee_id=admin.employee_id, comment="initial"))
    saved = repo.save(ticket)
    assert saved.ticket_id > 0 and saved.statuses[0].status_id > 0
    loaded = repo.get(saved.ticket_id)
    assert loaded.admin_id == admin.employee_id
    assert loaded.current_status_record().status.value == "created"
    assert loaded.comments[-1].comment == "initial"
    TicketManagementService.accept(ticket=loaded, actor_employee_id=admin.employee_id)
    repo.save(loaded)
    reloaded = repo.get(saved.ticket_id)
    assert [r.status.value for r in reloaded.statuses] == ["created", "accepted"]
    assert reloaded.admin_id == admin.employee_id
    assert repo.has_admin_reference(admin.employee_id)
    assert repo.does_client_exist(client.client_id)
    assert [t.ticket_id for t in repo.iter_by_client_id(client_id=client.client_id, batch_size=1)] == [saved.ticket_id]


def test_ticket_repository_created_from_user_keeps_zero_admin(conn: Connection) -> None:
    admin = save_admin(conn)
    client = save_client(conn, admin_id=admin.employee_id)
    user = save_user(conn, client_id=client.client_id)
    user_ticket = TicketUserRepositorySQLite(conn).save(
        TicketUser.create(client_id=client.client_id, user_id=user.employee_id, text_of_ticket="Phone")
    )
    repo = TicketRepositorySQLite(conn)
    ticket = repo.save(Ticket.create_from_ticket_user(
        client_id=client.client_id,
        user_id=user.employee_id,
        contact_user_id=0,
        text_of_ticket="Phone",
        user_ticket_id=user_ticket.ticket_id,
    ))
    loaded = repo.get(ticket.ticket_id)
    assert loaded.admin_id == 0
    assert loaded.statuses[0].actor_employee_id == 0
    assert repo.get_by_user_ticket_id(user_ticket.ticket_id).ticket_id == ticket.ticket_id


def test_ticket_repository_optimistic_lock(conn: Connection) -> None:
    admin = save_admin(conn); client = save_client(conn, admin_id=admin.employee_id)
    repo = TicketRepositorySQLite(conn)
    saved = repo.save(Ticket.create(client_id=client.client_id, admin_id=admin.employee_id, text_of_ticket="x"))
    a = repo.get(saved.ticket_id); b = repo.get(saved.ticket_id)
    a.update_details(actor_employee_id=admin.employee_id, description="a", contact_user_id=0, is_remote=False)
    repo.save(a)
    b.update_details(actor_employee_id=admin.employee_id, description="b", contact_user_id=0, is_remote=False)
    with pytest.raises(OptimisticLockError):
        repo.save(b)


def test_ticket_user_repository_roundtrip_append_history_comments_and_references(conn: Connection) -> None:
    admin = save_admin(conn); client = save_client(conn, admin_id=admin.employee_id); user = save_user(conn, client_id=client.client_id)
    repo = TicketUserRepositorySQLite(conn)
    tu = TicketUser.create(client_id=client.client_id, user_id=user.employee_id, text_of_ticket="Need help", comment="initial")
    saved = repo.save(tu)
    assert saved.ticket_id > 0 and saved.statuses[0].status_id > 0
    loaded = repo.get(saved.ticket_id)
    assert loaded.user_id == user.employee_id
    loaded.confirm_by_admin(actor_employee_id=admin.employee_id, comment="accepted")
    repo.save(loaded)
    reloaded = repo.get(saved.ticket_id)
    assert reloaded.current_status().value == "confirmed_by_admin"
    assert reloaded.statuses[-1].status_comment == "accepted"
    assert repo.does_client_exist(client.client_id)
    assert repo.has_admin_reference(admin.employee_id)
    assert repo.has_user_reference(user.employee_id)


def test_ticket_user_repository_optimistic_lock(conn: Connection) -> None:
    admin = save_admin(conn); client = save_client(conn, admin_id=admin.employee_id); user = save_user(conn, client_id=client.client_id)
    repo = TicketUserRepositorySQLite(conn)
    saved = repo.save(TicketUser.create(client_id=client.client_id, user_id=user.employee_id, text_of_ticket="x"))
    a = repo.get(saved.ticket_id); b = repo.get(saved.ticket_id)
    a.update_details(actor_employee_id=admin.employee_id, description="a", contact_user_id=0)
    repo.save(a)
    b.update_details(actor_employee_id=admin.employee_id, description="b", contact_user_id=0)
    with pytest.raises(OptimisticLockError):
        repo.save(b)


def test_sqlite_uow_commit_and_rollback(conn: Connection) -> None:
    uow = SQLiteUnitOfWork(conn)
    with uow:
        dep = uow.departments.save(Department.create(department_id=0, name="Committed"))
    assert DepartmentRepositorySQLite(conn).get(dep.department_id).department_id == dep.department_id

    with pytest.raises(RuntimeError):
        with uow:
            uow.departments.save(Department.create(department_id=0, name="Rolled Back"))
            raise RuntimeError("boom")
    assert all(str(d.name) != "Rolled Back" for d in DepartmentRepositorySQLite(conn).get_all())


def test_sqlite_uow_rejects_nested_context(conn: Connection) -> None:
    uow = SQLiteUnitOfWork(conn)
    with uow:
        with pytest.raises(RuntimeError, match="Cannot nest"):
            with uow:
                pass


def test_account_repository_reads_updates_and_deletes_employee_account(conn: Connection) -> None:
    admin = save_admin(conn, login="account-int")
    repo = AccountRepositorySQLite(conn)

    account = repo.get_employee_id(admin.employee_id)
    assert account.account_id > 0
    assert str(account.login) == "account-int"
    assert repo.exists(account.account_id)
    assert repo.find_by_login("account-int") == admin.employee_id
    assert repo.does_login_exist("account-int")
    assert repo.account_is_enabled_by_login("account-int")

    account.disable()
    repo.save(account, employee_id=admin.employee_id)
    assert not repo.get(account.account_id).enabled

    repo.delete(admin.employee_id)
    assert not repo.exists(account.account_id)


def test_account_repository_returns_no_account_for_employee_without_account(conn: Connection) -> None:
    admin = save_admin(conn, login="")
    repo = AccountRepositorySQLite(conn)
    assert not bool(repo.get_employee_id(admin.employee_id))
