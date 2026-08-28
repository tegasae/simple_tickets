# src/domain/ticket_user.py



from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Final, Self

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.ticket_components import Comment


class TicketUserStatus(StrEnum):
    CREATED = "created"
    CONFIRMED_BY_ADMIN = "confirmed_by_admin"
    IN_WORK = "in_work"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"

    EXECUTION_CONFIRMED_BY_USER = "execution_confirmed_by_user"
    EXECUTION_CONFIRMED_BY_ADMIN = "execution_confirmed_by_admin"

    CANCELLED_BY_USER = "cancelled_by_user"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"

    @classmethod
    def can_transition(
        cls,
        from_status: Self,
        to_status: Self,
    ) -> bool:
        from_status = cls(from_status)
        to_status = cls(to_status)

        return to_status in TICKET_USER_TRANSITIONS[from_status]

    @classmethod
    def is_terminal(
        cls,
        status: Self,
    ) -> bool:
        return cls(status) in TERMINAL_TICKET_USER_STATUSES


# Compatibility alias for older imports.
# Do not use this name in new code.
StatusTicketOfClient = TicketUserStatus


TERMINAL_TICKET_USER_STATUSES: Final[frozenset[TicketUserStatus]] = frozenset({
    TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
    TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
    TicketUserStatus.CANCELLED_BY_USER,
    TicketUserStatus.CANCELLED_BY_ADMIN,
})


