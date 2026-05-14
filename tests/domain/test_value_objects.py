import pytest

from src.domain.value_objects import Address, Email, Empty, Login, Name, Phone


def test_email_normalizes_to_lowercase():
    assert str(Email(" USER@Example.COM ")) == "user@example.com"


@pytest.mark.parametrize("bad_email", ["not-email", "   "])
def test_email_rejects_invalid_values(bad_email):
    with pytest.raises(ValueError):
        Email(bad_email)


def test_empty_is_always_empty_string():
    assert str(Empty("ignored")) == ""


def test_name_strips_spaces_and_rejects_short_values():
    assert str(Name(" Alice ")) == "Alice"
    with pytest.raises(ValueError):
        Name("A")


def test_login_rejects_spaces():
    with pytest.raises(ValueError):
        Login("bad login")


def test_phone_and_address_strip_spaces():
    assert str(Phone(" +123 ")) == "+123"
    assert str(Address(" Main street ")) == "Main street"
