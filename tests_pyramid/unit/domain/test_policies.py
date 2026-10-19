from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.domain.account import NoAccount
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.policies.admin import AdminPolicy
from src.domain.policies.client import ClientPolicy
from src.domain.policies.department import DepartmentPolicy
from src.domain.policies.ticket import TicketPolicy
from src.domain.policies.ticket_user_ticket import TicketUserTicketPolicy
from src.domain.policies.user import UserPolicy

pytestmark = pytest.mark.unit


def make_admin(*, enabled=True, account=True) -> Admin:
    admin = Admin.create(
        employee_id=1,
        first_name="Admin",
        login="admin" if account else "",
        password="Strong1!" if account else "",
    )
    admin.enabled = enabled
    return admin


def make_user(*, client_id=10, enabled=True, account=True) -> User:
    user = User.create(
        employee_id=2,
        first_name="User",
        client_id=client_id,
        login="user" if account else "",
        password="Strong1!" if account else "",
    )
    user.enabled = enabled
    return user


def test_admin_policy_login_success_and_failure() -> None:
    admin = make_admin()
    AdminPolicy.ensure_can_login(admin, "Strong1!")
    AdminPolicy.ensure_login_is_still_valid(admin)

    with pytest.raises(DomainOperationError):
        AdminPolicy.ensure_can_login(admin, "Wrong1!")

    admin.disable()
    with pytest.raises(DomainOperationError):
        AdminPolicy.ensure_login_is_still_valid(admin)


def test_admin_policy_rejects_no_account() -> None:
    admin = make_admin(account=False)
    assert isinstance(admin.account, NoAccount)
    with pytest.raises(DomainOperationError):
        AdminPolicy.ensure_can_login(admin, "Strong1!")


def test_user_policy_requires_enabled_user_account_and_client() -> None:
    client = Client.create(client_id=10, name="Client")
    user = make_user(client_id=10)
    UserPolicy.ensure_can_login(user, client, "Strong1!")
    UserPolicy.ensure_login_is_still_valid(user, client)

    client.disable()
    with pytest.raises(DomainOperationError):
        UserPolicy.ensure_can_login(user, client, "Strong1!")
    with pytest.raises(DomainOperationError):
        UserPolicy.ensure_login_is_still_valid(user, client)


def test_client_policy_allows_delete_without_references() -> None:
    client = Client.create(client_id=10, name="Client")
    ClientPolicy.ensure_can_delete(
        client=client,
        has_users=False,
        has_tickets=False,
        has_user_tickets=False,
    )


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"has_users": True, "has_tickets": False, "has_user_tickets": False}, "users"),
        ({"has_users": False, "has_tickets": True, "has_user_tickets": False}, "tickets"),
        ({"has_users": False, "has_tickets": False, "has_user_tickets": True}, "user tickets"),
    ],
)
def test_client_policy_rejects_delete_when_referenced(kwargs, match: str) -> None:
    client = Client.create(client_id=10, name="Client")
    with pytest.raises(DomainOperationError, match=match):
        ClientPolicy.ensure_can_delete(client=client, **kwargs)


def test_department_policy_disables_if_no_enabled_admins() -> None:
    department = Department.create(department_id=1, name="Support")
    disabled_admin = make_admin(enabled=False)
    DepartmentPolicy.ensure_can_disable(
        department=department,
        admins=[disabled_admin],
    )
    assert department.enabled is False


def test_department_policy_rejects_enabled_admin_reference() -> None:
    department = Department.create(department_id=1, name="Support")
    with pytest.raises(DomainOperationError):
        DepartmentPolicy.ensure_can_disable(
            department=department,
            admins=[make_admin(enabled=True)],
        )
    assert department.enabled is True


def test_ticket_policy_enabled_checks() -> None:
    client = Client.create(client_id=10, name="Client", enabled=False)
    admin = make_admin(enabled=False)
    user = make_user(enabled=False)
    for fn, arg in [
        (TicketPolicy.ensure_client_enabled, client),
        (TicketPolicy.ensure_admin_enabled, admin),
        (TicketPolicy.ensure_user_enabled, user),
    ]:
        with pytest.raises(DomainOperationError):
            fn(arg)


def test_ticket_policy_user_and_contact_must_belong_to_client() -> None:
    client = Client.create(client_id=10, name="Client")
    user = make_user(client_id=10)
    TicketPolicy.ensure_user_belongs_to_client(user=user, client=client)
    TicketPolicy.ensure_contact_user_belongs_to_client(contact_user=user, client=client)
    outsider = make_user(client_id=11)
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_user_belongs_to_client(user=outsider, client=client)
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_contact_user_belongs_to_client(contact_user=outsider, client=client)


def test_ticket_policy_link_and_matching_fields() -> None:
    ticket = SimpleNamespace(
        ticket_id=1,
        user_ticket_id=100,
        client_id=10,
        user_id=20,
        contact_user_id=30,
    )
    ticket_user = SimpleNamespace(
        ticket_id=100,
        client_id=10,
        user_id=20,
        contact_user_id=30,
    )
    TicketPolicy.ensure_ticket_matches_ticket_user(ticket=ticket, ticket_user=ticket_user)

    for field, value in [("client_id", 11), ("user_id", 21), ("contact_user_id", 31)]:
        bad = SimpleNamespace(**ticket_user.__dict__)
        setattr(bad, field, value)
        with pytest.raises(DomainOperationError):
            TicketPolicy.ensure_ticket_matches_ticket_user(ticket=ticket, ticket_user=bad)

    bad_link = SimpleNamespace(**ticket.__dict__)
    bad_link.user_ticket_id = 101
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_matches_ticket_user(ticket=bad_link, ticket_user=ticket_user)


def test_ticket_policy_has_or_has_no_ticket_user() -> None:
    linked = SimpleNamespace(ticket_id=1, user_ticket_id=2)
    plain = SimpleNamespace(ticket_id=1, user_ticket_id=0)
    TicketPolicy.ensure_ticket_has_ticket_user(ticket=linked)
    TicketPolicy.ensure_ticket_has_no_ticket_user(ticket=plain)
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_has_ticket_user(ticket=plain)
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_has_no_ticket_user(ticket=linked)


def test_ticket_policy_identity_helpers() -> None:
    user = SimpleNamespace(employee_id=10)
    contact = SimpleNamespace(employee_id=20)
    ticket = SimpleNamespace(ticket_id=1, user_id=10, contact_user_id=20)
    ticket_user = SimpleNamespace(ticket_id=2, user_id=10, contact_user_id=20)
    TicketPolicy.ensure_user_matches_ticket(user=user, ticket=ticket)
    TicketPolicy.ensure_user_matches_ticket_user(user=user, ticket_user=ticket_user)
    TicketPolicy.ensure_contact_user_matches_ticket(contact_user=contact, ticket=ticket)
    TicketPolicy.ensure_contact_user_matches_ticket_user(contact_user=contact, ticket_user=ticket_user)


def test_ticket_user_ticket_policy_delete_rejects_linked_ticket() -> None:
    user_ticket = SimpleNamespace(ticket_id=1)
    ticket = SimpleNamespace(ticket_id=2)
    with pytest.raises(DomainOperationError):
        TicketUserTicketPolicy.can_delete_user_ticket(user_ticket, ticket)
    TicketUserTicketPolicy.can_delete_user_ticket(user_ticket, None)
