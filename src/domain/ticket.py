"""Ticket aggregate and workflow commands."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Self

from src.domain.datetime_check import validate_utc_datetime
from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.statuses.rules.ticket_origin_rule import TICKET_ORIGIN_RULES
from src.domain.statuses.rules.ticket_state_rule import (
    TicketStateRule,
    TICKET_STATE_RULES,
)
from src.domain.statuses.rules.ticket_status_transition import (
    FIRST_TICKET_STATUSES,
    TERMINAL_TICKET_STATUSES,
    TICKET_TRANSITIONS,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket_components import Comment, TicketUrgency
from src.domain.value_objects import CommonComment, Description, Empty, TextOfTicket


@dataclass(kw_only=True)
class Ticket:
    """Aggregate of an internal Ticket.

    New Tickets are created through create() or create_from_ticket_user().
    Persisted Tickets are restored through rehydrate().

    The last TicketStatusRecord determines the current workflow state.
    TicketStatusRecord validates its own fields; Ticket validates its
    aggregate invariants, and TICKET_TRANSITIONS defines allowed changes.

    Times within the domain are UTC. The registration time of a workflow
    record is its date_created. An explicit work interval or duration, when
    present, takes priority over timestamps in workflow history.

    planned_at is independent of workflow status. Terminal state and closing
    time are derived from the status history, not supplied by callers.

    The aggregate does not check external actors' permissions, foreign-key
    existence, or the state of other aggregates.
    """

    ticket_id: int
    client_id: int
    text_of_ticket: TextOfTicket

    description: Description | Empty = field(default_factory=Empty)
    user_id: int = 0
    contact_user_id: int = 0
    statuses: list[TicketStatusRecord] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    date_created: datetime = field(default_factory=lambda: datetime.now(UTC))
    planned_at: datetime | None = None
    department_id: int = 0
    remote_work_recommended: bool = False
    version: int = 0
    urgency: TicketUrgency = TicketUrgency.NORMAL
    user_ticket_id: int = 0

    is_closed: bool = field(init=False, default=False)
    date_finished: datetime | None = field(init=False, default=None)

    @property
    def rule(self) -> TicketStateRule:
        """Rules belonging to the current state of the Ticket aggregate."""
        return TICKET_STATE_RULES[self.current_status()]

    def __post_init__(self) -> None:
        if not self.statuses:
            raise DomainOperationError("Ticket must have status history")

        if self.statuses[0].status not in FIRST_TICKET_STATUSES:
            raise DomainOperationError("The first Ticket status is incorrect")

        self._validate_identity()
        self._validate_datetimes()
        self._validate_creation_origin()
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
        if contact_user_id < 0:
            raise ItemValidationError("Contact user id cannot be negative")

        if contact_user_id > 0:
            return contact_user_id

        return user_id

    @classmethod
    def _create_new(
            cls,
            *,
            client_id: int,
            text_of_ticket: str,
            initial_status: TicketStatus,
            actor_employee_id: int,
            comment_employee_id: int,
            user_id: int = 0,
            contact_user_id: int = 0,
            user_ticket_id: int = 0,
            department_id: int = 0,
            description: str = "",
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            comment: str = "",
    ) -> Self:
        """Shared implementation of the two public creation scenarios."""
        now = datetime.now(UTC)

        if planned_at is not None:
            cls._validate_new_planned_at(planned_at, reference_time=now)

        resolved_contact_user_id = cls._resolve_contact_user_id(
            user_id=user_id,
            contact_user_id=contact_user_id,
        )

        ticket = cls(
            ticket_id=0,
            client_id=client_id,
            text_of_ticket=TextOfTicket(text_of_ticket),
            user_id=user_id,
            contact_user_id=resolved_contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=Description(description) or Empty(),
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            date_created=now,
            version=0,
            statuses=[
                TicketStatusRecord(
                    status=initial_status,
                    actor_employee_id=actor_employee_id,
                    date_created=now,
                ),
            ],
        )

        if comment.strip():
            ticket.add_comment(
                Comment(
                    employee_id=comment_employee_id,
                    comment=CommonComment(comment),
                    date_created=now,
                )
            )

        return ticket

    @classmethod
    def create(
            cls,
            *,
            client_id: int,
            admin_id: int,
            text_of_ticket: str,
            contact_user_id: int = 0,
            department_id: int = 0,
            description: str = "",
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            comment: str = "",
    ) -> Self:
        """Create a Ticket with initial status CREATED, by an Admin.

        The existing ticket_user_id parameter is preserved for API
        compatibility. It is forwarded to the stored user_ticket_id field.
        """
        return cls._create_new(
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            initial_status=TicketStatus.CREATED,
            actor_employee_id=admin_id,
            comment_employee_id=admin_id,
            user_id=0,
            contact_user_id=contact_user_id,
            user_ticket_id=0,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
        )

    @classmethod
    def create_from_request_user(
            cls,
            *,
            client_id: int,
            admin_id: int,
            user_id: int,
            user_ticket_id: int,
            text_of_ticket: str,
            contact_user_id: int = 0,
            department_id: int = 0,
            description: str = "",
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            comment: str = "",
    ) -> Self:
        """Register a User request entered by an Admin.

      The Admin is the author of the internal Ticket's initial status.
      A persisted TicketUser must already exist; its ID is required."""

        if type(admin_id) is not int or admin_id <= 0:
            raise ItemValidationError("Admin id must be positive")

        if type(user_id) is not int or user_id <= 0:
            raise ItemValidationError("User id must be positive")

        if type(user_ticket_id) is not int or user_ticket_id <= 0:
            raise ItemValidationError("User ticket id must be positive")
        return cls._create_new(
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            initial_status=TicketStatus.CREATED_FROM_REQUEST_USER,
            actor_employee_id=admin_id,
            comment_employee_id=admin_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
        )

    @classmethod
    def create_from_ticket_user(
            cls,
            *,
            client_id: int,
            user_id: int,
            user_ticket_id: int,
            text_of_ticket: str,
            contact_user_id: int = 0,
            description: str = "",
            department_id: int = 0,
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            comment: str = "",
    ) -> Self:
        """Create an internal Ticket from an existing TicketUser."""
        if user_id <= 0:
            raise ItemValidationError("User id must be positive")

        if user_ticket_id <= 0:
            raise ItemValidationError("User ticket id must be positive")

        return cls._create_new(
            client_id=client_id,
            text_of_ticket=text_of_ticket,
            initial_status=TicketStatus.CREATED_FROM_TICKET_USER,
            actor_employee_id=0,
            comment_employee_id=user_id,
            user_id=user_id,
            contact_user_id=contact_user_id,
            user_ticket_id=user_ticket_id,
            department_id=department_id,
            description=description,
            remote_work_recommended=remote_work_recommended,
            urgency=urgency,
            planned_at=planned_at,
            comment=comment,
        )

    @classmethod
    def rehydrate(
            cls,
            *,
            ticket_id: int,
            client_id: int,
            text_of_ticket: str,
            statuses: list[TicketStatusRecord],
            date_created: datetime,
            user_id: int = 0,
            contact_user_id: int = 0,
            comments: list[Comment] | None = None,
            department_id: int = 0,
            user_ticket_id: int = 0,
            description: str = "",
            remote_work_recommended: bool = False,
            urgency: TicketUrgency = TicketUrgency.NORMAL,
            planned_at: datetime | None = None,
            version: int = 0,
    ) -> Self:
        """Rehydrate using the first status, then replay the remaining history.

        Existing planned_at may be in the past. All status records are
        checked against the *current* workflow transition rules.
        """
        if ticket_id <= 0:
            raise DomainOperationError(
                "Cannot rehydrate Ticket with non-positive ticket_id"
            )

        if not statuses:
            raise DomainOperationError(
                "Cannot rehydrate Ticket without status history"
            )

        ticket = cls(
            ticket_id=ticket_id,
            client_id=client_id,
            text_of_ticket=TextOfTicket(text_of_ticket),
            user_id=user_id,
            contact_user_id=contact_user_id,
            statuses=statuses[:1],
            comments=comments if comments is not None else [],
            date_created=date_created,
            department_id=department_id,
            user_ticket_id=user_ticket_id,
            description=Description(description),
            remote_work_recommended=remote_work_recommended,
            urgency=TicketUrgency(urgency),
            planned_at=planned_at,
            version=version,
        )

        for status in statuses[1:]:
            ticket.append_status(status)

        return ticket

    # ==================================================================
    # Current state and executor
    # ==================================================================

    def current_status_record(self) -> TicketStatusRecord:
        if not self.statuses:
            raise DomainOperationError("Ticket has no status history")
        return self.statuses[-1]

    def current_status(self) -> TicketStatus:
        return self.current_status_record().status

    def is_terminal(self) -> bool:
        return self.current_status() in TERMINAL_TICKET_STATUSES

    def current_executor_id(self) -> int:
        """Return the active executor, or 0 when the state has none."""
        if not self.rule.has_executor:
            return 0

        for record in reversed(self.statuses):
            if not TICKET_STATE_RULES[record.status].has_executor:
                raise DomainOperationError(
                    "Active executor assignment history is broken"
                )

            if record.status == TicketStatus.ASSIGNED:
                return record.executor_id

        raise DomainOperationError(
            "Ticket is in executor-active status "
            "but has no preceding ASSIGNED record"
        )

    def last_executor_id(self) -> int:
        """Return the most recently assigned executor, even if inactive."""
        for record in reversed(self.statuses):
            if record.status == TicketStatus.ASSIGNED:
                return record.executor_id
        return 0

    # ==================================================================
    # Persistence helpers
    # ==================================================================

    def is_new(self) -> bool:
        return self.ticket_id == 0

    def new_statuses(self) -> list[TicketStatusRecord]:
        return [record for record in self.statuses if record.is_new()]

    def new_comments(self) -> list[Comment]:
        return [comment for comment in self.comments if comment.is_new()]

    # ==================================================================
    # Workflow
    # ==================================================================

    def append_status(self, record: TicketStatusRecord) -> None:
        """Append a validated workflow record for an allowed transition."""
        current_record = self.current_status_record()
        rule = TICKET_TRANSITIONS[current_record.status].get(record.status)

        if rule is None:
            raise DomainOperationError(
                "Ticket status transition is not allowed: "
                f"{current_record.status.value} -> {record.status.value}"
            )

        if record.date_created < current_record.date_created:
            raise DomainOperationError(
                "Ticket status history must be chronological"
            )

        for validator in rule.validators:
            validator(self, record)

        self.statuses.append(record)
        self._recompute_closed_state()

    # ==================================================================
    # Comments
    # ==================================================================

    def add_comment(self, comment: Comment) -> None:
        if self.is_terminal():
            raise DomainOperationError(
                f"Cannot add comment to terminal Ticket {self.ticket_id}"
            )

        if not comment.comment:
            raise DomainOperationError("Comment cannot be empty")

        validate_utc_datetime(
            comment.date_created,
            field_name="comment.date_created",
        )
        self.comments.append(comment)

    # ==================================================================
    # Editable Ticket data
    # ==================================================================

    def change_department(self, *, department_id: int) -> None:
        if department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative"
            )

        if not self.rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket department in current status "
                f"{self.current_status()}"
            )

        self.department_id = department_id

    def change_contact_user(self, *, contact_user_id: int) -> None:
        if not self.rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket contact User in current status "
                f"{self.current_status()}"
            )

        if contact_user_id < 0:
            raise DomainOperationError(
                "Ticket contact_user_id cannot be negative"
            )

        if self.user_id > 0 and contact_user_id == 0:
            raise DomainOperationError(
                "Ticket with user_id must have contact_user_id"
            )

        self.contact_user_id = contact_user_id

    def update_description(self, *, description: str) -> None:
        if not self.rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket description in current status "
                f"{self.current_status()}"
            )
        self.description = Description(description)

    def set_remote_work_recommended(self, *, recommend: bool) -> None:
        if not self.rule.can_change_data:
            raise DomainOperationError(
                "Cannot change remote work recommendation "
                f"in current status {self.current_status()}"
            )
        self.remote_work_recommended = recommend

    def change_urgency(self, *, urgency: TicketUrgency) -> None:
        if not self.rule.can_change_data:
            raise DomainOperationError(
                "Cannot change Ticket urgency in current status "
                f"{self.current_status()}"
            )

        if not isinstance(urgency, TicketUrgency):
            raise DomainOperationError("Invalid Ticket urgency")

        self.urgency = urgency

    # ==================================================================
    # Planning
    # ==================================================================

    def schedule(self, *, planned_at: datetime) -> None:
        if not self.rule.can_change_data:
            raise DomainOperationError(
                "Cannot set planned_at in current Ticket status"
            )

        self._validate_new_planned_at(
            planned_at,
            reference_time=datetime.now(UTC),
        )
        self.planned_at = planned_at

    def clear_schedule(self) -> None:
        if not self.rule.can_change_data:
            raise DomainOperationError(
                "Cannot clear planned_at in current Ticket status"
            )
        self.planned_at = None

    # ==================================================================
    # Analytics
    # ==================================================================

    def working_time(self) -> int:
        """Return total working time in seconds.

        Status records with rule.tracks_work_time=True contribute time.
        Their duration is taken from an explicit positive duration,
        an explicit actual start/finish interval, or the elapsed workflow
        interval to the next status (or now for a current work record).
        """
        total_seconds = 0
        now = datetime.now(UTC)

        for index, record in enumerate(self.statuses):
            if not record.rule.tracks_work_time:
                continue

            if record.duration:
                total_seconds += int(record.duration.total_seconds())
                continue

            if (
                    record.actual_started_at is not None
                    and record.actual_finished_at is not None
            ):
                total_seconds += int(
                    (
                            record.actual_finished_at - record.actual_started_at
                    ).total_seconds()
                )
                continue

            if index + 1 < len(self.statuses):
                finish_at = self.statuses[index + 1].date_created
            else:
                finish_at = now

            total_seconds += int((finish_at - record.date_created).total_seconds())

        return total_seconds

    # ==================================================================
    # Workflow commands
    # ==================================================================

    def accept(self, *, actor_employee_id: int, comment: str = "") -> None:
        record = TicketStatusRecord(
            status=TicketStatus.ACCEPTED,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def reject(self, *, actor_employee_id: int, comment: str) -> None:
        record = TicketStatusRecord(
            status=TicketStatus.REJECTED,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def defer(self, *, actor_employee_id: int, comment: str) -> None:
        record = TicketStatusRecord(
            status=TicketStatus.DEFERRED,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def suspend(self, *, actor_employee_id: int, comment: str = "") -> None:
        record = TicketStatusRecord(
            status=TicketStatus.SUSPENDED,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def assign(
            self,
            *,
            actor_employee_id: int,
            executor_id: int,
            comment: str = "",
    ) -> None:
        record = TicketStatusRecord(
            status=TicketStatus.ASSIGNED,
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        self.append_status(record)

    def start_work(
            self,
            *,
            actor_employee_id: int,
            work_is_remote: bool,
            comment: str = "",
    ) -> None:
        """Start live work from ASSIGNED (not a resume operation)."""
        self._require_current_status(
            TicketStatus.ASSIGNED,
            operation="start work",
        )
        record = TicketStatusRecord(
            status=TicketStatus.AT_WORK,
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )
        self.append_status(record)

    def register_work(
            self,
            *,
            actor_employee_id: int,
            work_is_remote: bool,
            actual_started_at: datetime | None = None,
            actual_finished_at: datetime | None = None,
            duration: timedelta = timedelta(0),
            comment: str = "",
    ) -> None:
        """Register completed work as ASSIGNED -> AT_WORK -> READY_FOR_REVIEW.

        At least one explicit duration or start/finish interval is required.
        Both records use the same registration timestamp. The operation
        rolls back its in-memory status changes if either append fails.
        """
        now = datetime.now(UTC)

        work_record = TicketStatusRecord(
            status=TicketStatus.AT_WORK,
            actor_employee_id=actor_employee_id,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            duration=duration,
            work_is_remote=work_is_remote,
            comment=comment,
            date_created=now,
        )

        if not work_record.has_retrospective_work_time:
            raise DomainOperationError(
                "Retrospective work requires an interval or duration"
            )

        review_record = TicketStatusRecord(
            status=TicketStatus.READY_FOR_REVIEW,
            actor_employee_id=actor_employee_id,
            date_created=now,
        )

        previous_status_count = len(self.statuses)
        try:
            self.append_status(work_record)
            self.append_status(review_record)
        except Exception:
            del self.statuses[previous_status_count:]
            self._recompute_closed_state()
            raise

    def pause_work(
            self,
            *,
            actor_employee_id: int,
            comment: str = "",
    ) -> None:
        self._require_current_status(
            TicketStatus.AT_WORK,
            operation="pause work",
        )
        record = TicketStatusRecord(
            status=TicketStatus.PAUSED,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def resume_work(
            self,
            *,
            actor_employee_id: int,
            work_is_remote: bool,
            comment: str = "",
    ) -> None:
        self._require_current_status(
            TicketStatus.PAUSED,
            operation="resume work",
        )
        record = TicketStatusRecord(
            status=TicketStatus.AT_WORK,
            actor_employee_id=actor_employee_id,
            work_is_remote=work_is_remote,
            comment=comment,
        )
        self.append_status(record)

    def submit_for_review(
            self,
            *,
            actor_employee_id: int,
            comment: str = "",
    ) -> None:
        """Submit work for review, according to the transition validator.

        Live work requires the current executor; retrospective work may be
        submitted by another Admin who registered that work.
        """
        self._require_current_status(
            TicketStatus.AT_WORK,
            operation="submit work for review",
        )
        record = TicketStatusRecord(
            status=TicketStatus.READY_FOR_REVIEW,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def confirm_by_user(self, *, comment: str = "") -> None:
        record = TicketStatusRecord(
            status=TicketStatus.CONFIRMED_BY_USER,
            actor_employee_id=0,
            comment=comment,
        )
        self.append_status(record)

    def execute(self, *, actor_employee_id: int, comment: str = "") -> None:
        record = TicketStatusRecord(
            status=TicketStatus.EXECUTED,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def cancel(self, *, actor_employee_id: int, comment: str) -> None:
        record = TicketStatusRecord(
            status=TicketStatus.CANCELLED,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )
        self.append_status(record)

    def cancel_by_user(self, *, comment: str = "") -> None:
        """Record user cancellation where allowed by the transition table."""
        record = TicketStatusRecord(
            status=TicketStatus.CANCELLED_BY_USER,
            actor_employee_id=0,
            comment=comment,
        )
        self.append_status(record)

    def start_remote_work(
            self,
            *,
            actor_employee_id: int,
            comment: str = "",
    ) -> None:
        """Start recommended remote work from ACCEPTED or ASSIGNED.

        From ACCEPTED, the actor is first assigned as executor and then
        begins work. Both status appends are atomic in memory.

        From ASSIGNED, only the current executor can start work and exactly
        one status record is appended.
        """
        if actor_employee_id <= 0:
            raise DomainOperationError("Actor employee id must be positive")

        if not self.remote_work_recommended:
            raise DomainOperationError(
                "Remote work is not recommended for this ticket"
            )

        current_status = self.current_status()
        if current_status == TicketStatus.ASSIGNED:
            if self.current_executor_id() != actor_employee_id:
                raise DomainOperationError(
                    "Ticket is assigned to another executor"
                )
        elif current_status != TicketStatus.ACCEPTED:
            raise DomainOperationError(
                "Remote work can be started only from "
                "ACCEPTED or ASSIGNED status"
            )

        now = datetime.now(UTC)
        work_record = TicketStatusRecord(
            status=TicketStatus.AT_WORK,
            actor_employee_id=actor_employee_id,
            work_is_remote=True,
            comment=comment,
            date_created=now,
        )

        assign_record = None
        if current_status == TicketStatus.ACCEPTED:
            assign_record = TicketStatusRecord(
                status=TicketStatus.ASSIGNED,
                actor_employee_id=actor_employee_id,
                executor_id=actor_employee_id,
                date_created=now,
            )

        previous_status_count = len(self.statuses)
        try:
            if assign_record is not None:
                self.append_status(assign_record)
            self.append_status(work_record)
        except Exception:
            del self.statuses[previous_status_count:]
            self._recompute_closed_state()
            raise

    # ==================================================================
    # Validation
    # ==================================================================

    def _validate_identity(self) -> None:
        """Validate basic identifiers and other stable aggregate fields."""
        if self.ticket_id < 0:
            raise DomainOperationError("Ticket ticket_id cannot be negative")

        if self.client_id <= 0:
            raise DomainOperationError("Ticket client_id must be positive")

        if self.user_id < 0:
            raise DomainOperationError("Ticket user_id cannot be negative")

        if self.contact_user_id < 0:
            raise DomainOperationError(
                "Ticket contact_user_id cannot be negative"
            )

        if self.user_ticket_id > 0 and self.user_id == 0:
            raise DomainOperationError(
                "Ticket linked to TicketUser must have user_id"
            )

        if self.user_id > 0 and self.contact_user_id == 0:
            raise DomainOperationError(
                "Ticket with user_id must have contact_user_id"
            )

        if self.department_id < 0:
            raise DomainOperationError(
                "Ticket department_id cannot be negative"
            )

        if self.version < 0:
            raise DomainOperationError("Ticket version cannot be negative")

        if not isinstance(self.urgency, TicketUrgency):
            raise DomainOperationError("Invalid Ticket urgency")

        if self.user_ticket_id < 0:
            raise DomainOperationError(
                "Ticket user_ticket_id cannot be negative"
            )

    def _validate_datetimes(self) -> None:
        """Validate timestamps owned directly by Ticket (not its records)."""
        validate_utc_datetime(self.date_created, field_name="date_created")

        if self.planned_at is not None:
            validate_utc_datetime(self.planned_at, field_name="planned_at")

    def _validate_creation_origin(self) -> None:
        """Validate requirements determined by the initial Ticket status."""
        first_status = self.statuses[0].status
        rule = TICKET_ORIGIN_RULES[first_status]

        if rule.requires_user_id and self.user_id <= 0:
            raise DomainOperationError(f"{first_status} requires user_id")

        if rule.requires_ticket_user_id and self.user_ticket_id <= 0:
            raise DomainOperationError(
                f"{first_status} requires user_ticket_id"
            )

    @classmethod
    def _validate_new_planned_at(
            cls,
            planned_at: datetime,
            *,
            reference_time: datetime,
    ) -> None:
        """Validate a newly set planned time against today's UTC date."""
        validate_utc_datetime(planned_at, field_name="planned_at")
        validate_utc_datetime(
            reference_time,
            field_name="planning reference_time",
        )
        if planned_at.date() < reference_time.date():
            raise DomainOperationError(
                "planned_at cannot be earlier than today"
            )

    # ==================================================================
    # Derived state and semantic command helpers
    # ==================================================================

    def _recompute_closed_state(self) -> None:
        self.is_closed = self.is_terminal()
        if self.is_closed:
            self.date_finished = self.current_status_record().date_created
        else:
            self.date_finished = None

    def _require_current_status(
            self,
            status: TicketStatus,
            *,
            operation: str,
    ) -> None:
        """Enforce the meaning of a specific public workflow command."""
        current_status = self.current_status()
        if current_status != status:
            raise DomainOperationError(
                f"Cannot {operation} when Ticket is in status "
                f"{current_status.value}; expected {status.value}"
            )
