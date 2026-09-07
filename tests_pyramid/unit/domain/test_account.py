from __future__ import annotations

from datetime import datetime

import pytest

from src.domain.account import Account, NoAccount

pytestmark = pytest.mark.unit


def test_account_create_hashes_password_and_verifies_it() -> None:
    account = Account.create(
        account_id=1,
        login="admin",
        plain_password="Strong1!",
        enabled=True,
    )
    assert str(account.login) == "admin"
    assert account.verify_password("Strong1!")
    assert not account.verify_password("Wrong1!")


def test_account_change_password_replaces_credentials() -> None:
    account = Account.create(1, "admin", "Strong1!", True)
    account.change_password(plain_password="Better2!")
    assert not account.verify_password("Strong1!")
    assert account.verify_password("Better2!")


def test_account_enable_disable() -> None:
    account = Account.create(1, "admin", "Strong1!", True)
    account.disable()
    assert account.enabled is False
    account.enable()
    assert account.enabled is True


def test_account_from_database_preserves_hash_and_date() -> None:
    original = Account.create(1, "admin", "Strong1!", True)
    created = datetime(2025, 1, 1)
    restored = Account.from_database(
        account_id=1,
        login="admin",
        password_hash=original.password.value,
        enabled=False,
        date_created=created,
    )
    assert restored.verify_password("Strong1!")
    assert restored.enabled is False
    assert restored.date_created == created


def test_account_identity_is_account_id() -> None:
    a = Account.create(1, "admin", "Strong1!", True)
    b = Account.create(1, "other", "Strong2!", True)
    c = Account.create(2, "third", "Strong3!", True)
    assert a == b
    assert a != c
    assert hash(a) == hash(b)


def test_no_account_is_false_and_never_verifies_password() -> None:
    account = NoAccount()
    assert not account
    assert account.login == ""
    assert account.enabled is False
    assert account.verify_password("anything") is False
    account.enable()
    account.disable()
    assert account.enabled is False
