from src.domain.account import Account
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.repositories.account_repository import AccountRepository


class EmployeeAccountService:
    def __init__(
            self,
            account_repository: AccountRepository

    ) -> None:
        self._account_repository = account_repository

    def attach_account(
            self,
            *,
            employee_id: int,
            login: str,
            plain_password: str,
    ) -> Account:
        """
        Create a new Account and attach it to an Admin.

        Raises:
          - DomainOperationError if admin already has an account
          - ItemValidationError if login already exists
        """
        try:
            self._account_repository.get_employee_id(employee_id=employee_id)
            raise DomainOperationError(f"Employee {employee_id} already has an account")
        except DomainOperationError:
            #if self._account_repository.find_by_login(login):
            #    raise ItemValidationError(f"Login '{login}' is already taken")
            account = Account.create(account_id=0, login=login, plain_password=plain_password)
            account = self._account_repository.save(account=account,employee_id=employee_id)
        return account

    def detach_account(self, *, employee_id: int):
        """
        Detach account from admin (does NOT delete account).
        """
        self._account_repository.delete(employee_id=employee_id)


    # -------- Account enable/disable (only if attached) --------

    def disable_account(self, *, employee_id: int):
        account = self._account_repository.get_employee_id(employee_id=employee_id)
        account.disable()
        self._account_repository.save(account=account)

    def enable_account(self, *, employee_id: int):
        account = self._account_repository.get_employee_id(employee_id=employee_id)
        account.disable()
        self._account_repository.save(account=account)

    def update_password(self, *, employee_id: int, password: str) -> None:
        account = self._account_repository.get(employee_id)
        account.change_password(plain_password=password)
        self._account_repository.save(account)

    def check_password(self, *, admin_id: int, password: str) -> bool:
        account = self._account_repository.get(admin_id)
        return account.verify_password(plain_password=password)

    def find_by_login(self, *, login: str) -> Admin:
        employee_id = self._account_repository.find_by_login(login=login)
        return self._account_repository.get(employee_id)
