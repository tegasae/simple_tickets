from typing import runtime_checkable, Protocol


@runtime_checkable
class TicketUserRepository(Protocol):
    def exists_for_user(self, user_id: int) -> bool: ...