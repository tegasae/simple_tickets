# src/adapters/repositories/mappers/ticket_mapper.py
from datetime import timedelta

from src.adapters.repositories.mappers.auxiliary import datetime_to_db, dt_from_sqlite
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket, TicketUrgency
from src.domain.ticket_components import Comment



class TicketMapper:
    TICKET_FIELDS = [
        "ticket_id",
        "client_id",
        "text_of_ticket",
        "user_id",
        "contact_user_id",
        "user_ticket_id",
        "date_created",
        "planned_at",
        "department_id",
        "remote_work_recommended",
        "urgency_level",
        "description",
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
        "status",
        "actor_employee_id",
        "work_is_remote",
        "date_created",
        "executor_id",
        "actual_started_at",
        "actual_finished_at",
        "duration",
        "comment",
    ]

    @staticmethod
    def row_to_ticket(
        row: dict,
        *,
        statuses: list[TicketStatusRecord],
        comments: list[Comment],
    ) -> Ticket:
        date_created = dt_from_sqlite(row["date_created"])

        if date_created is None:
            raise ValueError(
                f"Ticket {row['ticket_id']} has no date_created"
            )

        return Ticket.rehydrate(
            ticket_id=row["ticket_id"],
            client_id=row["client_id"],
            text_of_ticket=row["text_of_ticket"] or "",
            user_id=row["user_id"] or 0,
            contact_user_id=row["contact_user_id"] or 0,
            user_ticket_id=row["user_ticket_id"] or 0,
            department_id=row["department_id"] or 0,
            description=row["description"] or "",
            date_created=date_created,
            remote_work_recommended=bool(row["remote_work_recommended"]),
            urgency=TicketUrgency(row["urgency_level"]),
            version=row["version"] or 0,
            planned_at=dt_from_sqlite(row["planned_at"]),
            statuses=statuses,
            comments=comments,
        )

    @staticmethod
    def row_to_comment(row: dict) -> Comment:
        date_created = dt_from_sqlite(row["date_created"])

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
        date_created = dt_from_sqlite(row["date_created"])

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
            work_is_remote=bool(row["work_is_remote"]),
            actual_started_at=dt_from_sqlite(
                row["actual_started_at"]
            ),
            actual_finished_at=dt_from_sqlite(
                row["actual_finished_at"]
            ),
            duration= timedelta(seconds=row["duration"]) or timedelta(seconds=0),
            comment=row["comment"] or "",
        )

    @staticmethod
    def ticket_params(ticket: Ticket) -> dict:
        return {
            "ticket_id": ticket.ticket_id,
            "client_id": ticket.client_id,
            "user_id": ticket.user_id or None,
            "contact_user_id": ticket.contact_user_id or None,
            "user_ticket_id": ticket.user_ticket_id or None,
            "department_id": ticket.department_id or None,
            "text_of_ticket": ticket.text_of_ticket,
            "description": ticket.description or None,
            "date_created": datetime_to_db(ticket.date_created),
            "remote_work_recommended": int(ticket.remote_work_recommended),
            "planned_at":  datetime_to_db(ticket.planned_at),
            "urgency_level": ticket.urgency,
            "version": ticket.version,
            "current_executor_id": ticket.current_executor_id(),
            "date_finished": datetime_to_db(ticket.date_finished),
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
            "comment": comment.comment.value,
            "date_created": datetime_to_db(
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
            "actor_employee_id": record.actor_employee_id,
            "status": record.status.value,
            "date_created": datetime_to_db(
                record.date_created
            ),
            "executor_id": record.executor_id if record.executor_id else None,

            "actual_started_at": datetime_to_db(
                record.actual_started_at
            ),
            "actual_finished_at": datetime_to_db(
                record.actual_finished_at
            ),
            "work_is_remote":record.work_is_remote,
            "duration": record.duration.total_seconds(),
            "comment": record.comment.value,
        }