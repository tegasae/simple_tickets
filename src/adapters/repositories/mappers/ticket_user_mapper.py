from datetime import datetime

from src.domain.ticket_user import (
    TicketUser,
    StatusRecordTicketUser,
    StatusTicketOfClient,
    Comment,
)


class TicketUserMapper:

    VARS_TICKET = [
        "ticket_id",
        "client_id",
        "user_id",
        "contact_user_id",
        "description",
        "date_created",
        "version",
        "date_closed",
        "is_closed",
    ]

    VARS_STATUS = [
        "status_id",
        "employee_id",
        "status",
        "date_created",
    ]

    VARS_COMMENT = [
        "comment_id",
        "employee_id",
        "comment",
        "date_created",
    ]

    @staticmethod
    def row_to_ticket(row):

        return TicketUser(
            ticket_id=row["ticket_id"],
            client_id=row["client_id"],
            user_id=row["user_id"],
            contact_user_id=row["contact_user_id"] or 0,
            description=row["description"] or "",
            date_created=datetime.fromisoformat(row["date_created"]),
            is_closed=bool(row["is_closed"]),
            version=row["version"],
        )

    @staticmethod
    def ticket_params(ticket: TicketUser) -> dict:
        return {
            "ticket_id": ticket.ticket_id,
            "client_id": ticket.client_id,
            "user_id": ticket.user_id,
            "contact_user_id": ticket.contact_user_id if ticket.contact_user_id else None,
            "description": ticket.description,
            "date_created": ticket.date_created.isoformat(),
            "version": ticket.version,
            "is_closed": int(ticket.is_closed),
            "date_closed": (
                ticket.date_finished.isoformat()
                if ticket.date_finished
                else None
            ),
        }

    @staticmethod
    def row_to_status(row):

        return StatusRecordTicketUser(
            status_id=row["status_id"],
            actor_employee_id=row["employee_id"],
            status=StatusTicketOfClient(row["status"]),
            date_created=datetime.fromisoformat(row["date_created"]),
        )

    @staticmethod
    def row_to_comment(row):

        return Comment(
            comment_id=row["comment_id"],
            employee_id=row["employee_id"],
            comment=row["comment"],
            date_created=datetime.fromisoformat(row["date_created"]),
        )