TICKET_USER_TRANSITIONS: Final[dict[TicketUserStatus, frozenset[TicketUserStatus]]] = {
    TicketUserStatus.CREATED: frozenset({
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.CANCELLED_BY_USER,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.CONFIRMED_BY_ADMIN: frozenset({
        TicketUserStatus.IN_WORK,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.IN_WORK: frozenset({
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.WAITING_FOR_CONFIRMATION,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.WAITING_FOR_CONFIRMATION: frozenset({
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.IN_WORK,
        TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
        TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.EXECUTION_CONFIRMED_BY_USER: frozenset(),
    TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN: frozenset(),
    TicketUserStatus.CANCELLED_BY_USER: frozenset(),
    TicketUserStatus.CANCELLED_BY_ADMIN: frozenset(),
}


def _validate_ticket_user_transitions() -> None:
    missing_statuses = set(TicketUserStatus) - set(TICKET_USER_TRANSITIONS)

    if missing_statuses:
        missing = ", ".join(
            sorted(str(status) for status in missing_statuses),
        )
        raise RuntimeError(
            f"Missing TicketUser transition definitions: {missing}",
        )


_validate_ticket_user_transitions()


@dataclass(kw_only=True)
class StatusRecordTicketUser:
    """
    Неизменяемый факт изменения статуса TicketUser.

    actor_employee_id:
        - для пользовательского действия: id User;
        - для действия Admin: id Admin.

    В TicketUser actor_employee_id не бывает 0.
    Конкретный User хранится именно здесь, в истории TicketUser.
    """

    status_id: int = 0
    actor_employee_id: int
    status: TicketUserStatus

    date_created: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    comment: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            TicketUserStatus(self.status),
        )

        object.__setattr__(
            self,
            "date_created",
            self._normalize_datetime(
                value=self.date_created,
                field_name="date_created",
            ),
        )

        object.__setattr__(
            self,
            "comment",
            self._normalize_comment(self.comment),
        )

        self._validate_identity()

    def is_new(self) -> bool:
        return self.status_id == 0

    def _validate_identity(self) -> None:
        if self.status_id < 0:
            raise ItemValidationError(
                "TicketUser status record ID cannot be negative",
            )

        if self.actor_employee_id <= 0:
            raise ItemValidationError(
                "TicketUser status actor employee ID must be positive",
            )

    @staticmethod
    def _normalize_comment(comment: str) -> str:
        if not isinstance(comment, str):
            raise ItemValidationError(
                "TicketUser status comment must be a string",
            )

        comment = comment.strip()

        if len(comment) > 1000:
            raise ItemValidationError(
                "TicketUser status comment cannot exceed 1000 characters",
            )

        return comment

    @staticmethod
    def _normalize_datetime(
        *,
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime",
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


@dataclass(kw_only=True)
class TicketUser:
    """
    Пользовательская заявка.

    TicketUser отражает внешний workflow пользователя.

    Внутренняя Ticket создаётся и изменяется отдельно:
        TicketUser не создаёт Ticket;
        Ticket не создаёт TicketUser.

    Связь:
        Ticket.user_ticket_id == TicketUser.ticket_id
    """

    ticket_id: int
    client_id: int
    user_id: int

    text_of_ticket: str
    description: str = ""

    contact_user_id: int = 0
    urgency_level: int = 0

    statuses: list[StatusRecordTicketUser] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    date_created: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    is_closed: bool = False
    date_finished: datetime | None = None

    version: int = 0

    @classmethod
    def create(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        user_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        urgency_level: int = 0,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> Self:
        """
        User создаёт TicketUser.

        Новая TicketUser всегда создаётся с ticket_id = 0.
        Repository назначит настоящий ID при сохранении.

        Initial state:
            TicketUser.CREATED

        actor_employee_id:
            user_id

        Application service после этого создаёт связанную Ticket:

            Ticket.CREATED_FROM_TICKET_USER
            Ticket.admin_id = 0
            Ticket.user_ticket_id = TicketUser.ticket_id
            TicketStatusRecord.actor_employee_id = 0
        """
        cls._validate_create_args(
            ticket_id=ticket_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
        )

        now = date_created or datetime.now(timezone.utc)

        ticket_user = cls(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            text_of_ticket=text_of_ticket,
            description=description,
            urgency_level=urgency_level,
            date_created=now,
            statuses=[
                StatusRecordTicketUser(
                    actor_employee_id=user_id,
                    status=TicketUserStatus.CREATED,
                    date_created=now,
                ),
            ],
        )

        comment = comment.strip()
        if comment:
            ticket_user.add_comment(
                Comment(
                    employee_id=user_id,
                    comment=comment,
                ),
            )

        return ticket_user

    @classmethod
    def create_confirmed_by_admin(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        user_id: int,
        actor_admin_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        urgency_level: int = 0,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> Self:
        """
        Admin создаёт TicketUser для конкретного User.

        Новая TicketUser всегда создаётся с ticket_id = 0.
        Repository назначит настоящий ID при сохранении.

        Initial state:
            TicketUser.CONFIRMED_BY_ADMIN

        actor_employee_id:
            actor_admin_id
        """
        cls._validate_create_args(
            ticket_id=ticket_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
        )

        if actor_admin_id <= 0:
            raise ItemValidationError(
                "Actor admin id must be positive",
            )

        now = date_created or datetime.now(timezone.utc)

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            text_of_ticket=text_of_ticket,
            description=description,
            urgency_level=urgency_level,
            date_created=now,
            statuses=[
                StatusRecordTicketUser(
                    actor_employee_id=actor_admin_id,
                    status=TicketUserStatus.CONFIRMED_BY_ADMIN,
                    date_created=now,
                    comment=comment,
                ),
            ],
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        ticket_id: int,
        client_id: int,
        user_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        urgency_level: int = 0,
        statuses: list[StatusRecordTicketUser],
        comments: list[Comment] | None = None,
        date_created: datetime,
        is_closed: bool = False,
        date_finished: datetime | None = None,
        version: int = 0,
    ) -> Self:
        """
        Восстанавливает TicketUser из БД.

        Repository обязан передать persisted entity:
            ticket_id > 0

        Repository обязан передать полную историю статусов
        в стабильном порядке:

            ORDER BY date_created, status_id

        is_closed и date_finished являются derived state.
        Они будут пересчитаны в __post_init__.
        """
        if ticket_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser with non-positive ticket_id",
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser without status history",
            )

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            text_of_ticket=text_of_ticket,
            description=description,
            urgency_level=urgency_level,
            statuses=statuses,
            comments=comments or [],
            date_created=date_created,
            is_closed=is_closed,
            date_finished=date_finished,
            version=version,
        )

    def update_details(
            self,
            *,
            actor_employee_id: int,
            description: str = "",
            contact_user_id: int = 0,
    ) -> None:
        if actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be positive",
            )

        if self.is_closed:
            raise DomainOperationError(
                "Cannot update details of closed ticket user",
            )

        description = description.strip()

        if contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id cannot be negative",
            )

        self.description = description
        self.contact_user_id = contact_user_id

    def __post_init__(self) -> None:
        self.text_of_ticket = self.text_of_ticket.strip()
        self.description = self.description.strip()
        self.date_created = self._normalize_datetime(
            value=self.date_created,
            field_name="date_created",
        )

        self._validate_identity()
        self._validate_status_history()
        self._recompute_closed_state()

    # ----------------------------
    # Queries
    # ----------------------------

    def is_new(self) -> bool:
        return self.ticket_id == 0

    def current_status(self) -> TicketUserStatus:
        if not self.statuses:
            raise DomainOperationError(
                "TicketUser has no status history",
            )

        return self.statuses[-1].status

    def current_status_record(self) -> StatusRecordTicketUser:
        if not self.statuses:
            raise DomainOperationError(
                "TicketUser has no status history",
            )

        return self.statuses[-1]

    def is_terminal(self) -> bool:
        return TicketUserStatus.is_terminal(
            self.current_status(),
        )

    def new_statuses(self) -> list[StatusRecordTicketUser]:
        return [
            status
            for status in self.statuses
            if status.is_new()
        ]

    def new_comments(self) -> list[Comment]:
        return [
            comment
            for comment in self.comments
            if comment.comment_id == 0
        ]

    # ----------------------------
    # Commands
    # ----------------------------

    def confirm_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicketUser:
        return self._append_status(
            StatusRecordTicketUser(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.CONFIRMED_BY_ADMIN,
                comment=comment,
            ),
        )

    def mark_in_work(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicketUser:
        return self._append_status(
            StatusRecordTicketUser(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.IN_WORK,
                comment=comment,
            ),
        )

    def mark_waiting_for_confirmation(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicketUser:
        return self._append_status(
            StatusRecordTicketUser(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.WAITING_FOR_CONFIRMATION,
                comment=comment,
            ),
        )

    def confirm_execution_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicketUser:
        return self._append_status(
            StatusRecordTicketUser(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.EXECUTION_CONFIRMED_BY_USER,
                comment=comment,
            ),
        )

    def confirm_execution_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicketUser:
        return self._append_status(
            StatusRecordTicketUser(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
                comment=comment,
            ),
        )

    def cancel_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicketUser:
        return self._append_status(
            StatusRecordTicketUser(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.CANCELLED_BY_USER,
                comment=comment,
            ),
        )

    def cancel_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicketUser:
        return self._append_status(
            StatusRecordTicketUser(
                actor_employee_id=actor_employee_id,
                status=TicketUserStatus.CANCELLED_BY_ADMIN,
                comment=comment,
            ),
        )

    def add_comment(self, comment: Comment) -> None:
        self._ensure_not_terminal()

        comment.comment = comment.comment.strip()

        if not comment.comment:
            raise DomainOperationError(
                "The comment can't be empty",
            )

        self.comments.append(comment)

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _append_status(
        self,
        record: StatusRecordTicketUser,
    ) -> StatusRecordTicketUser:
        self._ensure_not_terminal()

        current_status = self.current_status()

        if not TicketUserStatus.can_transition(
            current_status,
            record.status,
        ):
            raise DomainOperationError(
                "TicketUser status transition is not allowed: "
                f"{current_status.value} -> {record.status.value}",
            )

        self.statuses.append(record)
        self._recompute_closed_state()

        return record

    def _ensure_not_terminal(self) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                f"The TicketUser {self.ticket_id} is in terminal status "
                f"{self.current_status().value}",
            )

    def _validate_identity(self) -> None:
        if self.ticket_id < 0:
            raise DomainOperationError(
                "TicketUser ticket_id cannot be negative",
            )

        if self.client_id <= 0:
            raise DomainOperationError(
                "TicketUser client_id must be positive",
            )

        if self.user_id <= 0:
            raise DomainOperationError(
                "TicketUser user_id must be positive",
            )

        if self.contact_user_id < 0:
            raise DomainOperationError(
                "TicketUser contact_user_id cannot be negative",
            )

        if self.urgency_level < 0:
            raise DomainOperationError(
                "TicketUser urgency_level cannot be negative",
            )

        if self.version < 0:
            raise DomainOperationError(
                "TicketUser version cannot be negative",
            )

        if not self.text_of_ticket:
            raise DomainOperationError(
                "TicketUser text_of_ticket cannot be empty",
            )

    def _validate_status_history(self) -> None:
        if not self.statuses:
            raise DomainOperationError(
                "TicketUser must have status history",
            )

        first_status = self.statuses[0].status

        if first_status not in {
            TicketUserStatus.CREATED,
            TicketUserStatus.CONFIRMED_BY_ADMIN,
        }:
            raise DomainOperationError(
                "TicketUser first status must be CREATED "
                "or CONFIRMED_BY_ADMIN",
            )

        for index in range(1, len(self.statuses)):
            previous_status = self.statuses[index - 1].status
            current_status = self.statuses[index].status

            if not TicketUserStatus.can_transition(
                previous_status,
                current_status,
            ):
                raise DomainOperationError(
                    "Invalid TicketUser status history: "
                    f"{previous_status.value} -> {current_status.value}",
                )

    def _recompute_closed_state(self) -> None:
        if not self.statuses:
            self.is_closed = False
            self.date_finished = None
            return

        self.is_closed = self.is_terminal()

        if self.is_closed:
            self.date_finished = (
                self.current_status_record().date_created
            )
        else:
            self.date_finished = None

    @staticmethod
    def _validate_create_args(
        *,
        ticket_id: int,
        user_id: int,
        text_of_ticket: str,
    ) -> None:
        #if ticket_id != 0:
        #    raise ItemValidationError(
        #        "New TicketUser ticket_id must be 0",
        #    )

        if user_id <= 0:
            raise ItemValidationError(
                "TicketUser user_id must be positive",
            )

        if not isinstance(text_of_ticket, str):
            raise ItemValidationError(
                "TicketUser text_of_ticket must be a string",
            )

        if not text_of_ticket.strip():
            raise ItemValidationError(
                "TicketUser text_of_ticket cannot be empty",
            )

    def belong(self, employee_id: int) -> bool:
        if employee_id <= 0:
            return False

        if employee_id == self.user_id:
            return True

        if employee_id == self.contact_user_id:
            return True

        for status in self.statuses:
            if status.actor_employee_id == employee_id:
                return True

        for comment in self.comments:
            if comment.employee_id == employee_id:
                return True

        return False

    @staticmethod
    def _normalize_datetime(
        *,
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime",
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)