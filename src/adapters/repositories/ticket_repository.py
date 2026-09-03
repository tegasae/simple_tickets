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

    def iter_by_client_id(
            self,
            *,
            client_id: int,
            batch_size: int = 500,
    ) -> Iterator[Ticket]:
        """
        Loads all tickets of one client in batches.

        Repository does not interpret Ticket workflow state.
        Domain/application logic decides what to do with each Ticket.
        """
        last_id = 0

        while True:
            rows = self._get_many(
                TicketGateway.SELECT_BY_CLIENT_ID_BATCH,
                TicketMapper.TICKET_FIELDS,
                {
                    "client_id": client_id,
                    "last_id": last_id,
                    "limit": batch_size,
                },
            )

            if not rows:
                return

            for row in rows:
                yield self._load_ticket(row)

            last_id = rows[-1]["ticket_id"]

    def iter_get_all(
            self,
            *,
            batch_size: int = 500,
    ) -> Iterator[Ticket]:
        last_id = 0

        while True:
            rows = self._get_many(
                TicketGateway.SELECT_ALL_BATCH,
                TicketMapper.TICKET_FIELDS,
                {
                    "last_id": last_id,
                    "limit": batch_size,
                },
            )

            if not rows:
                return

            for row in rows:
                yield self._load_ticket(row)

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
'''
    def search(
            self,
            criteria: TicketSearchCriteria,
    ) -> list[Ticket]:
        where: list[str] = []
        params: dict[str, object] = {}

        if criteria.client_id != 0:
            where.append("t.client_id = :client_id")
            params["client_id"] = criteria.client_id

        if criteria.user_id != 0:
            where.append("t.user_id = :user_id")
            params["user_id"] = criteria.user_id

        if criteria.admin_id != 0:
            where.append("t.admin_id = :admin_id")
            params["admin_id"] = criteria.admin_id

        if criteria.department_id != 0:
            where.append("t.department_id = :department_id")
            params["department_id"] = criteria.department_id

        if criteria.executor_id != 0:
            where.append(
                "current_executor.executor_id = :executor_id"
            )
            params["executor_id"] = criteria.executor_id

        if criteria.status:
            where.append("current_status.status = :status")
            params["status"] = criteria.status

        if criteria.is_closed is not None:
            where.append("t.is_closed = :is_closed")
            params["is_closed"] = 1 if criteria.is_closed else 0

        if criteria.date_from is not None:
            where.append("t.date_created >= :date_from")
            params["date_from"] = criteria.date_from

        if criteria.date_to is not None:
            where.append("t.date_created < :date_to")
            params["date_to"] = criteria.date_to

        if criteria.text:
            where.append(
                """
                (
                    lower(t.text_of_ticket) LIKE :text
                    OR lower(t.description) LIKE :text
                )
                """
            )
            params["text"] = f"%{criteria.text.lower()}%"

        where_sql = ""

        if where:
            where_sql = "WHERE " + " AND ".join(where)

        params["limit"] = criteria.limit
        params["offset"] = criteria.offset

        sql = f"""
            SELECT
                t.ticket_id
            FROM tickets AS t

            LEFT JOIN ticket_status_records AS current_status
                ON current_status.status_id = (
                    SELECT status_record.status_id
                    FROM ticket_status_records AS status_record
                    WHERE status_record.ticket_id = t.ticket_id
                    ORDER BY status_record.status_id DESC
                    LIMIT 1
                )

            LEFT JOIN ticket_status_records AS current_executor
                ON current_executor.status_id = (
                    SELECT executor_record.status_id
                    FROM ticket_status_records AS executor_record
                    WHERE executor_record.ticket_id = t.ticket_id
                      AND executor_record.executor_id IS NOT NULL
                    ORDER BY executor_record.status_id DESC
                    LIMIT 1
                )

            {where_sql}

            ORDER BY t.date_created DESC, t.ticket_id DESC
            LIMIT :limit
            OFFSET :offset
        """

        rows = self._get_many(
            sql,
            ["ticket_id"],
            params,
        )

        return [
            self.get(row["ticket_id"])
            for row in rows
        ]
        
        '''