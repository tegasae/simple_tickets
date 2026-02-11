# src/domain/repositories/account_repository.py


from typing import Protocol, runtime_checkable

from src.domain.account import Account, NoAccount


@runtime_checkable
class AccountRepository(Protocol):
    """
    Repository for system accounts.

    Note: Not every employee has an account, so employee code should not
    assume account existence. This repo never returns NoAccount.
    """

    # -------- Reads --------

    def get(self, account_id: int) -> Account: ...

    def get_all(self) -> list[Account]: ...
    def exists(self, account_id: int) -> bool: ...
    def account_is_enabled(self,account_id:int)->bool: ...
    # Often useful:
    def find_by_login(self, login: str) -> Account | NoAccount: ...
    def account_is_enabled_by_login(self, login: str) -> bool: ...
    # -------- Writes --------

    def save(self, account: Account): ...
    def hard_delete(self, account_id: int): ...
