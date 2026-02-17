# src/domain/services/user_deletion.py
from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.repositories.ticket_user_repository import TicketUserRepository



# ---------- Domain service ----------

class UserDeletionService:
    """
    Orchestrates user deletion with cross-aggregate checks.

    Rules:
      - Soft delete is always allowed (most common).
      - Hard delete is allowed only if the user has NO TicketUser records.
    """
    def __init__(self, users: UserRepository, ticket_users: TicketUserRepository) -> None:
        self._users = users
        self._ticket_users = ticket_users

    def soft_delete_user(self, user_id: int) -> User:
        user = self._users.get(user_id)
        user.is_deleted=True
        user.is_enabled = False
        self._users.save(user)
        return user

    def hard_delete_user(self, user_id: int) -> None:
        # Fast existence check (don't count; don't load all tickets)
        if self._ticket_users.exists_for_user(user_id):
            raise DomainOperationError(
                f"Cannot hard-delete user {user_id}: they have TicketUser records."
            )
        self._users.hard_delete(user_id)


