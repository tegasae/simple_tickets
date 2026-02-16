# src/domain/services/account_service.py
from src.domain.account import Account, AccountType
from src.domain.exceptions import ItemValidationError
from src.domain.repositories.account_repository import AccountRepository


# ---------------------------
# Service
# ---------------------------

class AccountService:
    """
    Account use-cases:
      - create account (unique login)
      - attach/detach account to employee
      - enable/disable account
      - change password
      - hard delete (rare)

    Notes:
      - No transaction control here (UoW wraps later).
      - Authorization checks (who can do what) should be in application layer
        or a dedicated RBAC service.
    """

    def __init__(self, account_repository: AccountRepository) -> None:
        self._account_repository = account_repository


    # -------- Account lifecycle --------

    def create_account(self, *, employee_id:int, login: str, plain_password: str) -> Account:
        # Uniqueness rule
        if self._account_repository.find_by_login(login) is not None:
            raise ItemValidationError(f"Login '{login}' is already taken")

        account = Account.create(
            account_id=0,
            login=login,
            plain_password=plain_password,
        )
        account=self._account_repository.save(account=account,employee_id=employee_id)
        return account

    def get_account(self, *, account_id: int) -> AccountType:
        account = self._account_repository.get(account_id)
        return account

    def find_by_login(self, login: str) -> AccountType:
        account = self._account_repository.find_by_login(login)
        return account

    def enable_account(self, *, employee_id: int) -> Account:
        account = self._account_repository.get_by_employee_id(employee_id=employee_id)
        account.enable()
        account=self._account_repository.save(account)
        return account

    def disable_account(self, *, employee_id: int) -> Account:
        account = self._account_repository.get_by_employee_id(employee_id=employee_id)
        account.disable()
        account=self._account_repository.save(account)
        return account

    def change_password(self, *, employee_id:int, new_plain_password: str) -> Account:
        """
        Stores only hashed password (Password.from_plain does hashing + validation).
        """
        account = self._account_repository.get_by_employee_id(employee_id=employee_id)
        if isinstance(account,Account):
            # Account.password is a Password value object; replace it.
            account.password = account.password.from_plain(new_plain_password)  # type: ignore[attr-defined]
            # If you prefer, use: account.password = Password.from_plain(new_plain_password)
            account=self._account_repository.save(account)
        return account


    def check_password(self, *, employee_id: int, password: str) -> bool:
        account = self._account_repository.get_by_employee_id(employee_id=employee_id)
        if isinstance(account,Account):
            account.password = account.password.from_plain(password)
            return True
        return False

    def delete(self, *, account_id: int) -> None:
        """
        Rare operation.
        """

        # No guaranteed way to find employee_id from account_id with current link interface
        self._account_repository.delete(account_id)



