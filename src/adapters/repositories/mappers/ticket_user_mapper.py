# src/adapters/repositories/mappers/ticket_user_mapper.py

from datetime import UTC, datetime

from src.adapters.repositories.mappers.auxiliary import datetime_to_db
from src.domain.ticket_components import Comment
from src.domain.ticket_user import (
    StatusRecordTicketUser,
    TicketUser,
    TicketUserStatus,
)


def _datetime_from_db(
    value: str | datetime,
) -> datetime:
    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(value)

    if result.tzinfo is None:
        return result.replace(tzinfo=UTC)

    return result.astimezone(UTC)


class TicketUserMapper:
    TICKET_FIELDS = [
        "ticket_id",
        "client_id",
        "user_id",
        "contact_user_id",
        "text_of_ticket",
        "description",
        "date_created",
        "version",
        "urgency_level",
    ]

    STATUS_FIELDS = [
        "status_id",
        "actor_employee_id",
        "status",
        "comment",
        "date_created",
    ]

    COMMENT_FIELDS = [
        "comment_id",
        "employee_id",
        "comment",
        "date_created",
    ]

    # --------------------------------
    # DB -> domain
    # --------------------------------

    @staticmethod
    def row_to_ticket(
        row: dict,
        *,
        statuses: list[StatusRecordTicketUser],
        comments: list[Comment],
    ) -> TicketUser:
        return TicketUser.rehydrate(
            ticket_id=row["ticket_id"],
            client_id=row["client_id"],
            user_id=row["user_id"],
            contact_user_id=row["contact_user_id"] or 0,
            text_of_ticket=row["text_of_ticket"],
            description=row["description"] or "",
            date_created=_datetime_from_db(
                row["date_created"],
            ),
            version=row["version"] or 0,
            comments=comments,
            statuses=statuses,
            urgency_level=row["urgency_level"] or 0,
        )

    @staticmethod
    def row_to_status(
        row: dict,
    ) -> StatusRecordTicketUser:
        return StatusRecordTicketUser(
            status_id=row["status_id"],
            actor_employee_id=row["actor_employee_id"],
            status=TicketUserStatus(row["status"]),
            status_comment=row["comment"] or "",
            date_created=_datetime_from_db(
                row["date_created"],
            ),
        )

    @staticmethod
    def row_to_comment(
        row: dict,
    ) -> Comment:
        return Comment(
            comment_id=row["comment_id"],
            employee_id=row["employee_id"],
            comment=row["comment"],
            date_created=_datetime_from_db(
                row["date_created"],
            ),
        )

    # --------------------------------
    # Domain -> DB
    # --------------------------------

    @staticmethod
    def ticket_params(
        ticket: TicketUser,
    ) -> dict:
        return {
            "ticket_id": ticket.ticket_id,
            "client_id": ticket.client_id,
            "user_id": ticket.user_id,
            "contact_user_id": (
                ticket.contact_user_id
                if ticket.contact_user_id > 0
                else None
            ),
            "text_of_ticket": ticket.text_of_ticket,
            "description": ticket.description,
            "date_created": datetime_to_db(
                ticket.date_created,
            ),
            "version": ticket.version,
            "urgency_level": ticket.urgency_level,
            "is_closed": int(ticket.is_closed),
            "date_closed": (
                datetime_to_db(ticket.date_finished)
                if ticket.date_finished is not None
                else None
            ),
        }

    @staticmethod
    def status_record_params(
        *,
        ticket_id: int,
        record: StatusRecordTicketUser,
    ) -> dict:
        return {
            "ticket_id": ticket_id,
            "actor_employee_id": record.actor_employee_id,
            "status": record.status.value,
            "comment": record.status_comment,
            "date_created": datetime_to_db(
                record.date_created,
            ),
        }

    @staticmethod
    def comment_params(
        *,
        ticket_id: int,
        comment: Comment,
    ) -> dict:
        return {
            "ticket_id": ticket_id,
            "employee_id": comment.employee_id,
            "comment": comment.comment,
            "date_created": datetime_to_db(
                comment.date_created,
            ),
        }