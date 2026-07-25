# src/adapters/repositories/mappers/ticket_mapper.py

from datetime import datetime, timezone

from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    """
    Converts SQLite TEXT datetime to timezone-aware datetime.

    SQLite NULL / empty string becomes None.
    Naive datetime from old data is interpreted as UTC.
    """
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _datetime_to_db(value: datetime | None) -> str | None:
    """
    Converts domain datetime to SQLite TEXT.

    All stored datetimes are normalized to UTC ISO-8601.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()


class TicketMapper:
    TICKET_FIELDS = [
        "ticket_id",
        "client_id",
        "admin_id",
        "user_id",
        "contact_user_id",
        "user_ticket_id",
        "department_id",
        "text_of_ticket",
        "description",
        "date_created",
        "is_remote",
        "urgency_level",
        "version",
    ]

    COMMENT_FIELDS = [
        "ticket_comment_id",
        "employee_id",
        "comment",
        "date_created",
    ]

    STATUS_FIELDS = [
        "status_id",
        "actor_employee_id",
        "status",
        "date_created",
        "executor_id",
        "planned_start_at",
        "planned_finish_at",
        "actual_started_at",
        "actual_finished_at",
        "comment",
    ]

    @staticmethod
    def row_to_ticket(
        row: dict,
        *,
        statuses: list[TicketStatusRecord],
        comments: list[Comment],
    ) -> Ticket:
        date_created = _parse_datetime(row["date_created"])

        if date_created is None:
            raise ValueError(
                f"Ticket {row['ticket_id']} has no date_created"
            )

        return Ticket.rehydrate(
            ticket_id=row["ticket_id"],
            client_id=row["client_id"],
            admin_id=row["admin_id"] or 0,
            text_of_ticket=row["text_of_ticket"] or "",
            user_id=row["user_id"] or 0,
            contact_user_id=row["contact_user_id"] or 0,
            user_ticket_id=row["user_ticket_id"] or 0,
            department_id=row["department_id"] or 0,
            description=row["description"] or "",
            date_created=date_created,
            is_remote=bool(row["is_remote"]),
            urgency_level=row["urgency_level"] or 0,
            version=row["version"] or 0,
            statuses=statuses,
            comments=comments,
        )

    @staticmethod
    def row_to_comment(row: dict) -> Comment:
        date_created = _parse_datetime(row["date_created"])

        if date_created is None:
            raise ValueError(
                f"Ticket comment {row['ticket_comment_id']} "
                "has no date_created"
            )

        return Comment(
            comment_id=row["ticket_comment_id"],
            employee_id=row["employee_id"],
            comment=row["comment"] or "",
            date_created=date_created,
        )

    @staticmethod
    def row_to_status_record(row: dict) -> TicketStatusRecord:
        date_created = _parse_datetime(row["date_created"])

        if date_created is None:
            raise ValueError(
                f"Ticket status record {row['status_id']} "
                "has no date_created"
            )

        return TicketStatusRecord(
            status_id=row["status_id"],
            actor_employee_id=row["actor_employee_id"] or 0,
            status=TicketStatus(row["status"]),
            date_created=date_created,
            executor_id=row["executor_id"] or 0,
            planned_start_at=_parse_datetime(
                row["planned_start_at"]
            ),
            planned_finish_at=_parse_datetime(
                row["planned_finish_at"]
            ),
            actual_started_at=_parse_datetime(
                row["actual_started_at"]
            ),
            actual_finished_at=_parse_datetime(
                row["actual_finished_at"]
            ),
            comment=row["comment"] or "",
        )

    @staticmethod
    def ticket_params(ticket: Ticket) -> dict:
        return {
            "ticket_id": ticket.ticket_id,
            "client_id": ticket.client_id,
            "admin_id": ticket.admin_id or None,
            "user_id": ticket.user_id or None,
            "contact_user_id": ticket.contact_user_id or None,
            "user_ticket_id": ticket.user_ticket_id or None,
            "department_id": ticket.department_id or None,
            "text_of_ticket": ticket.text_of_ticket,
            "description": ticket.description or None,
            "date_created": _datetime_to_db(ticket.date_created),
            "is_remote": int(ticket.is_remote),
            "urgency_level": ticket.urgency_level,
            "version": ticket.version,
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
            "date_created": _datetime_to_db(
                comment.date_created
            ),
        }

    @staticmethod
    def status_record_params(
        *,
        ticket_id: int,
        record: TicketStatusRecord,
    ) -> dict:
        return {
            "ticket_id": ticket_id,
            "actor_employee_id": record.actor_employee_id or None,
            "status": record.status.value,
            "date_created": _datetime_to_db(
                record.date_created
            ),
            "executor_id": (
                record.executor_id
                if record.executor_id != 0
                else None
            ),
            "planned_start_at": _datetime_to_db(
                record.planned_start_at
            ),
            "planned_finish_at": _datetime_to_db(
                record.planned_finish_at
            ),
            "actual_started_at": _datetime_to_db(
                record.actual_started_at
            ),
            "actual_finished_at": _datetime_to_db(
                record.actual_finished_at
            ),
            "comment": record.comment,
        }