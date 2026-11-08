from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.datetime_check import validate_utc_datetime
from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_user_status import (
    TICKET_USER_STATUS_RULES,
    TicketUserStatus,
    TicketUserStatusRule,
)
from src.domain.value_objects import CommonComment, Empty


@dataclass(slots=True, kw_only=True)
class TicketUserStatusRecord:
    """
    Historical record of a TicketUser workflow status.

    The record represents one concrete status change in TicketUser history.

    Responsibilities
    ----------------

    TicketUserStatusRecord validates only its own intrinsic data:

    - persistent identity;
    - status type;
    - actor identity;
    - required comment;
    - datetime contract.

    It does not validate transitions between TicketUser statuses.

    Allowed transitions are defined separately by:

        TICKET_USER_TRANSITIONS


    Status
    ------

    status identifies the TicketUser workflow state represented
    by this record.

    The value must be an instance of TicketUserStatus.


    Actor
    -----

    actor_employee_id stores the real identifier of the actor
    who performed the action.

    The actor may be:

    - User;
    - Admin.

    Which kind of actor is expected is determined by the intrinsic
    TicketUserStatusRule of the status.

    In particular:

        rule.user_action == True
            the action is performed by a User

        rule.user_action == False
            the action is performed by an Admin

    actor_employee_id must always be positive.

    Unlike TicketStatusRecord, TicketUserStatusRecord does not use
    actor_employee_id == 0 for User actions.

    Whether a concrete Admin identifier should be exposed to a User is
    not a domain concern. The domain history always keeps the real actor
    identifier.


    Persistence identity
    --------------------

    ticket_user_status_id is the persistent identifier of this history record.

        ticket_user_status_id == 0
            record has not been persisted yet

        ticket_user_status_id > 0
            persisted record

        ticket_user_status_id < 0
            invalid


    Comment
    -------

    comment is optional unless the corresponding TicketUserStatusRule
    requires one.

    Strings are normalized to CommonComment. An invalid optional string
    becomes Empty. A required comment must be a valid CommonComment.


    Date/time contract
    ------------------

    date_created is the moment when this history record was created.

    All datetime values inside the domain use UTC.

    Therefore date_created must explicitly use:

        datetime.UTC

    Naive datetime values are not allowed.

    Datetime values using another timezone are also not allowed.

    The domain does not automatically convert other timezones to UTC.
    Conversion must happen before the value enters the domain.
    """

    status: TicketUserStatus
    actor_employee_id: int

    # Persistent record identifier.
    # 0 means that this record has not been persisted yet.
    ticket_user_status_id: int = 0

    # Optional status comment.
    # Empty represents the absence of a comment.
    comment: str | CommonComment | Empty = field(
        default_factory=Empty,
    )

    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )

    def __post_init__(self) -> None:
        """Validate the complete intrinsic state of the record."""
        self._validate_identity()
        self._validate_actor()
        self._validate_comment()

    @property
    def rule(self) -> TicketUserStatusRule:
        """Return intrinsic rules of the current TicketUser status."""
        return TICKET_USER_STATUS_RULES[self.status]

    def is_new(self) -> bool:
        """Return True when ticket_user_status_id == 0."""
        return self.ticket_user_status_id == 0

    def _validate_identity(self) -> None:
        """Validate the record ID, status type, and creation time."""
        if type(self.ticket_user_status_id) is not int:
            raise ItemValidationError(
                "TicketUser status record ID must be an integer"
            )

        if self.ticket_user_status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if not isinstance(self.status, TicketUserStatus):
            raise ItemValidationError(
                "Invalid TicketUser status"
            )

        if not isinstance(self.date_created, datetime):
            raise ItemValidationError(
                "date_created must be a datetime"
            )

        validate_utc_datetime(
            self.date_created,
            field_name="date_created",
        )

    def _validate_actor(self) -> None:
        """
        Validate actor identity.

        TicketUserStatusRecord always stores the real actor identifier.

        The actor may be either User or Admin, but the identifier must
        always be positive.
        """
        if self.actor_employee_id <= 0:
            raise ItemValidationError(
                "Actor employee ID must be positive"
            )

    def _validate_comment(self) -> None:
        """Normalize the comment and enforce status-specific requirements."""
        if isinstance(self.comment, str):
            try:
                self.comment = CommonComment(self.comment)
            except ValueError:
                self.comment = Empty()

        if not isinstance(self.comment, (CommonComment, Empty)):
            raise ItemValidationError(
                "Invalid TicketUser status comment"
            )

        if self.rule.requires_comment and isinstance(self.comment, Empty):
            raise ItemValidationError(
                f"{self.status} requires a comment"
            )
