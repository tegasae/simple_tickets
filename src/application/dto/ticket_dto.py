from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.domain.ticket import TicketUrgency


@dataclass(kw_only=True)
class TicketDTO:
    actor_admin_id: int

    ticket_id: int = 0

    client_id: int = 0

    user_id: int = 0
    contact_user_id: int = 0
    user_ticket_id: int = 0

    department_id: int = 0

    text_of_ticket: str = ""
    description: str = ""

    # Ticket-level recommendation.
    remote_work_recommended: bool = False

    # Actual mode of one work episode.
    work_is_remote: bool = False

    urgency: str=TicketUrgency.NORMAL.value

    executor_id: int = 0
    comment: str = ""

    planned_at: datetime | None = None

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    duration: timedelta = field(
        default_factory=timedelta,
    )

@dataclass(kw_only=True, frozen=True)
class TicketResponseDTO:
    """
    Response DTO for the internal Ticket aggregate.

    Workflow actors are stored in status records.

    Ticket creation source is represented by the first workflow status:

        CREATED
        CREATED_FROM_TICKET_USER

    The DTO does not contain admin_id because Ticket no longer stores
    the creator as a separate aggregate field.
    """

    ticket_id: int

    client_id: int

    user_id: int
    contact_user_id: int
    user_ticket_id: int

    department_id: int

    text_of_ticket: str
    description: str

    date_created: datetime
    date_finished: datetime | None

    planned_at: datetime | None

    remote_work_recommended: bool

    urgency: str

    version: int
    is_closed: bool

    time_spent: int = 0

    statuses: list[dict[str, object]] = field(
        default_factory=list,
    )

    comments: list[dict[str, object]] = field(
        default_factory=list,
    )

# -------------------------------------------------------------------
# TicketUser DTOs
#
# TicketUser is a separate aggregate representing
# the user-facing ticket workflow.
# -------------------------------------------------------------------





@dataclass(kw_only=True, frozen=True)
class TicketUserDTO:
    """
    Command DTO for TicketUser use cases.

    actor_user_id:
        User performing the use case.

    user_id:
        Target User for query use cases.
        New TicketUser created by User always belongs to actor_user_id.

    department_id, remote_work_recommended and urgency belong to
    the linked internal Ticket and are used during creation.
    """

    actor_user_id: int

    ticket_user_id: int = 0
    client_id: int = 0
    user_id: int = 0

    text_of_ticket: str = ""

    contact_user_id: int = 0
    department_id: int = 0

    description: str = ""

    remote_work_recommended: bool = False
    urgency: TicketUrgency = TicketUrgency.NORMAL

    comment: str = ""


@dataclass(kw_only=True, frozen=True)
class TicketUserResponseDTO:
    """
    Response DTO for TicketUser aggregate.

    Internal Ticket identity is intentionally not exposed here.
    The link is stored on:

        Ticket.user_ticket_id
    """

    ticket_user_id: int

    client_id: int
    user_id: int
    contact_user_id: int

    text_of_ticket: str
    description: str

    current_status: str

    date_created: datetime
    date_finished: datetime | None

    version: int
    is_closed: bool

    statuses: list[dict[str, object]] = field(
        default_factory=list,
    )

    comments: list[dict[str, object]] = field(
        default_factory=list,
    )