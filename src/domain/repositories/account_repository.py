# src/domain/repositories/account_repository.py
from abc import ABC, abstractmethod


from src.domain.account import Account, AccountType


class AccountRepository(ABC):
    """
    Repository for system accounts.

    Note: Not every employee has an account, so employee code should not
    assume account existence. This repo never returns NoAccount.
    """

    # -------- Reads --------
    @abstractmethod
    def get(self, account_id: int) -> AccountType:
        raise NotImplementedError

    @abstractmethod
    def get_employee_id(self, employee_id: int) -> AccountType:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Account]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, account_id: int) -> bool:
        raise NotImplementedError

    # Often useful:
    @abstractmethod
    def find_by_login(self, login: str) -> int: #employee_id
        raise NotImplementedError

    @abstractmethod
    def account_is_enabled_by_login(self, login: str) -> bool:
        raise NotImplementedError

    # -------- Writes --------
    @abstractmethod
    def save(self, account: Account,employee_id=0)->Account:
        raise NotImplementedError

    @abstractmethod
    def delete(self, employee_id: int):
        raise NotImplementedError
