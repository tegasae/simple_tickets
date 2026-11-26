"""Synthetic regressions for role assignment SQL and new UTC timestamps."""
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta, timezone

import pytest

from conftest import database_uow
from src.domain.account import Account
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role


@contextmanager
def local_timezone(value):
    """Exercise non-UTC hosts without changing the calling process permanently."""
    if not hasattr(time, "tzset"):
        pytest.skip("These timezone regressions require time.tzset")
    previous = os.environ.get("TZ")
    os.environ["TZ"] = value
    time.tzset()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        time.tzset()


@pytest.mark.parametrize("assignment", ["none", "admin", "user"])
def test_role_assignment_predicate_checks_both_assignment_tables(world, assignment):
    with database_uow(world.path) as uow:
        is_admin = assignment != "user"
        repository = uow.roles_admin if is_admin else uow.roles_user
        permission = AdminPermission.ADMIN_VIEW if is_admin else UserPermission.TICKET_VIEW
        role = repository.save(Role.create(
            name="Synthetic isolated role " + assignment,
            permissions=frozenset({permission}),
        ))
        if assignment != "none":
            table, employee_id = (
                ("admins_roles", world.admin_id) if is_admin
                else ("users_roles", world.user_id)
            )
            # table comes only from the fixed choices above; all values are bound.
            uow.connection.connect.execute(
                f"INSERT INTO {table} (employee_id, role_id) VALUES (?, ?)",
                (employee_id, role.role_id),
            )
        role_id = role.role_id
    # Verify the persisted result using a fresh transaction.
    with database_uow(world.path) as uow:
        repository = uow.roles_admin if is_admin else uow.roles_user
        assert repository.is_assigned(role_id) is (assignment != "none")


@pytest.mark.parametrize("entity", ["department", "admin", "user", "account"])
def test_new_entity_dates_are_aware_utc_on_non_utc_host(world, entity):
    with local_timezone("UTC-3"):
        before = datetime.now(UTC)
        if entity == "department":
            value = Department.create(name="Synthetic clock department")
        elif entity == "admin":
            value = Admin.create(first_name="Synthetic clock admin")
        elif entity == "user":
            value = User.create(first_name="Synthetic clock user", client_id=world.client_id)
        else:
            value = Account.create(
                account_id=0, login="synthetic-clock", plain_password=world.password, enabled=True,
            )
        after = datetime.now(UTC)
        assert value.date_created.tzinfo is UTC
        assert before <= value.date_created <= after


@pytest.mark.parametrize("local_zone", ["UTC0", "UTC-3"])
def test_new_employee_account_and_department_dates_keep_their_instant(world, local_zone):
    with local_timezone(local_zone):
        before = datetime.now(UTC)
        with database_uow(world.path) as uow:
            department = uow.departments.save(Department.create(name="Synthetic roundtrip clock"))
            admin = uow.admins.save(Admin.create(
                first_name="Synthetic roundtrip admin", department_id=department.department_id,
                login="synthetic-roundtrip-admin", password=world.password,
            ))
            user = uow.users.save(User.create(
                first_name="Synthetic roundtrip user", client_id=world.client_id,
                login="synthetic-roundtrip-user", password=world.password,
            ))
        after = datetime.now(UTC)
        with database_uow(world.path) as uow:
            restored = (
                uow.departments.get(department.department_id),
                uow.admins.get(admin.employee_id), uow.users.get(user.employee_id),
            )
            dates = [value.date_created for value in restored]
            dates += [value.account.date_created for value in restored[1:]]
        for created_at in dates:
            assert created_at.tzinfo is UTC
            assert before <= created_at <= after


@pytest.mark.parametrize("local_zone", ["UTC0", "UTC-3"])
def test_department_create_and_get_expose_the_same_aware_instant(world, local_zone):
    with local_timezone(local_zone):
        before = datetime.now(UTC)
        response = world.client.post(
            "/admin/departments/", headers=world.admin_headers,
            json={"name": "Synthetic HTTP clock"},
        )
        assert response.status_code == 201
        created = response.json()
        loaded = world.client.get(
            f"/admin/departments/{created['department_id']}", headers=world.admin_headers,
        )
        assert loaded.status_code == 200
        dates = [datetime.fromisoformat(value["date_created"]) for value in (created, loaded.json())]
        assert all(value.tzinfo is UTC for value in dates)
        assert dates[0] == dates[1]
        assert before <= dates[0] <= datetime.now(UTC)


@pytest.mark.parametrize("existing", [
    datetime(2020, 2, 3, 4, 5),
    datetime(2020, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=3))),
])
def test_rehydration_preserves_explicit_historical_timestamps(world, existing):
    restored = [
        Department.rehydrate(
            department_id=1, name="Synthetic old department", enabled=True,
            date_created=existing, version=0,
        ),
        Admin.rehydrate(employee_id=1, first_name="Synthetic old admin", version=0, date_created=existing),
        User.rehydrate(
            employee_id=2, first_name="Synthetic old user", client_id=world.client_id,
            version=0, date_created=existing,
        ),
        Account.rehydrate(
            account_id=1, login="synthetic-old", password_hash="synthetic-placeholder-hash",
            date_created=existing,
        ),
    ]
    assert all(value.date_created is existing for value in restored)


def test_account_rehydrate_without_a_date_generates_aware_utc():
    before = datetime.now(UTC)
    account = Account.rehydrate(
        account_id=1, login="synthetic-no-date", password_hash="synthetic-placeholder-hash",
    )
    assert account.date_created.tzinfo is UTC
    assert before <= account.date_created <= datetime.now(UTC)


def test_creating_new_entities_does_not_rewrite_historical_database_dates(world):
    historical = "2020-02-03T04:05:00"
    with database_uow(world.path) as uow:
        uow.connection.connect.execute(
            "UPDATE departments SET date_created = ? WHERE department_id = ?",
            (historical, world.department_id),
        )
    with database_uow(world.path) as uow:
        uow.departments.save(Department.create(name="Synthetic unrelated new department"))
    with database_uow(world.path) as uow:
        raw = uow.connection.connect.execute(
            "SELECT date_created FROM departments WHERE department_id = ?", (world.department_id,),
        ).fetchone()[0]
    assert raw == historical
