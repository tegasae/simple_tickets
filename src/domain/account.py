from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime

from typing import Self

from src.domain.value_objects import Login, Password

@dataclass(slots=True)
class Account:
    account_id: int
    login: Login
    password: Password
    enabled:bool=True
    date_created: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(cls, account_id: int, login: str, plain_password: str) -> Self:
        return cls(
            account_id=account_id,
            login=Login(login),
            password=Password.from_plain(plain_password),
        )

    @classmethod
    def from_db(cls, account_id: int, login: str, password_hash: str) -> Self:
        return cls(
            account_id=account_id,
            login=Login(login),
            password=Password.from_hash(password_hash),
        )

    def verify_password(self, plain_password: str) -> bool:
        return self.password.verify(plain_password)

@dataclass(frozen=True)
class NoAccount:
    """
    Null Object representing the absence of an internal system account.
    Explicitly means: 'this employee has no account in this system'.
    """

    def __str__(self) -> str:
        return "<no-account>"

    def __repr__(self) -> str:
        return "NoAccount()"