from __future__ import annotations


from dataclasses import dataclass

from typing import Self

from src.domain.value_objects import Login, Password

# Требования:
# - минимум 8 символов
# - хотя бы одна строчная, одна заглавная, одна цифра, один спецсимвол





@dataclass(slots=True)
class Account:
    account_id: int
    login: "Login"
    password: Password

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

if __name__=="__main__":
    account=Account.create(1,"login","1234567890")
    print(account)
    print(account.verify_password("1234567890"))
    account.from_db(1,"login","1234567890")
    print(account.password)