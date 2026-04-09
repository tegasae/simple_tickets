from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.gateways.ticket_user_gateway import TicketUserGateway
from src.adapters.repositories.gateways.ticket_user_status_gateway import TicketUserStatusGateway
from src.adapters.repositories.gateways.ticket_user_comment_gateway import TicketUserCommentGateway
from src.adapters.repositories.mappers.ticket_user_mapper import TicketUserMapper

from src.domain.repositories.ticket_user_repository import TicketUserRepository
from src.domain.exceptions import ItemNotFoundError
from src.domain.ticket_user import TicketUser
from utils.db.exceptions import DBOperationError


class TicketUserRepositorySQLite(BaseRepository, TicketUserRepository):

    # -------------------------
    # Load helpers
    # -------------------------

    def _load_statuses(self, ticket):

        rows = self._get_many(
            TicketUserStatusGateway.SELECT,
            TicketUserMapper.VARS_STATUS,
            {"ticket_id": ticket.ticket_id},
        )

        ticket.statuses = [
            TicketUserMapper.row_to_status(r)
            for r in rows
        ]

    def _load_comments(self, ticket):

        rows = self._get_many(
            TicketUserCommentGateway.SELECT,
            TicketUserMapper.VARS_COMMENT,
            {"ticket_id": ticket.ticket_id},
        )

        ticket.comments = [
            TicketUserMapper.row_to_comment(r)
            for r in rows
        ]

    # -------------------------
    # Reads
    # -------------------------

    def get(self, ticket_id):

        row = self._get_one(
            TicketUserGateway.SELECT_BY_ID,
            TicketUserMapper.VARS_TICKET,
            {"ticket_id": ticket_id},
        )

        if not row:
            raise ItemNotFoundError(f"TicketUser {ticket_id} not found")

        ticket = TicketUserMapper.row_to_ticket(row)

        self._load_statuses(ticket)
        self._load_comments(ticket)

        return ticket

    def get_all(self):

        rows = self._get_many(
            TicketUserGateway.SELECT_ALL,
            ["ticket_id"],
        )

        tickets = []

        for r in rows:
            tickets.append(self.get(r["ticket_id"]))

        return tickets

    # -------------------------
    # Save
    # -------------------------

    def save(self, ticket:TicketUser):

        try:

            if ticket.ticket_id == 0:

                result = self._exec(
                    TicketUserGateway.INSERT,
                    TicketUserMapper.ticket_params(ticket=ticket)
                )
                ticket.ticket_id=result.last_row_id
            else:

                result = self._exec(
                    TicketUserGateway.UPDATE,
                    {
                        "ticket_id": ticket.ticket_id,
                        "version": ticket.version,
                        "is_closed": int(ticket.is_closed),
                        "date_closed": ticket.date_finished.isoformat()
                        if ticket.date_finished
                        else None,
                    },
                )

                if not result:
                    raise DBOperationError("Optimistic lock error")

            # insert statuses
            for s in ticket.statuses:

                if s.status_id != 0:
                    continue

                self._exec(
                    TicketUserStatusGateway.INSERT,
                    {
                        "employee_id": s.actor_employee_id,
                        "ticket_id": ticket.ticket_id,
                        "status": s.status.value,
                        "date_created": s.date_created.isoformat(),
                    },
                )

            # insert comments
            for c in ticket.comments:

                if c.comment_id != 0:
                    continue

                self._exec(
                    TicketUserCommentGateway.INSERT,
                    {
                        "ticket_id": ticket.ticket_id,
                        "employee_id": c.employee_id,
                        "comment": c.comment,
                        "date_created": c.date_created.isoformat(),
                    },
                )

            ticket.version += 1

            return ticket

        except Exception as e:
            raise DBOperationError(f"TicketUser save failed: {str(e)}")

    # -------------------------
    # Delete
    # -------------------------

    def delete(self, ticket_id):

        try:

            self._exec(
                TicketUserCommentGateway.DELETE_ALL,
                {"ticket_id": ticket_id},
            )

            self._exec(
                TicketUserStatusGateway.DELETE_ALL,
                {"ticket_id": ticket_id},
            )

            self._exec(
                TicketUserGateway.DELETE,
                {"ticket_id": ticket_id},
            )

        except Exception as e:
            raise DBOperationError(f"Delete failed: {str(e)}")

    def does_client_exist(self, client_id: int) -> bool:
        return self._exists(TicketUserGateway.SELECT_BY_ID, {'client_id': client_id})