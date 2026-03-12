from datetime import datetime

from src.domain.ticket_user import (
    TicketUser,
    StatusRecordTicketUser,
    StatusTicketOfClient,
    Comment,
)

from src.domain.repositories.ticket_user_repository import TicketUserRepository
from utils.db.connect import Connection
from utils.db.exceptions import DBOperationError


class TicketUserRepositorySQLite(TicketUserRepository):

    def __init__(self, conn: Connection):
        self.conn = conn

    # -------------------------
    # Load helpers
    # -------------------------

    def _load_statuses(self, ticket: TicketUser):

        query = self.conn.create_query(
            """
            SELECT user_ticket_status_record_id, employee_id, status, date_created
            FROM user_tickets_status_record
            WHERE user_ticket_id = :ticket_id
            ORDER BY user_ticket_status_record_id
            """,
            var=["status_id", "employee_id", "status", "date_created"],
        )

        rows = query.get_result({"ticket_id": ticket.ticket_id})

        ticket.statuses = []

        for r in rows:

            ticket.statuses.append(
                StatusRecordTicketUser(
                    status_id=r["status_id"],
                    actor_employee_id=r["employee_id"],
                    status=StatusTicketOfClient(r["status"]),
                    created_at=datetime.fromisoformat(r["date_created"]),
                )
            )

    def _load_comments(self, ticket: TicketUser):

        query = self.conn.create_query(
            """
            SELECT user_comment_ticket_id, employee_id, comment, date_created
            FROM user_tickets_comment
            WHERE user_ticket_id = :ticket_id
            ORDER BY user_comment_ticket_id
            """,
            var=["comment_id", "employee_id", "comment", "date_created"],
        )

        rows = query.get_result({"ticket_id": ticket.ticket_id})

        ticket.comments = []

        for r in rows:

            ticket.comments.append(
                Comment(
                    comment_id=r["comment_id"],
                    employee_id=r["employee_id"],
                    comment=r["comment"],
                    date_created=datetime.fromisoformat(r["date_created"]),
                )
            )

    # -------------------------
    # Reads
    # -------------------------

    def get(self, ticket_id: int) -> TicketUser:

        query = self.conn.create_query(
            """
            SELECT user_ticket_id, client_id, user_id,
                   user_ticket_contact_user_id, text_of_ticket,
                   date_created, version, date_closed, is_closed
            FROM user_tickets
            WHERE user_ticket_id = :ticket_id
            """,
            var=[
                "ticket_id",
                "client_id",
                "user_id",
                "contact_user_id",
                "description",
                "date_created",
                "version",
                "date_closed",
                "is_closed",
            ],
        )

        row = query.get_one_result({"ticket_id": ticket_id})

        if not row:
            raise DBOperationError(f"TicketUser {ticket_id} not found")

        ticket = TicketUser(
            ticket_id=row["ticket_id"],
            client_id=row["client_id"],
            user_id=row["user_id"],
            contact_user_id=row["contact_user_id"] or 0,
            description=row["description"] or "",
            date_created=datetime.fromisoformat(row["date_created"]),
            is_closed=bool(row["is_closed"]),
            version=row["version"],
        )

        self._load_statuses(ticket)
        self._load_comments(ticket)

        return ticket

    def get_all(self) -> list[TicketUser]:

        query = self.conn.create_query(
            """
            SELECT user_ticket_id
            FROM user_tickets
            """,
            var=["ticket_id"],
        )

        rows = query.get_result()

        tickets = []

        for r in rows:
            tickets.append(self.get(r["ticket_id"]))

        return tickets

    # -------------------------
    # Save
    # -------------------------

    def save(self, ticket: TicketUser) -> TicketUser:

        try:

            if ticket.ticket_id == 0:

                insert_query = self.conn.create_query(
                    """
                    INSERT INTO user_tickets
                    (client_id, user_id, user_ticket_contact_user_id,
                     text_of_ticket, date_created, version, is_closed)
                    VALUES (:client_id, :user_id, :contact_user_id,
                            :description, :date_created, :version, :is_closed)
                    """
                )

                ticket.ticket_id = insert_query.set_result(
                    {
                        "client_id": ticket.client_id,
                        "user_id": ticket.user_id,
                        "contact_user_id": ticket.contact_user_id,
                        "description": ticket.description,
                        "date_created": ticket.date_created.isoformat(),
                        "version": ticket.version,
                        "is_closed": int(ticket.is_closed),
                    }
                )

            else:

                update_query = self.conn.create_query(
                    """
                    UPDATE user_tickets
                    SET version = :version + 1,
                        is_closed = :is_closed,
                        date_closed = :date_closed
                    WHERE user_ticket_id = :ticket_id
                      AND version = :version
                    """
                )

                update_query.set_result(
                    {
                        "ticket_id": ticket.ticket_id,
                        "version": ticket.version,
                        "is_closed": int(ticket.is_closed),
                        "date_closed": ticket.finished_at.isoformat()
                        if ticket.finished_at
                        else None,
                    }
                )

                if not update_query.count:
                    raise DBOperationError("Optimistic lock error")

            # save statuses
            for s in ticket.statuses:
                if s.status_id == 0:

                    q = self.conn.create_query(
                        """
                        INSERT INTO user_tickets_status_record
                        (employee_id, user_ticket_id, status, date_created)
                        VALUES (:employee_id, :ticket_id, :status, :date_created)
                        """
                    )

                    q.set_result(
                        {
                            "employee_id": s.actor_employee_id,
                            "ticket_id": ticket.ticket_id,
                            "status": s.status.value,
                            "date_created": s.created_at.isoformat(),
                        }
                    )

            # save comments
            for c in ticket.comments:
                if c.comment_id == 0:

                    q = self.conn.create_query(
                        """
                        INSERT INTO user_tickets_comment
                        (user_ticket_id, employee_id, comment, date_created)
                        VALUES (:ticket_id, :employee_id, :comment, :date_created)
                        """
                    )

                    q.set_result(
                        {
                            "ticket_id": ticket.ticket_id,
                            "employee_id": c.employee_id,
                            "comment": c.comment,
                            "date_created": c.date_created.isoformat(),
                        }
                    )

            ticket.version += 1

            return ticket

        except Exception as e:
            raise DBOperationError(f"TicketUser save failed: {str(e)}")

    # -------------------------
    # Delete
    # -------------------------

    def delete(self, ticket_id: int):

        try:

            self.conn.create_query(
                "DELETE FROM user_tickets_comment WHERE user_ticket_id=:id"
            ).set_result({"id": ticket_id})

            self.conn.create_query(
                "DELETE FROM user_tickets_status_record WHERE user_ticket_id=:id"
            ).set_result({"id": ticket_id})

            self.conn.create_query(
                "DELETE FROM user_tickets WHERE user_ticket_id=:id"
            ).set_result({"id": ticket_id})

        except Exception as e:
            raise DBOperationError(f"Delete failed: {str(e)}")


