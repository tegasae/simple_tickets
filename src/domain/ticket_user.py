"""User-facing TicketUser aggregate and its workflow commands."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Self

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.statuses.ticket_user_status import TicketUserStatus
from src.domain.statuses.ticket_user_status_record import TicketUserStatusRecord
from src.domain.statuses.ticket_user_status_transitions import (
    FIRST_TICKET_USER_STATUSES,
    TERMINAL_TICKET_USER_STATUSES,
    TICKET_USER_TRANSITIONS,
)
from src.domain.ticket_components import Comment
from src.domain.value_objects import CommonComment, Description, Empty, TextOfTicket


@dataclass(kw_only=True)
class TicketUser:
    """User-facing request aggregate.

    TicketUser and Ticket are independent aggregates. Coordination between
    them belongs to domain/application services, not this aggregate.

    The original request text is immutable by business rules. Description
    and contact User are editable. update_details() replaces both fields.

    TicketUserStatusRecord records the actual actor identifier, which may
    represent a User or an Admin. This aggregate does not perform RBAC.

    Stored datetime values must explicitly use datetime.UTC.
    """

    ticket_user_id: int
    client_id: int
    user_id: int
    text_of_ticket: TextOfTicket

    description: Description | Empty = field(default_factory=Empty)
    contact_user_id: int = 0

    statuses: list[TicketUserStatusRecord] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    date_created: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 0

    is_closed: bool = field(init=False, default=False)
    date_finished: datetime | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Validate invariants without normalizing persisted values."""
        self._validate_identity()
        self._validate_content()
        self._validate_datetimes()
        self._validate_status_history()
        self._recompute_closed_state()

    # ==================================================================
    # Factories
    # ==================================================================

    @staticmethod
    def _resolve_contact_user_id(
        *,
        user_id: int,
        contact_user_id: int,
    ) -> int:
        """Resolve the contact when creating a new request."""
        if type(contact_user_id) is not int or contact_user_id < 0:
            raise ItemValidationError(
                "Contact user id must be a non-negative integer"
            )
        return contact_user_id if contact_user_id > 0 else user_id

    @classmethod
    def create(
        cls,
        *,
        client_id: int,
        user_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        comment: str = "",

    ) -> Self:
        """Create a User-originated request, directly or through staff."""
        if type(user_id) is not int or user_id <= 0:
            raise ItemValidationError("User id must be a positive integer")

        now = datetime.now(UTC)
        resolved_contact_user_id = cls._resolve_contact_user_id(
            user_id=user_id,
            contact_user_id=contact_user_id,
        )

        ticket_user = cls(
            ticket_user_id=0,
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=TextOfTicket(text_of_ticket),
            contact_user_id=resolved_contact_user_id,
            description=Description(description) if description else Empty(),
            date_created=now,
            version=0,
            statuses=[
                TicketUserStatusRecord(
                    status=TicketUserStatus.CREATED,
                    actor_employee_id=user_id,
                    date_created=now,
                ),
            ],
        )

        if comment.strip():
            ticket_user.add_comment(
                Comment(
                    employee_id=user_id,
                    comment=CommonComment(comment),
                    date_created=now,
                )
            )

        return ticket_user

    @classmethod
    def rehydrate(
        cls,
        *,
        ticket_user_id: int,
        client_id: int,
        user_id: int,
        text_of_ticket: str,
        statuses: list[TicketUserStatusRecord],
        date_created: datetime,
        contact_user_id: int,
        description: str = "",
        comments: list[Comment] | None = None,
        version: int = 0,
    ) -> Self:
        """Restore persisted fields and replay the workflow history."""
        if type(ticket_user_id) is not int or ticket_user_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser with non-positive ticket_user_id"
            )
        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate TicketUser without status history"
            )

        ticket_user = cls(
            ticket_user_id=ticket_user_id,
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=TextOfTicket(text_of_ticket),
            contact_user_id=contact_user_id,
            description=Description(description) if description else Empty(),
            statuses=statuses[:1],
            comments=comments if comments is not None else [],
            date_created=date_created,
            version=version,
        )

        for record in statuses[1:]:
            ticket_user.append_status(record)

        return ticket_user

    # ==================================================================
    # Queries and persistence helpers
    # ==================================================================

    def is_new(self) -> bool:
        return self.ticket_user_id == 0

    def current_status_record(self) -> TicketUserStatusRecord:
        if not self.statuses:
            raise DomainOperationError("TicketUser has no status history")
        return self.statuses[-1]

    def current_status(self) -> TicketUserStatus:
        return self.current_status_record().status

    def is_terminal(self) -> bool:
        return self.current_status() in TERMINAL_TICKET_USER_STATUSES

    def new_statuses(self) -> list[TicketUserStatusRecord]:
        return [record for record in self.statuses if record.is_new()]

    def new_comments(self) -> list[Comment]:
        return [comment for comment in self.comments if comment.is_new()]

    # ==================================================================
    # Editable data
    # ==================================================================

    def _resolve_edited_contact_user_id(self, contact_user_id: int) -> int:
        """Validate and resolve a contact for an existing request."""
        if type(contact_user_id) is not int or contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id must be a non-negative integer"
            )
        return contact_user_id if contact_user_id > 0 else self.user_id

    def update_details(
        self,
        *,
        description: str = "",
        contact_user_id: int = 0,
    ) -> None:
        """Replace BOTH description and contact User on a nonterminal request.

        An omitted description clears it; an omitted or zero contact resets
        the contact to the request's owner.
        """
        self._ensure_not_terminal()

        new_contact_user_id = self._resolve_edited_contact_user_id(
            contact_user_id
        )
        new_description = Description(description) if description else Empty()

        self.description = new_description
        self.contact_user_id = new_contact_user_id

    def change_contact_user(
        self,
        *,
        contact_user_id: int,
    ) -> None:
        """Set or reset the contact without changing description.

        Linked-pair synchronization belongs to TicketSyncService.
        No actor is recorded for a data-only change.
        """
        self._ensure_not_terminal()
        self.contact_user_id = self._resolve_edited_contact_user_id(
            contact_user_id
        )

    # ==================================================================
    # Workflow commands
    # ==================================================================

    def mark_in_work(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """Set IN_WORK, including a return from WAITING_FOR_CONFIRMATION."""
        self.append_status(
            TicketUserStatusRecord(
                status=TicketUserStatus.IN_WORK,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        )

    def mark_waiting_for_confirmation(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """Record that work is ready for the User's confirmation."""
        self.append_status(
            TicketUserStatusRecord(
                status=TicketUserStatus.WAITING_FOR_CONFIRMATION,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        )

    def confirm_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """Record User confirmation (terminal status)."""
        self.append_status(
            TicketUserStatusRecord(
                status=TicketUserStatus.CONFIRMED_BY_USER,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        )

    def confirm_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """Record Admin confirmation (terminal status)."""
        self.append_status(
            TicketUserStatusRecord(
                status=TicketUserStatus.CONFIRMED_BY_ADMIN,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        )

    def suspend(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """Move the request to terminal SUSPENDED status."""
        self.append_status(
            TicketUserStatusRecord(
                status=TicketUserStatus.SUSPENDED,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        )

    def cancel_by_user(
        self,
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """Cancel a request by User; allowed only from CREATED."""
        self.append_status(
            TicketUserStatusRecord(
                status=TicketUserStatus.CANCELLED_BY_USER,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        )

    def cancel_by_admin(
        self,
        *,
        actor_employee_id: int,
        comment: str,
    ) -> None:
        """Cancel by Admin; a valid status comment is required."""
        self.append_status(
            TicketUserStatusRecord(
                status=TicketUserStatus.CANCELLED_BY_ADMIN,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        )

    # ==================================================================
    # Workflow and ordinary comments
    # ==================================================================

    def append_status(self, record: TicketUserStatusRecord) -> None:
        """Append a valid chronological transition to workflow history."""
        self._ensure_not_terminal()
        self._require_utc_datetime(
            record.date_created,
            field_name="status.date_created",
        )

        current_record = self.current_status_record()

        if record.status not in TICKET_USER_TRANSITIONS[current_record.status]:
            raise DomainOperationError(
                "TicketUser status transition is not allowed: "
                f"{current_record.status.value} -> {record.status.value}"
            )

        if record.date_created < current_record.date_created:
            raise DomainOperationError(
                "TicketUser status history must be chronological"
            )

        self.statuses.append(record)
        self._recompute_closed_state()

    def add_comment(self, comment: Comment) -> None:
        """Append a nonempty ordinary comment to a nonterminal request."""
        self._ensure_not_terminal()

        if not comment.comment:
            raise DomainOperationError("Comment cannot be empty")

        self._require_utc_datetime(
            comment.date_created,
            field_name="comment.date_created",
        )
        self.comments.append(comment)

    # ==================================================================
    # Validation
    # ==================================================================

    def _validate_status_history(self) -> None:
        """Validate initial status, transitions and chronological order."""
        if not self.statuses:
            raise DomainOperationError("TicketUser must have status history")

        first_record = self.statuses[0]
        if first_record.status not in FIRST_TICKET_USER_STATUSES:
            raise DomainOperationError(
                "TicketUser cannot start with status "
                f"{first_record.status.value}"
            )

        for index in range(1, len(self.statuses)):
            previous_record = self.statuses[index - 1]
            current_record = self.statuses[index]

            if (
                current_record.status
                not in TICKET_USER_TRANSITIONS[previous_record.status]
            ):
                raise DomainOperationError(
                    "Invalid TicketUser status history: "
                    f"{previous_record.status.value} -> "
                    f"{current_record.status.value}"
                )

            if current_record.date_created < previous_record.date_created:
                raise DomainOperationError(
                    "TicketUser status history must be chronological"
                )

    def _ensure_not_terminal(self) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                f"TicketUser {self.ticket_user_id} is in terminal "
                f"status {self.current_status().value}"
            )

    def _validate_identity(self) -> None:
        """Validate aggregate identifiers and persistence version strictly."""
        for name, value, minimum in (
            ("ticket_user_id", self.ticket_user_id, 0),
            ("client_id", self.client_id, 1),
            ("user_id", self.user_id, 1),
            ("contact_user_id", self.contact_user_id, 1),
            ("version", self.version, 0),
        ):
            if type(value) is not int or value < minimum:
                raise DomainOperationError(
                    f"{name} must be an integer >= {minimum}"
                )

    def _validate_content(self) -> None:
        """Require request text and description to use their value objects."""
        if not isinstance(self.text_of_ticket, TextOfTicket):
            raise DomainOperationError(
                "TicketUser text_of_ticket must be TextOfTicket"
            )

        if not isinstance(self.description, (Description, Empty)):
            raise DomainOperationError(
                "TicketUser description must be Description or Empty"
            )

    def _validate_datetimes(self) -> None:
        """Validate aggregate, status and ordinary comment UTC datetimes."""
        self._require_utc_datetime(self.date_created, field_name="date_created")

        for record in self.statuses:
            self._require_utc_datetime(
                record.date_created,
                field_name="status.date_created",
            )

        for comment in self.comments:
            self._require_utc_datetime(
                comment.date_created,
                field_name="comment.date_created",
            )

    # ==================================================================
    # Derived state and helpers
    # ==================================================================

    def _recompute_closed_state(self) -> None:
        self.is_closed = self.is_terminal()
        self.date_finished = (
            self.current_status_record().date_created
            if self.is_closed
            else None
        )

    @staticmethod
    def _require_utc_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        """Require a datetime with exactly datetime.UTC as timezone."""
        if not isinstance(value, datetime):
            raise ItemValidationError(f"{field_name} must be datetime")

        if value.tzinfo is not UTC:
            raise ItemValidationError(
                f"{field_name} must use UTC timezone"
            )
