from __future__ import annotations

import pytest

from src.domain.account import Account, NoAccount
from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import ItemValidationError
from src.domain.value_objects import Address, Email, Empty, Login, Name, Password, Phone


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" USER@Example.COM ", "user@example.com"),
        ("user.name+tag@example.co.uk", "user.name+tag@example.co.uk"),
    ],
)
def test_email_normalizes_valid_values(value, expected):
    assert str(Email(value)) == expected


@pytest.mark.parametrize("value", ["bad-email", "@example.com", "user@", "   "])
def test_email_rejects_invalid_or_blank_values(value):
    with pytest.raises(ValueError):
        Email(value)


def test_empty_value_object_is_always_empty():
    assert str(Empty("anything")) == ""
    assert Empty().value == ""


@pytest.mark.parametrize("cls", [Name, Login])
def test_name_and_login_strip_values(cls):
    assert str(cls("  Alice  ")) == "Alice"


@pytest.mark.parametrize("value", ["", " ", "a"])
def test_name_rejects_too_short_or_blank_values(value):
    with pytest.raises(ValueError):
        Name(value)


def test_login_rejects_spaces():
    with pytest.raises(ValueError, match="spaces"):
        Login("bad login")


@pytest.mark.parametrize("cls", [Address, Phone])
def test_optional_text_value_objects_strip_values(cls):
    assert str(cls("  Some value  ")) == "Some value"


@pytest.mark.parametrize("cls", [Address, Phone])
def test_optional_text_value_objects_reject_whitespace_only(cls):
    with pytest.raises(ValueError):
        cls("   ")


def test_password_hashes_plain_value_and_verifies_it():
    password = Password.from_plain("Strong1!")

    assert password.value != "Strong1!"
    assert password.verify("Strong1!") is True
    assert password.verify("Wrong1!") is False
    assert str(password) == "**hidden**"


@pytest.mark.parametrize(
    "plain",
    [
        "short1!",
        "nouppercase1!",
        "NOLOWERCASE1!",
        "NoDigit!",
        "NoSpecial1",
        "With Space1!",
    ],
)
def test_password_rejects_weak_plain_values(plain):
    with pytest.raises(ValueError):
        Password.from_plain(plain)


def test_account_create_verify_change_password_and_enable_disable():
    account = Account.create(account_id=1, login="admin", plain_password="Strong1!", enabled=True)

    assert str(account.login) == "admin"
    assert account.verify_password("Strong1!") is True

    account.change_password(plain_password="Better1!")
    assert account.verify_password("Strong1!") is False
    assert account.verify_password("Better1!") is True

    account.disable()
    assert account.enabled is False
    account.enable()
    assert account.enabled is True


def test_account_from_database_uses_existing_hash():
    password = Password.from_plain("Strong1!")
    account = Account.from_database(
        account_id=1,
        login="admin",
        password_hash=password.value,
        enabled=False,
    )

    assert account.enabled is False
    assert account.verify_password("Strong1!") is True


def test_no_account_is_false_and_never_verifies_password():
    account = NoAccount()

    assert bool(account) is False
    assert account.verify_password("Strong1!") is False
    assert account.login == "<no-account>"


def test_client_create_update_enable_disable_and_summary():
    client = Client.create(
        client_id=1,
        name="ACME",
        email="INFO@ACME.COM",
        address="  Main Street  ",
        phone=" 123 ",
        created_by_admin_id=10,
    )

    assert str(client.name) == "ACME"
    assert str(client.email) == "info@acme.com"
    assert str(client.address) == "Main Street"
    assert str(client.phone) == "123"

    client.update_contact_info(email="support@acme.com", address="New Street", phone="456")
    assert client.get_contact_summary() == {
        "name": "ACME",
        "email": "support@acme.com",
        "address": "New Street",
        "phone": "456",
    }

    client.disable()
    assert client.enabled is False
    client.enable()
    assert client.enabled is True


def test_client_rejects_negative_created_by_admin_id():
    with pytest.raises(ItemValidationError, match="Admin ID cannot be negative"):
        Client.create(client_id=1, name="ACME", created_by_admin_id=-1)


def test_admin_create_update_account_and_roles():
    admin = Admin.create(
        employee_id=1,
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        login="alice",
        password="Strong1!",
        job_title="Support",
        roles=frozenset({1}),
    )

    assert admin.role_ids() == frozenset({1})
    assert admin.account.verify_password("Strong1!") is True

    admin.update(
        job_title="Lead Support",
        first_name="Alicia",
        last_name=None,
        email=None,
        phone="555",
    )

    assert str(admin.first_name) == "Alicia"
    assert admin.job_title == "Lead Support"
    assert str(admin.phone) == "555"

    admin.grant_role(2)
    assert admin.role_ids() == frozenset({1, 2})
    admin.revoke_role(1)
    assert admin.role_ids() == frozenset({2})

    admin.disable()
    assert admin.enabled is False
    assert admin.account.enabled is False

    admin.remove_account()
    assert isinstance(admin.account, NoAccount)


def test_user_create_update_and_client_association(client):
    user = User.create(
        employee_id=10,
        first_name="Charlie",
        client_id=client.client_id,
        email="charlie@example.com",
    )

    assert user.client_id == client.client_id
    assert isinstance(user.account, NoAccount)

    user.update(first_name="Charles", last_name="Brown", email=None, phone=None)
    assert str(user.first_name) == "Charles"
    assert str(user.last_name) == "Brown"
