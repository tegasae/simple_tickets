# src/domain/ticket_user.py

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.statuses.ticket_user_status import TicketUserStatus, _validate_ticket_user_transitions, \
    StatusRecordTicketUser
from src.domain.ticket_components import Comment
from src.domain.value_objects import Empty, CommonComment, Description

# Compatibility alias for older imports.
# Do not use this name in new code.
#StatusTicketOfClient = TicketUserStatus


_validate_ticket_user_transitions()


@dataclass(kw_only=True)
class TicketUser:
    """
    Пользовательская заявка.

    TicketUser отражает внешний workflow пользователя.

    TicketUser и внутренняя Ticket являются независимыми
    aggregates.

    Связь с внутренней Ticket:

        Ticket.user_ticket_id == TicketUser.ticket_id
    """

    ticket_id: int
    client_id: int
    user_id: int

    text_of_ticket: str
    description: Description|Empty=field(default_factory=Empty)
    contact_user_id: int = 0
    urgency_level: int = 0

    statuses: list[StatusRecordTicketUser] = field(
        default_factory=list,
    )
    comments: list[Comment] = field(
        default_factory=list,
    )

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    version: int = 0

    # Derived state.
    is_closed: bool = field(
        init=False,
        default=False,
    )
    date_finished: datetime | None = field(
        init=False,
        default=None,
    )

    def __post_init__(self) -> None:
        self.text_of_ticket = self.text_of_ticket.strip()

        if not self.contact_user_id:
            self.contact_user_id=self.user_id

        self.date_created = self._normalize_datetime(
            value=self.date_created,
            field_name="date_created",
        )

        self._validate_identity()
        self._validate_status_history()
        self._recompute_closed_state()

    # ----------------------------
    # Factories
    # ----------------------------

    @classmethod
    def create(
        cls,
        *,
        ticket_id: int = 0,
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
        User создаёт новую TicketUser.

        Initial state:
            CREATED

        actor_employee_id:
            user_id
        """
        if ticket_id != 0:
            raise ItemValidationError(
                "New TicketUser ticket_id must be 0"
            )

        now = date_created or datetime.now(UTC)

        ticket_user = cls(
            ticket_id=0,
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
            contact_user_id=contact_user_id,
            description=Description(description) if description else Empty(),
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



        if comment:
            ticket_user.add_comment(comment=Comment(employee_id=user_id,comment=CommonComment(comment)))


        return ticket_user

    @classmethod
    def create_confirmed_by_admin(
        cls,
        *,
        ticket_id: int = 0,
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

        Initial state:
            CONFIRMED_BY_ADMIN

        actor_employee_id:
            actor_admin_id
        """
        if ticket_id != 0:
            raise ItemValidationError(
                "New TicketUser ticket_id must be 0"
            )

        if actor_admin_id <= 0:
            raise ItemValidationError(
                "Actor admin id must be positive"
            )

        now = date_created or datetime.now(UTC)

        return cls(
            ticket_id=0,
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
            contact_user_id=contact_user_id,
            description=Description(description) if description else Empty(),
            urgency_level=urgency_level,
            date_created=now,
            statuses=[
                StatusRecordTicketUser(
                    actor_employee_id=actor_admin_id,
                    status=TicketUserStatus.CONFIRMED_BY_ADMIN,
                    date_created=now,
                    status_comment=CommonComment(comment) if comment else Empty(),
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
        statuses: list[StatusRecordTicketUser],
        date_created: datetime,
        contact_user_id: int = 0,
        description: str = "",
        urgency_level: int = 0,
        comments: list[Comment] | None = None,
        version: int = 0,
    ) -> Self:
        """
        Восстанавливает TicketUser из persistence.

        Repository обязан передать:
        - ticket_id > 0;
        - полную историю статусов;
        - историю в правильном порядке.

        is_closed и date_finished вычисляются из истории.
        """
        if ticket_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser with "
                "non-positive ticket_id"
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser without "
                "status history"
            )

        return cls(
            ticket_id=ticket_id,
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
            contact_user_id=contact_user_id,
            description=Description(description) if description else Empty(),
            urgency_level=urgency_level,
            statuses=statuses,
            comments=comments or [],
            date_created=date_created,
            version=version,
        )

    # ----------------------------
    # Queries
    # ----------------------------

    def is_new(self) -> bool:
        return self.ticket_id == 0

    def current_status_record(
        self,
    ) -> StatusRecordTicketUser:
        if not self.statuses:
            raise DomainOperationError(
                "TicketUser has no status history"
            )

        return self.statuses[-1]

    def current_status(self) -> TicketUserStatus:
        return self.current_status_record().status

    def is_terminal(self) -> bool:
        return self.current_status_record().is_terminal()

    def new_statuses(
        self,
    ) -> list[StatusRecordTicketUser]:
        return [
            record
            for record in self.statuses
            if record.is_new()
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

    def update_details(
            self,
            *,
            actor_employee_id: int,
            description: str = "",
            contact_user_id: int = 0,
    ) -> None:
        if actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be positive"
            )

        if self.is_terminal():
            raise DomainOperationError(
                "Cannot update details of terminal TicketUser"
            )

        if contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id cannot be negative"
            )

        self.description=Description(description) if description else Empty()
        self.contact_user_id = contact_user_id

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
                status_comment=CommonComment(comment) if comment else Empty(),
            )
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
                status_comment=CommonComment(comment) if comment else Empty(),
            )
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
                status_comment=CommonComment(comment) if comment else Empty(),
            )
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
                status_comment=CommonComment(comment) if comment else Empty(),
            )
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
                status_comment=CommonComment(comment) if comment else Empty(),
            )
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
                status_comment=CommonComment(comment) if comment else Empty(),
            )
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
                status_comment=CommonComment(comment) if comment else Empty(),
            )
        )

    def add_comment(
        self,
        comment: Comment,
    ) -> None:
        self._ensure_not_terminal()


        if not comment.comment:
            raise DomainOperationError(
                "Comment cannot be empty"
            )

        self.comments.append(comment)

    # ----------------------------
    # Workflow
    # ----------------------------

    def _append_status(
        self,
        record: StatusRecordTicketUser,
    ) -> StatusRecordTicketUser:
        self._ensure_not_terminal()

        current_record = self.current_status_record()

        if not current_record.can_move_to_next_record(
            record
        ):
            raise DomainOperationError(
                "TicketUser status transition is not allowed: "
                f"{current_record.status.value} -> "
                f"{record.status.value}"
            )

        self.statuses.append(record)
        self._recompute_closed_state()

        return record

    def _validate_status_history(self) -> None:
        if not self.statuses:
            raise DomainOperationError(
                "TicketUser must have status history"
            )

        first_record = self.statuses[0]

        if not first_record.is_first_status():
            raise DomainOperationError(
                "TicketUser cannot start with status "
                f"{first_record.status.value}"
            )

        for index in range(1, len(self.statuses)):
            previous_record = self.statuses[index - 1]
            current_record = self.statuses[index]

            if not previous_record.can_move_to_next_record(
                current_record
            ):
                raise DomainOperationError(
                    "Invalid TicketUser status history: "
                    f"{previous_record.status.value} -> "
                    f"{current_record.status.value}"
                )

    def _ensure_not_terminal(self) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                f"TicketUser {self.ticket_id} is in terminal "
                f"status {self.current_status().value}"
            )

    # ----------------------------
    # Validation
    # ----------------------------

    def _validate_identity(self) -> None:
        if self.ticket_id < 0:
            raise DomainOperationError(
                "TicketUser ticket_id cannot be negative"
            )

        if self.client_id <= 0:
            raise DomainOperationError(
                "TicketUser client_id must be positive"
            )

        if self.user_id <= 0:
            raise DomainOperationError(
                "TicketUser user_id must be positive"
            )

        if self.contact_user_id <= 0:
            raise DomainOperationError(
                "TicketUser contact_user_id cannot be negative"
            )

        if self.urgency_level < 0:
            raise DomainOperationError(
                "TicketUser urgency_level cannot be negative"
            )

        if self.version < 0:
            raise DomainOperationError(
                "TicketUser version cannot be negative"
            )

        if not self.text_of_ticket:
            raise DomainOperationError(
                "TicketUser text_of_ticket cannot be empty"
            )

    # ----------------------------
    # Derived state
    # ----------------------------

    def _recompute_closed_state(self) -> None:
        self.is_closed = self.is_terminal()

        if self.is_closed:
            self.date_finished = (
                self.current_status_record().date_created
            )
        else:
            self.date_finished = None



    # ----------------------------
    # Helpers
    # ----------------------------

    @staticmethod
    def _normalize_datetime(
        *,
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise ItemValidationError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)