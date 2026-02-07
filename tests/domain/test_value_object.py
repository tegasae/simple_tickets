"""Tests for value objects."""

import pytest
from src.domain.value_objects import (
    Email,
    Address,
    Phone,
    Name,
    Login,
    Password,
    hash_password,
    verify_password
)


class TestEmail:
    """Tests for Email value object."""

    def test_valid_email(self):
        """Test valid email addresses."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"

        email2 = Email("  TEST@EXAMPLE.COM  ")
        assert email2.value == "test@example.com"  # Normalized to lowercase

        email3 = Email("")
        assert email3.value == ""

    def test_invalid_email(self):
        """Test invalid email addresses."""
        with pytest.raises(ValueError, match="cannot be only whitespace"):
            Email("   ")

        with pytest.raises(ValueError, match="Invalid email format"):
            Email("invalid-email")

        with pytest.raises(ValueError, match="Invalid email format"):
            Email("test@")

        with pytest.raises(ValueError, match="Invalid email format"):
            Email("@example.com")

    def test_email_comparison(self):
        """Test email comparison and ordering."""
        email1 = Email("a@example.com")
        email2 = Email("b@example.com")
        email3 = Email("a@example.com")

        assert email1 < email2
        assert email1 == email3
        assert email2 > email1

        emails = [email2, email1]
        assert sorted(emails) == [email1, email2]


class TestAddress:
    """Tests for Address value object."""

    def test_valid_address(self):
        """Test valid addresses."""
        address = Address("123 Main St")
        assert address.value == "123 Main St"

        address2 = Address("  123 Main St  ")
        assert address2.value == "123 Main St"

        address3 = Address("")
        assert address3.value == ""

    def test_invalid_address(self):
        """Test invalid addresses."""
        with pytest.raises(ValueError, match="cannot be only whitespace"):
            Address("   ")


class TestPhone:
    """Tests for Phone value object."""

    def test_valid_phone(self):
        """Test valid phone numbers."""
        phone = Phone("+1 234 567 8900")
        assert phone.value == "+1 234 567 8900"

        phone2 = Phone("  +1 234 567 8900  ")
        assert phone2.value == "+1 234 567 8900"

        phone3 = Phone("")
        assert phone3.value == ""

    def test_invalid_phone(self):
        """Test invalid phone numbers."""
        with pytest.raises(ValueError, match="cannot be only whitespace"):
            Phone("   ")


class TestName:
    """Tests for Name value object."""

    def test_valid_name(self):
        """Test valid names."""
        name = Name("John Doe")
        assert name.value == "John Doe"

        name2 = Name("  John Doe  ")
        assert name2.value == "John Doe"

        name3 = Name("Jo")  # Minimum length
        assert name3.value == "Jo"

    def test_invalid_name(self):
        """Test invalid names."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Name("")

        with pytest.raises(ValueError, match="Login cannot be empty or only whitespace"):
            Name("   ")

        with pytest.raises(ValueError, match="at least 2 characters"):
            Name("J")

        with pytest.raises(ValueError, match="cannot exceed 100 characters"):
            Name("A" * 101)


class TestLogin:
    """Tests for Login value object."""

    def test_valid_login(self):
        """Test valid logins."""
        login = Login("johndoe")
        assert login.value == "johndoe"

        login2 = Login("  johndoe  ")
        assert login2.value == "johndoe"

        login3 = Login("jd")  # Minimum length
        assert login3.value == "jd"

    def test_invalid_login(self):
        """Test invalid logins."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Login("")

        with pytest.raises(ValueError, match="Login cannot be empty or only whitespace"):
            Login("   ")

        with pytest.raises(ValueError, match="at least 2 characters"):
            Login("j")

        with pytest.raises(ValueError, match="cannot exceed 100 characters"):
            Login("a" * 101)

        with pytest.raises(ValueError, match="cannot contain spaces"):
            Login("john doe")


class TestPassword:
    """Tests for Password value object."""

    def test_password_from_plain(self):
        """Test creating password from plain text."""
        password = Password.from_plain("ValidPass123!")
        assert password.value is not None
        assert password.value != "ValidPass123!"  # Should be hashed

        # Verify the password
        assert password.verify("ValidPass123!") is True
        assert password.verify("wrongpassword") is False

    def test_password_from_hash(self):
        """Test creating password from hash."""
        hash_value = hash_password("ValidPass123!")
        password = Password.from_hash(hash_value)

        assert password.value == hash_value
        assert password.verify("ValidPass123!") is True

    def test_invalid_passwords(self):
        """Test invalid password creation."""
        # Too short
        with pytest.raises(ValueError, match="at least 8 characters"):
            Password.from_plain("Short1!")

        # Too long
        with pytest.raises(ValueError, match="cannot exceed 128 characters"):
            Password.from_plain("A" * 129 + "1!")

        # No uppercase
        with pytest.raises(ValueError, match="uppercase letter"):
            Password.from_plain("nouppercase123!")

        # No lowercase
        with pytest.raises(ValueError, match="lowercase letter"):
            Password.from_plain("NOLOWERCASE123!")

        # No digit (using r"\d" now fixed)
        with pytest.raises(ValueError, match="digit"):
            Password.from_plain("NoDigitPass!")

        # No special character (using r"\W" now fixed)
        with pytest.raises(ValueError, match="special character"):
            Password.from_plain("NoSpecial123")

        # Contains whitespace
        with pytest.raises(ValueError, match="cannot contain whitespace"):
            Password.from_plain("Pass 123!")

        # Empty
        with pytest.raises(ValueError, match="cannot be empty"):
            Password.from_plain("")

        # None
        with pytest.raises(ValueError, match="cannot be None"):
            Password.from_plain(None)  # type: ignore

        # Wrong type
        with pytest.raises(TypeError, match="must be a string"):
            Password.from_plain(123)  # type: ignore

    def test_empty_hash(self):
        """Test creating password from empty hash."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Password.from_hash("")

    def test_password_repr(self):
        """Test password representation doesn't reveal hash."""
        password = Password.from_plain("ValidPass123!")

        assert "**hidden**" in str(password)
        assert "**hidden**" in repr(password)
        assert password.value not in repr(password)
        assert password.value not in str(password)


def test_hash_password():
    """Test password hashing function."""
    plain = "test123"
    hash1 = hash_password(plain)
    hash2 = hash_password(plain)

    # Same input should produce same hash
    assert hash1 == hash2

    # Hash should be different from plain text
    assert hash1 != plain

    # Hash should be hex string
    assert len(hash1) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in hash1)


def test_verify_password():
    """Test password verification function."""
    plain = "test123"
    hashed = hash_password(plain)

    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False