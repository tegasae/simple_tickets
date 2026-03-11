from datetime import datetime, timezone

from src.domain.ticket import Ticket


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None

class TicketMapper:
    VARS = [
        "ticket_id",
        "client_id",
        "admin_id",
        "user_id",
        "user_ticket_contact_user_id",
        "user_ticket_id",
        "text_of_ticket",
        "date_created",
        "is_remote",
        "is_closed",
        "date_closed",
        "urgency_level",
        "version",
    ]
    VARS_COMMENT=["comment_ticket_id","admin_id", "comment", "date_created"]
    VARS_EXECUTORS=["executor_id","admin_id","date_created"]
    @staticmethod
    def row_to_ticket(row: dict) -> Ticket:
        ticket = Ticket(
            ticket_id=row["ticket_id"],
            client_id=row["client_id"],
            admin_id=row["admin_id"],
            description=row["text_of_ticket"] or "",
            text_of_ticket=row["text_of_ticket"] or "",
            user_id=row["user_id"] or 0,
            contact_user_id=row["user_ticket_contact_user_id"] or 0,
            user_ticket_id=row["user_ticket_id"] or 0,
            is_remote=bool(row["is_remote"]),
            urgency_level=row["urgency_level"] or 0,
            version=row["version"] or 0,
        )

        created = _parse_dt(row.get("date_created"))
        if created is not None:
            ticket.date_created = created

        finished = _parse_dt(row.get("date_closed"))
        if finished is not None:
            ticket.date_finished = finished

        ticket.is_closed = bool(row["is_closed"])
        return ticket

    @staticmethod
    def ticket_params(ticket: Ticket) -> dict:
        return {
            "ticket_id": ticket.ticket_id,
            "client_id": ticket.client_id,
            "admin_id": ticket.admin_id,
            "user_id": ticket.user_id if ticket.user_id else None,
            "contact_user_id": ticket.contact_user_id if ticket.contact_user_id else None,
            "user_ticket_id": ticket.user_ticket_id if ticket.user_ticket_id else None,
            "text_of_ticket": ticket.text_of_ticket,
            "date_created": ticket.date_created.isoformat(),
            "is_remote": int(ticket.is_remote),
            "is_closed": int(ticket.is_closed),
            "date_closed": ticket.date_finished.isoformat() if ticket.date_finished else None,
            "urgency_level": ticket.urgency_level,
            "version": ticket.version,
        }


