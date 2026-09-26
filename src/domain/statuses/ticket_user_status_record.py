from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_user_status import (
    TICKET_USER_STATUS_RULES,
    TicketUserStatus,
    TicketUserStatusRule,
)
from src.domain.value_objects import CommonComment, Empty


@dataclass(frozen=True, slots=True, kw_only=True)
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

    status_id is the persistent identifier of this history record.

        status_id == 0
            record has not been persisted yet

        status_id > 0
            persisted record

        status_id < 0
            invalid


    Comment
    -------

    comment is optional unless the corresponding TicketUserStatusRule
    requires one.

    The absence of a comment is represented by Empty.

    For statuses with:

        rule.requires_comment == True

    Empty is not allowed.


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
    #
    # 0 means that this record has not been persisted yet.
    status_id: int = 0

    # Optional status comment.
    #
    # Empty represents the absence of a comment.
    comment: CommonComment | Empty = field(
        default_factory=Empty,
    )

    # Time when the status record was created.
    #
    # Newly created records always use UTC.
    # Rehydrated records must also already contain UTC datetime.
    date_created: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )



    def __post_init__(self) -> None:
        """
        Validate the complete intrinsic state of the record.

        Validation is intentionally split into small methods:

        - _validate_identity()
        - _validate_actor()
        - _validate_comment()

        Transition-related validation does not belong here.
        """

        self._validate_identity()
        self._validate_actor()
        self._validate_comment()

    @property
    def rule(self) -> TicketUserStatusRule:
        """
        Return intrinsic rules of the current TicketUser status.

        These rules describe properties of the status itself.

        They do not describe allowed workflow transitions.
        """

        return TICKET_USER_STATUS_RULES[self.status]

    def is_new(self) -> bool:
        """
        Return True when this status record has not been persisted yet.

        New records use:

            status_id == 0
        """

        return not bool(self.status_id)


    def _validate_identity(self) -> None:
        """
        Validate record identity, status type and creation time.

        status_id
        ---------

        Negative persistent identifiers are invalid.

        status
        ------

        Must be a TicketUserStatus instance.

        date_created
        ------------

        Must explicitly use UTC.

        The domain deliberately rejects:

        - naive datetime;
        - timezone-aware datetime in a timezone other than UTC.
        """

        if self.status_id < 0:
            raise ItemValidationError(
                "Status record ID cannot be negative"
            )

        if not isinstance(self.status, TicketUserStatus):
            raise ItemValidationError(
                "Invalid TicketUser status"
            )

        if self.date_created.tzinfo is not UTC:
            raise ItemValidationError(
                "Status record date_created must use UTC timezone"
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
        """
        Validate comment requirements of the current status.

        Most statuses allow an empty comment.

        If the current TicketUserStatusRule declares:

            requires_comment == True

        the record must contain CommonComment rather than Empty.
        """

        if (
            self.rule.requires_comment
            and isinstance(self.comment, Empty)
        ):
            raise ItemValidationError(
                f"{self.status} requires a comment"
            )