# src/adapters/repositories/ticket_user_repository.py

from __future__ import annotations

from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.exceptions import (
    OptimisticLockError,
    PersistenceError,
)
from src.adapters.repositories.gateways.ticket_user_comment_gateway import (
    TicketUserCommentGateway,
)
from src.adapters.repositories.gateways.ticket_user_gateway import (
    TicketUserGateway,
)
from src.adapters.repositories.gateways.ticket_user_status_gateway import (
    TicketUserStatusGateway,
)
from src.adapters.repositories.mappers.ticket_user_mapper import (
    TicketUserMapper,
)
from src.domain.exceptions import ItemNotFoundError
from src.domain.repositories.ticket_user_repository import (
    TicketUserRepository,
)
from src.domain.ticket_components import Comment
from src.domain.ticket_user import (
    StatusRecordTicketUser,
    TicketUser,
)


class TicketUserRepositorySQLite(
    TicketUserRepository,
    BaseRepository,
):
    """
    SQLite repository для aggregate TicketUser.

    Aggregate persistence:

        TicketUser
        StatusRecordTicketUser[]
        Comment[]

    Status history и comments являются append-only.
    """

    # --------------------------------
    # Load helpers
    # --------------------------------

    def _load_statuses(
        self,
        ticket_id: int,
    ) -> list[StatusRecordTicketUser]:
        rows = self._get_many(
            TicketUserStatusGateway.SELECT,
            TicketUserMapper.STATUS_FIELDS,
            {
                "ticket_id": ticket_id,
            },
        )

        return [
            TicketUserMapper.row_to_status(row)
            for row in rows
        ]

    def _load_comments(
        self,
        ticket_id: int,
    ) -> list[Comment]:
        rows = self._get_many(
            TicketUserCommentGateway.SELECT,
            TicketUserMapper.COMMENT_FIELDS,
            {
                "ticket_id": ticket_id,
            },
        )

        return [
            TicketUserMapper.row_to_comment(row)
            for row in rows
        ]

    def _load_ticket(
        self,
        row: dict,
    ) -> TicketUser:
        ticket_id = row["ticket_id"]

        statuses = self._load_statuses(
            ticket_id,
        )

        comments = self._load_comments(
            ticket_id,
        )

        return TicketUserMapper.row_to_ticket(
            row,
            statuses=statuses,
            comments=comments,
        )

    # --------------------------------
    # Append-only persistence
    # --------------------------------

    def _append_new_statuses(
        self,
        ticket: TicketUser,
    ) -> None:
        for record in ticket.new_statuses():
            result = self._exec(
                TicketUserStatusGateway.INSERT,
                TicketUserMapper.status_record_params(
                    ticket_id=ticket.ticket_id,
                    record=record,
                ),
            )

            record.status_id = result.last_row_id

    def _append_new_comments(
        self,
        ticket: TicketUser,
    ) -> None:
        for comment in ticket.new_comments():
            result = self._exec(
                TicketUserCommentGateway.INSERT,
                TicketUserMapper.comment_params(
                    ticket_id=ticket.ticket_id,
                    comment=comment,
                ),
            )

            comment.comment_id = result.last_row_id

    # --------------------------------
    # Reads
    # --------------------------------

    def get(
        self,
        ticket_id: int,
    ) -> TicketUser:
        row = self._get_one(
            TicketUserGateway.SELECT_BY_ID,
            TicketUserMapper.TICKET_FIELDS,
            {
                "ticket_id": ticket_id,
            },
        )

        if not row:
            raise ItemNotFoundError(
                f"TicketUser {ticket_id}"
            )

        return self._load_ticket(row)

    def get_all(
        self,
    ) -> list[TicketUser]:
        rows = self._get_many(
            TicketUserGateway.SELECT_ALL,
            TicketUserMapper.TICKET_FIELDS,
        )

        return [
            self._load_ticket(row)
            for row in rows
        ]

    # --------------------------------
    # Save
    # --------------------------------

    def save(
        self,
        ticket: TicketUser,
    ) -> TicketUser:
        """
        Saves TicketUser aggregate.

        New TicketUser:
            1. INSERT root;
            2. INSERT initial status records;
            3. INSERT initial comments.

        Existing TicketUser:
            1. UPDATE root with optimistic locking;
            2. append new status records;
            3. append new comments.
        """
        try:
            if ticket.ticket_id == 0:
                result = self._exec(
                    TicketUserGateway.INSERT,
                    TicketUserMapper.ticket_params(
                        ticket,
                    ),
                )

                ticket.ticket_id = result.last_row_id

                self._append_new_statuses(
                    ticket,
                )

                self._append_new_comments(
                    ticket,
                )

                return ticket

            result = self._exec(
                TicketUserGateway.UPDATE,
                TicketUserMapper.ticket_params(
                    ticket,
                ),
            )

            if result.rowcount == 0:
                raise OptimisticLockError(
                    f"TicketUser {ticket.ticket_id} "
                    f"was changed by another transaction"
                )

            self._append_new_statuses(
                ticket,
            )

            self._append_new_comments(
                ticket,
            )

            ticket.version += 1

            return ticket

        except (
            OptimisticLockError,
            PersistenceError,
        ):
            raise

        except Exception as exc:
            raise PersistenceError(
                f"Failed to save TicketUser "
                f"{ticket.ticket_id}: {exc}"
            ) from exc

    # --------------------------------
    # Delete
    # --------------------------------

    def delete(
        self,
        ticket_id: int,
    ) -> None:
        """
        Физически удаляет TicketUser aggregate.

        Пока явно удаляем children, поэтому repository
        не зависит от наличия ON DELETE CASCADE.
        """
        try:
            self._exec(
                TicketUserCommentGateway.DELETE_ALL,
                {
                    "ticket_id": ticket_id,
                },
            )

            self._exec(
                TicketUserStatusGateway.DELETE_ALL,
                {
                    "ticket_id": ticket_id,
                },
            )

            self._exec(
                TicketUserGateway.DELETE,
                {
                    "ticket_id": ticket_id,
                },
            )

        except PersistenceError:
            raise

        except Exception as exc:
            raise PersistenceError(
                f"Failed to delete TicketUser "
                f"{ticket_id}: {exc}"
            ) from exc

    # --------------------------------
    # Reference checks
    # --------------------------------

    def does_client_exist(
        self,
        client_id: int,
    ) -> bool:
        """
        Historical method name.

        Returns True when at least one TicketUser
        belongs to client_id.
        """
        row = self._get_one(
            TicketUserGateway.COUNT_BY_CLIENT_ID,
            ["cnt"],
            {
                "client_id": client_id,
            },
        )

        return bool(
            row
            and int(row["cnt"]) > 0
        )

    def has_admin_reference(
        self,
        admin_id: int,
    ) -> bool:
        """
        Проверяет, упоминается ли employee_id Admin
        в persistence TicketUser.

        Источники:
        - StatusRecordTicketUser.actor_employee_id;
        - Comment.employee_id.

        У TicketUser больше нет отдельной executor history.
        """
        return (
            self._exists(
                TicketUserStatusGateway.EXISTS_BY_EMPLOYEE_ID,
                {
                    "employee_id": admin_id,
                },
            )
            or self._exists(
                TicketUserCommentGateway.EXISTS_BY_EMPLOYEE_ID,
                {
                    "employee_id": admin_id,
                },
            )
        )

    def has_user_reference(
            self,
            user_id: int,
    ) -> bool:
        return (
                self._exists(
                    TicketUserGateway.EXISTS_BY_USER_ID,
                    {
                        "user_id": user_id,
                    },
                )
                or self._exists(
            TicketUserStatusGateway.EXISTS_BY_EMPLOYEE_ID,
            {
                "employee_id": user_id,
            },
        )
                or self._exists(
            TicketUserCommentGateway.EXISTS_BY_EMPLOYEE_ID,
            {
                "employee_id": user_id,
            },
        )
        )