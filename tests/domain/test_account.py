from src.domain.account import Account, NoAccount


def test_account_create_hashes_and_verifies_password():
    account = Account.create(account_id=1, login="john", plain_password="Secret123!", enabled=True)

    assert str(account.login) == "john"
    assert account.password.value != "Secret123!"
    assert account.verify_password("Secret123!") is True
    assert account.verify_password("wrong") is False


def test_account_from_database_keeps_hash_verification():
    account = Account.create(account_id=1, login="john", plain_password="Secret123!", enabled=True)
    restored = Account.from_database(
        account_id=1,
        login="john",
        password_hash=account.password.value,
        enabled=True,
    )

    assert restored.verify_password("Secret123!") is True


def test_no_account_is_false_and_never_authenticates():
    account = NoAccount()

    assert bool(account) is False
    assert account.verify_password("anything") is False
    assert str(account.login) == ""
