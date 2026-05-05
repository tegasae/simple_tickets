from datetime import datetime

from src.adapters.repositories.base_repository import BaseRepository

from src.adapters.repositories.gateways.ticket_gateway import (
    TicketGateway,
    TicketCommentGateway,
    TicketExecutorGateway,
    TicketStatusGateway,
)
from src.adapters.repositories.mappers.ticket_mapper import TicketMapper
from src.domain.repositories.ticket_repository import TicketRepository

from src.domain.ticket import Ticket, TicketStatusRecord, TicketStatus
from src.domain.ticket_components import Comment, ExecutorAssignment
from src.domain.exceptions import ItemNotFoundError
from utils.db.exceptions import DBOperationError


class TicketRepositorySQLite(TicketRepository, BaseRepository):






    # ---------------------------
    # load helpers
    # ---------------------------

    def _load_comments(self, ticket: Ticket) -> None:
        rows = self._get_many(
            TicketCommentGateway.SELECT,
            TicketMapper.VARS_COMMENT,
            {"ticket_id": ticket.ticket_id},
        )

        ticket.comments = []
        for r in rows:
            c = Comment(
                comment_id=r['comment_ticket_id'],
                employee_id=r["admin_id"],
                comment=r["comment"],
                date_created=datetime.fromisoformat(r["date_created"])
            )
            ticket.comments.append(c)

    def _load_executors(self, ticket: Ticket) -> None:
        rows = self._get_many(
            TicketExecutorGateway.SELECT,
            ["admin_id", "date_assignment"],
            {"ticket_id": ticket.ticket_id},
        )

        ticket.executors = []
        for r in rows:
            e = ExecutorAssignment(
                admin_id=r["admin_id"],
            )
            ticket.executors.append(e)

    def _load_statuses(self, ticket: Ticket) -> None:
        rows = self._get_many(
            TicketStatusGateway.SELECT,
            ["admin_id", "status", "date_created"],
            {"ticket_id": ticket.ticket_id},
        )

        ticket.statuses = []
        for r in rows:
            s = TicketStatusRecord(
                actor_employee_id=r["admin_id"],
                status=TicketStatus(r["status"]),
            )
            ticket.statuses.append(s)

    # ---------------------------
    # count helpers for append-only history
    # ---------------------------



    def _status_count(self, ticket_id: int) -> int:
        row = self._get_one(
            TicketStatusGateway.COUNT1,
            ["cnt"],
            {"ticket_id": ticket_id},
        )
        return int(row["cnt"]) if row else 0

    # ---------------------------
    # append-only sync helpers
    # ---------------------------

    def _append_new_comments(self, ticket: Ticket) -> None:
        for c in ticket.comments:
            if c.comment_id!=0:
                continue
            result=self._exec(
                TicketCommentGateway.INSERT,
                {
                    "ticket_id": ticket.ticket_id,
                    "admin_id": c.employee_id,
                    "comment": c.comment,
                    "date_created": c.date_created.isoformat(),
                },
             )
            c.comment_id=result.last_row_id


    def _append_new_executors(self, ticket: Ticket) -> None:
        for e in ticket.executors:
            if e.executor_id!=0:
                continue
            result=self._exec(TicketExecutorGateway.INSERT,params={"ticket_id": ticket.ticket_id, "admin_id": e.admin_id,"date_assignment": e.date_created})
            e.executor_id=result.last_row_id

    def _append_new_statuses(self, ticket: Ticket) -> None:
        for s in ticket.statuses:
            if s.status_id==0:
                continue
            result=self._exec(TicketStatusGateway.INSERT, params={"ticket_id":ticket.ticket_id,"status": s.status, "date_created": s.date_created})
            s.status_id=result.last_row_id

    # ---------------------------
    # reads
    # ---------------------------

    def get(self, ticket_id: int) -> Ticket:
        row = self._get_one(
            TicketGateway.SELECT_BY_ID,
            TicketMapper.VARS,
            {"ticket_id": ticket_id},
        )

        if not row:
            raise ItemNotFoundError(f"Ticket {ticket_id} not found")

        ticket = TicketMapper.row_to_ticket(row)

        self._load_statuses(ticket)
        self._load_comments(ticket)
        self._load_executors(ticket)

        # recompute closure safely after histories are loaded
        ticket.__post_init__()

        return ticket

    def get_all(self) -> list[Ticket]:
        rows = self._get_many(
            TicketGateway.SELECT_BASE,
            TicketMapper.VARS,
        )

        tickets: list[Ticket] = []

        for r in rows:
            ticket = TicketMapper.row_to_ticket(r)
            self._load_statuses(ticket)
            self._load_comments(ticket)
            self._load_executors(ticket)
            ticket.__post_init__()
            tickets.append(ticket)

        return tickets

    # ---------------------------
    # save
    # ---------------------------

    def save(self, ticket: Ticket) -> Ticket:
        try:
            if ticket.ticket_id == 0:
                ins = self._exec(
                    TicketGateway.INSERT,
                    TicketMapper.ticket_params(ticket),
                )
                ticket.ticket_id = ins.last_row_id

                # For new tickets, append all history rows
                self._append_new_comments(ticket)
                self._append_new_executors(ticket)
                self._append_new_statuses(ticket)

                return ticket

            upd = self._exec(
                TicketGateway.UPDATE,
                TicketMapper.ticket_params(ticket),
            )

            if upd.rowcount == 0:
                raise DBOperationError("Optimistic lock failed")

            # append-only history
            self._append_new_comments(ticket)
            self._append_new_executors(ticket)
            self._append_new_statuses(ticket)

            ticket.version += 1
            return ticket

        except Exception as e:
            raise DBOperationError(f"Failed to save ticket: {e}")

    # ---------------------------
    # delete
    # ---------------------------

    def delete(self, ticket_id: int) -> None:
        """
        Preferred approach:
        - use ON DELETE CASCADE in DB schema for comments/executors/statuses
        - then deleting ticket row is enough

        If cascade is not configured, delete children first.
        """
        self._exec(
            TicketCommentGateway.DELETE_ALL,
            {"ticket_id": ticket_id},
        )
        self._exec(
            TicketExecutorGateway.DELETE_ALL,
            {"ticket_id": ticket_id},
        )
        self._exec(
            TicketStatusGateway.DELETE_ALL,
            {"ticket_id": ticket_id},
        )
        self._exec(
            TicketGateway.DELETE,
            {"ticket_id": ticket_id},
        )

    def does_client_exist(self, client_id: int) -> bool:
        return self._exists(TicketGateway.SELECT_BY_CLIENT_ID, {'client_id': client_id})

    def does_user_tickets_exist(self, user_ticket_id: int) -> bool:
        return self._exists(TicketGateway.SELECT_BY_TICKET_USER_ID, {'user_ticket_id': user_ticket_id})
