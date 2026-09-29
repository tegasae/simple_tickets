# src/adapters/repositories/mappers/ticket_user_mapper.py



from src.adapters.repositories.mappers.auxiliary import datetime_to_db, dt_from_sqlite
from src.domain.statuses.ticket_user_status_record import TicketUserStatusRecord
from src.domain.ticket_components import Comment
from src.domain.ticket_user import (
    TicketUser,
)
from src.domain.statuses.ticket_user_status import TicketUserStatus

class TicketUserMapper:
    TICKET_FIELDS = [
        "ticket_user_id",
        "client_id",
        "user_id",
        "contact_user_id",
        "text_of_ticket",
        "description",
        "date_created",
        "version",
    ]

    STATUS_FIELDS = [
        "ticket_user_status_id",
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
        statuses: list[TicketUserStatusRecord],
        comments: list[Comment],
    ) -> TicketUser:
        return TicketUser.rehydrate(
            ticket_user_id=row["user_ticket_id"],
            client_id=row["client_id"],
            user_id=row["user_id"],
            contact_user_id=row["contact_user_id"] or 0,
            text_of_ticket=row["text_of_ticket"],
            description=row["description"] or "",
            date_created=dt_from_sqlite(
                row["date_created"],
            ),
            version=row["version"] or 0,
            comments=comments,
            statuses=statuses,
        )

    @staticmethod
    def row_to_status(
        row: dict,
    ) -> TicketUserStatusRecord:
        return TicketUserStatusRecord(
            ticket_user_status_id=row["user_ticket_status_record_id"],
            actor_employee_id=row["actor_employee_id"],
            status=TicketUserStatus(row["status"]),
            comment=row["comment"] or "",
            date_created=dt_from_sqlite(
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
            date_created=dt_from_sqlite(
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
            "user_ticket_id": ticket.ticket_user_id,
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
            "date_closed": (
                datetime_to_db(ticket.date_finished)
                if ticket.date_finished is not None
                else None
            ),
        }

    @staticmethod
    def status_record_params(
        *,
        ticket_user_id: int,
        record: TicketUserStatusRecord,
    ) -> dict:
        return {
            "ticket_user_id": ticket_user_id,
            "actor_employee_id": record.actor_employee_id,
            "status": record.status.value,
            "comment": record.comment,
            "date_created": datetime_to_db(
                record.date_created,
            ),
        }

    @staticmethod
    def comment_params(
        *,
        ticket_user_id: int,
        comment: Comment,
    ) -> dict:
        return {
            "ticket_user_id": ticket_user_id,
            "employee_id": comment.employee_id,
            "comment": comment.comment,
            "date_created": datetime_to_db(
                comment.date_created,
            ),
        }