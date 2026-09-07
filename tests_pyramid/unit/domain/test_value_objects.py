from __future__ import annotations

import pytest

from src.domain.value_objects import (
    Address,
    Description,
    Email,
    Empty,
    Login,
    Name,
    Password,
    Phone,
    hash_password,
    verify_password,
)

pytestmark = pytest.mark.unit


def test_empty_always_normalizes_to_empty_string() -> None:
    assert str(Empty("ignored")) == ""


def test_email_is_trimmed_and_lowercased() -> None:
    assert str(Email("  Foo.Bar@Example.COM ")) == "foo.bar@example.com"


@pytest.mark.parametrize("value", [" ", "abc", "a@b", "a@@b.com"])
def test_email_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        Email(value)


def test_address_and_phone_trim_whitespace() -> None:
    assert str(Address("  Main street  ")) == "Main street"
    assert str(Phone(" +1 555 123 ")) == "+1 555 123"


@pytest.mark.parametrize("factory", [Address, Phone])
def test_optional_text_rejects_whitespace_only(factory) -> None:
    with pytest.raises(ValueError):
        factory("   ")


def test_name_normalizes_and_validates_length() -> None:
    assert str(Name("  John  ")) == "John"
    with pytest.raises(ValueError):
        Name("A")
    with pytest.raises(ValueError):
        Name("x" * 101)


def test_description_validates_length() -> None:
    assert str(Description("  ok  ")) == "ok"
    with pytest.raises(ValueError):
        Description("")
    with pytest.raises(ValueError):
        Description("x" * 1001)


def test_login_trims_and_rejects_spaces() -> None:
    assert str(Login("  admin  ")) == "admin"
    with pytest.raises(ValueError):
        Login("a b")
    with pytest.raises(ValueError):
        Login("a")


def test_password_hash_helpers_are_consistent() -> None:
    digest = hash_password("Strong1!")
    assert len(digest) == 64
    assert verify_password("Strong1!", digest)
    assert not verify_password("Wrong1!", digest)


@pytest.mark.parametrize(
    "plain",
    [
        "short1!A"[:7],
        "lowercase1!",
        "UPPERCASE1!",
        "NoDigits!",
        "NoSpecial1",
        "Has space1!A",
    ],
)
def test_password_rejects_invalid_plain_passwords(plain: str) -> None:
    with pytest.raises((ValueError, TypeError)):
        Password.from_plain(plain)


def test_password_from_plain_hashes_and_verifies_without_leaking_value() -> None:
    password = Password.from_plain("Strong1!")
    assert password.value != "Strong1!"
    assert password.verify("Strong1!")
    assert not password.verify("Strong2!")
    assert str(password) == "**hidden**"
    assert "hidden" in repr(password)


def test_password_from_hash_requires_nonempty_hash() -> None:
    with pytest.raises(ValueError):
        Password.from_hash("")
    assert Password.from_hash("abc").value == "abc"
