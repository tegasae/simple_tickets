from dataclasses import dataclass, field
from datetime import datetime




@dataclass(kw_only=True)
class TicketDTO:
    """
    Command DTO for the internal Ticket aggregate.

    `status` is intentionally absent.
    Each workflow transition must be performed by a dedicated
    application-service use case.
    """

    actor_admin_id: int

    ticket_id: int = 0

    client_id: int = 0
    admin_id: int = 0

    user_id: int = 0
    contact_user_id: int = 0
    user_ticket_id: int = 0

    department_id: int = 0

    text_of_ticket: str = ""
    description: str = ""

    is_remote: bool = False
    urgency_level: int = 0

    executor_id: int = 0
    comment: str = ""

    planned_start_at: datetime | None = None
    planned_finish_at: datetime | None = None

    actual_started_at: datetime | None = None
    actual_finished_at: datetime | None = None

    def __post_init__(self) -> None:
        # By default, the actor creates the Ticket on their own behalf.
        self.admin_id = self.admin_id or self.actor_admin_id


@dataclass(kw_only=True, frozen=True)
class TicketResponseDTO:
    ticket_id: int

    client_id: int
    admin_id: int

    user_id: int
    contact_user_id: int
    user_ticket_id: int

    department_id: int

    text_of_ticket: str
    description: str

    date_created:datetime
    date_finished: datetime | None

    is_remote: bool
    urgency_level: int

    version: int
    is_closed: bool
    time_spent:int=0

    statuses: list[dict[str, object]] = field(default_factory=list)
    comments: list[dict[str, object]] = field(default_factory=list)


# -------------------------------------------------------------------
# TicketUser DTOs
#
# TicketUser is still a separate legacy aggregate. These DTOs remain
# unchanged until its workflow is redesigned separately.
# -------------------------------------------------------------------

@dataclass(kw_only=True, frozen=True)
class TicketUserDTO:
    ticket_user_id: int
    client_id: int
    actor_user_id: int
    text_of_ticket: str

    contact_user_id: int = 0
    department_id: int = 0

    is_remote: bool = False

    description: str = ""
    urgency_level: int = 0

    comment: str = ""




@dataclass(kw_only=True, frozen=True)
class TicketUserResponseDTO:
    """
    DTO пользовательской заявки.

    Это не внутренняя Ticket.
    ticket_id здесь — id агрегата TicketUser.
    Связь с внутренней Ticket хранится
    на стороне Ticket.user_ticket_id.
    """

    ticket_id: int
    client_id: int

    user_id: int
    contact_user_id: int

    text_of_ticket: str
    description: str
    urgency_level: int

    current_status: str
    is_closed: bool

    date_created: str
    date_finished: str | None

    statuses: list[dict[str, object]] = field(
        default_factory=list,
    )
    comments: list[dict[str, object]] = field(
        default_factory=list,
    )