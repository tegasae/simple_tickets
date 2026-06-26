from __future__ import annotations

from typing import Iterator

from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.exceptions import (
    OptimisticLockError,
    PersistenceError,
)
from src.adapters.repositories.gateways.ticket_gateway import (
    TicketCommentGateway,
    TicketGateway,
    TicketStatusGateway,
)
from src.adapters.repositories.mappers.ticket_mapper import TicketMapper
from src.domain.exceptions import ItemNotFoundError
from src.domain.repositories.ticket_repository import TicketRepository
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment


class TicketRepositorySQLite(TicketRepository, BaseRepository):
    """
    SQLite repository for the Ticket aggregate.

    Aggregate persistence:
        Ticket
        TicketStatusRecord[]
        Comment[]

    Status records and comments are append-only.
    Executor history is stored inside TicketStatusRecord.executor_id.
    """

    # ---------------------------
    # Load helpers
    # ---------------------------

    def _load_comments(self, ticket_id: int) -> list[Comment]:
        rows = self._get_many(
            TicketCommentGateway.SELECT_BY_TICKET_ID,
            TicketMapper.COMMENT_FIELDS,
            {"ticket_id": ticket_id},
        )

        return [
            TicketMapper.row_to_comment(row)
            for row in rows
        ]

    def _load_statuses(
        self,
        ticket_id: int,
    ) -> list[TicketStatusRecord]:
        rows = self._get_many(
            TicketStatusGateway.SELECT_BY_TICKET_ID,
            TicketMapper.STATUS_FIELDS,
            {"ticket_id": ticket_id},
        )

        return [
            TicketMapper.row_to_status_record(row)
            for row in rows
        ]

    def _load_ticket(self, row: dict) -> Ticket:
        ticket_id = row["ticket_id"]

        statuses = self._load_statuses(ticket_id)
        comments = self._load_comments(ticket_id)

        return TicketMapper.row_to_ticket(
            row,
            statuses=statuses,
            comments=comments,
        )

    # ---------------------------
    # Append-only sync helpers
    # ---------------------------

    def _append_new_comments(self, ticket: Ticket) -> None:
        for comment in ticket.new_comments():
            result = self._exec(
                TicketCommentGateway.INSERT,
                TicketMapper.comment_params(
                    ticket_id=ticket.ticket_id,
                    comment=comment,
                ),
            )

            comment.comment_id = result.last_row_id

    def _append_new_statuses(self, ticket: Ticket) -> None:
        for record in ticket.new_statuses():
            result = self._exec(
                TicketStatusGateway.INSERT,
                TicketMapper.status_record_params(
                    ticket_id=ticket.ticket_id,
                    record=record,
                ),
            )

            record.status_id = result.last_row_id

    # ---------------------------
    # Reads
    # ---------------------------

    def get(self, ticket_id: int) -> Ticket:
        row = self._get_one(
            TicketGateway.SELECT_BY_ID,
            TicketMapper.TICKET_FIELDS,
            {"ticket_id": ticket_id},
        )

        if not row:
            raise ItemNotFoundError(f"Ticket {ticket_id}")

        return self._load_ticket(row)

    def get_all(self) -> list[Ticket]:
        rows = self._get_many(
            TicketGateway.SELECT_ALL,
            TicketMapper.TICKET_FIELDS,
        )

        return [
            self._load_ticket(row)
            for row in rows
        ]

    def iter_active_by_client_id(
        self,
        *,
        client_id: int,
        batch_size: int = 500,
    ) -> Iterator[list[Ticket]]:
        """
        Loads non-terminal tickets of one client in batches.

        The SQL query determines only whether a ticket is terminal.
        Domain rules decide which workflow action is allowed.
        """
        last_id = 0

        while True:
            rows = self._get_many(
                TicketGateway.SELECT_ACTIVE_BY_CLIENT_ID_BATCH,
                TicketMapper.TICKET_FIELDS,
                {
                    "client_id": client_id,
                    "last_id": last_id,
                    "limit": batch_size,
                },
            )

            if not rows:
                return

            yield [
                self._load_ticket(row)
                for row in rows
            ]

            last_id = rows[-1]["ticket_id"]

    def get_by_user_ticket_id(
        self,
        user_ticket_id: int,
    ) -> Ticket:
        row = self._get_one(
            TicketGateway.SELECT_BY_USER_TICKET_ID,
            TicketMapper.TICKET_FIELDS,
            {"user_ticket_id": user_ticket_id},
        )

        if not row:
            raise ItemNotFoundError(
                f"Ticket for user ticket {user_ticket_id}"
            )

        return self._load_ticket(row)

    # ---------------------------
    # Save
    # ---------------------------

    def save(self, ticket: Ticket) -> Ticket:
        """
        Saves Ticket aggregate.

        For a new ticket:
            1. inserts Ticket row;
            2. inserts initial status history;
            3. inserts initial comments.

        For an existing ticket:
            1. updates Ticket root using optimistic locking;
            2. appends new status records;
            3. appends new comments.
        """
        try:
            if ticket.ticket_id == 0:
                result = self._exec(
                    TicketGateway.INSERT,
                    TicketMapper.ticket_params(ticket),
                )

                ticket.ticket_id = result.last_row_id

                self._append_new_statuses(ticket)
                self._append_new_comments(ticket)

                return ticket

            result = self._exec(
                TicketGateway.UPDATE,
                TicketMapper.ticket_params(ticket),
            )

            if result.rowcount == 0:
                raise OptimisticLockError(
                    f"Ticket {ticket.ticket_id} "
                    f"was changed by another transaction"
                )

            self._append_new_statuses(ticket)
            self._append_new_comments(ticket)

            ticket.version += 1

            return ticket

        except (OptimisticLockError, PersistenceError):
            raise
        except Exception as exc:
            raise PersistenceError(
                f"Failed to save ticket {ticket.ticket_id}: {exc}"
            ) from exc

    # ---------------------------
    # Delete
    # ---------------------------

    def delete(self, ticket_id: int) -> None:
        """
        ticket_status_records and ticket_comments must use
        ON DELETE CASCADE for ticket_id foreign key.
        """
        self._exec(
            TicketGateway.DELETE,
            {"ticket_id": ticket_id},
        )

    # ---------------------------
    # Reference checks
    # ---------------------------

    def does_client_exist(self, client_id: int) -> bool:
        """
        Historical name preserved.

        Returns True when at least one Ticket belongs to client_id.
        """
        row = self._get_one(
            TicketGateway.COUNT_BY_CLIENT_ID,
            ["cnt"],
            {"client_id": client_id},
        )

        return bool(row and int(row["cnt"]) > 0)

    def does_user_tickets_exist(
        self,
        user_ticket_id: int,
    ) -> bool:
        """
        Historical name preserved.

        Returns True when at least one Ticket references user_ticket_id.
        """
        row = self._get_one(
            TicketGateway.COUNT_BY_USER_TICKET_ID,
            ["cnt"],
            {"user_ticket_id": user_ticket_id},
        )

        return bool(row and int(row["cnt"]) > 0)

    def has_admin_reference(self, admin_id: int) -> bool:
        """
        Checks whether an Admin is referenced by Ticket aggregate data.

        Reference sources:
            - Ticket.admin_id;
            - TicketStatusRecord.actor_employee_id;
            - TicketStatusRecord.executor_id;
            - Comment.employee_id.
        """
        return (
            self._exists(
                TicketGateway.EXISTS_BY_ADMIN_ID,
                {"admin_id": admin_id},
            )
            or self._exists(
                TicketStatusGateway.EXISTS_BY_EMPLOYEE_ID,
                {"employee_id": admin_id},
            )
            or self._exists(
                TicketCommentGateway.EXISTS_BY_EMPLOYEE_ID,
                {"employee_id": admin_id},
            )
        )

    def has_department_reference(self, department_id: int) -> bool:
        return self._exists(
            TicketGateway.EXISTS_BY_DEPARTMENT_ID,
            {"department_id": department_id},
        )