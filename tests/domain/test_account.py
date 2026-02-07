"""Tests for Account domain model."""

import pytest
from datetime import datetime


from src.domain.account import Account, NoAccount, AccountType
from src.domain.value_objects import Login, Password


class TestAccount:
    """Tests for Account entity."""

    def test_account_creation(self):
        """Test creating a new account."""
        account = Account.create(
            account_id=1,
            login="john_doe",
            plain_password="ValidPass123!"
        )

        assert account.account_id == 1
        assert account.login == Login("john_doe")
        assert account.enabled is True
        assert isinstance(account.date_created, datetime)

        # Password should be verified
        assert account.verify_password("ValidPass123!") is True
        assert account.verify_password("wrong") is False

    def test_account_from_database(self):
        """Test reconstructing account from database."""
        password_hash = Password.from_plain("ValidPass123!").value
        fixed_date = datetime(2024, 1, 1, 12, 0, 0)

        account = Account.from_database(
            account_id=1,
            login="john_doe",
            password_hash=password_hash,
            enabled=False,
            date_created=fixed_date
        )

        assert account.account_id == 1
        assert account.login == Login("john_doe")
        assert account.enabled is False
        assert account.date_created == fixed_date
        assert account.verify_password("ValidPass123!") is True

    def test_account_from_database_defaults(self):
        """Test from_database with defaults."""
        password_hash = Password.from_plain("ValidPass123!").value

        account = Account.from_database(
            account_id=1,
            login="john_doe",
            password_hash=password_hash,
        )

        assert account.enabled is True  # Default
        assert isinstance(account.date_created, datetime)  # Current time

    def test_disable_and_enable(self):
        """Test disabling and enabling accounts."""
        account = Account.create(
            account_id=1,
            login="john_doe",
            plain_password="ValidPass123!"
        )

        assert account.enabled is True

        account.disable()
        assert account.enabled is False

        account.enable()
        assert account.enabled is True

    def test_account_equality(self):
        """Test account equality based on account_id."""
        account1 = Account.create(1, "user1", "Pass123!")
        account2 = Account.create(1, "user1", "Pass123!")
        account3 = Account.create(2, "user2", "Pass456!")

        assert account1 == account2
        assert account1 != account3
        assert account1 != "not an account"

    def test_account_hash(self):
        """Test account hashing."""
        account1 = Account.create(1, "user1", "Pass123!")
        account2 = Account.create(1, "user1", "Pass123!")
        account3 = Account.create(2, "user2", "Pass456!")

        # Same ID should give same hash
        assert hash(account1) == hash(account2)
        assert hash(account1) != hash(account3)

        # Can be used in sets
        accounts_set = {account1, account2, account3}
        assert len(accounts_set) == 2  # account1 and account2 are equal

    def test_account_string_representations(self):
        """Test account string representations."""
        account = Account.create(1, "john_doe", "Pass123!")

        # str() for display
        assert "Account(id=1" in str(account)
        assert "john_doe" in str(account)

        # repr() for debugging
        assert "Account(" in repr(account)
        assert "account_id=1" in repr(account)
        assert "login=Login" in repr(account)


class TestNoAccount:
    """Tests for NoAccount null object."""

    def test_no_account_properties(self):
        """Test NoAccount properties."""
        no_account = NoAccount()

        assert no_account.account_id == -1
        assert no_account.login == "<no-account>"
        assert no_account.enabled is False
        assert no_account.date_created == datetime.min

    def test_no_account_verification(self):
        """Test password verification always fails."""
        no_account = NoAccount()

        assert no_account.verify_password("anything") is False
        assert no_account.verify_password("") is False

    def test_no_account_truthiness(self):
        """Test NoAccount is falsy."""
        no_account = NoAccount()

        assert bool(no_account) is False
        if no_account:  # Should not execute
            pytest.fail("NoAccount should be falsy")

    def test_no_account_string_representations(self):
        """Test NoAccount string representations."""
        no_account = NoAccount()

        assert str(no_account) == "<no-account>"
        assert repr(no_account) == "NoAccount()"


class TestAccountType:
    """Tests for Account type union."""

    def test_account_type_union(self):
        """Test that AccountType accepts both Account and NoAccount."""

        def process_account(account: AccountType) -> bool:
            return bool(account)

        real_account = Account.create(1, "user", "Pass123!")
        no_account = NoAccount()

        # Both should be accepted
        assert process_account(real_account) is True
        assert process_account(no_account) is False

    def test_pattern_matching(self):
        """Test pattern matching with AccountType."""

        def describe_account(account: AccountType) -> str:
            match account:
                case Account(account_id=id_):
                    return f"Real account {id_}"
                case NoAccount():
                    return "No account"
                case _:
                    return "Unknown"

        real_account = Account.create(1, "user", "Pass123!")
        no_account = NoAccount()

        assert describe_account(real_account) == "Real account 1"
        assert describe_account(no_account) == "No account"


def test_account_creation_validation():
    """Test that account creation validates login and password."""
    # Invalid login (too short)
    with pytest.raises(ValueError):
        Account.create(1, "a", "ValidPass123!")

    # Invalid password
    with pytest.raises(ValueError):
        Account.create(1, "validuser", "short")


