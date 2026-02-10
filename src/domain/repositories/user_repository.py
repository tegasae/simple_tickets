from typing import runtime_checkable, Protocol

from src.domain.employee import User


@runtime_checkable
class UserRepository(Protocol):
    def get(self, user_id: int) -> User: ...
    def save(self, user: User) -> None: ...
    def hard_delete(self, user_id: int) -> None: ...

