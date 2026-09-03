from dataclasses import dataclass, field
from datetime import datetime


@dataclass(kw_only=True)
class TicketDTO:
    """
    Command DTO for the internal Ticket aggregate.

    `status` is intentionally absent.
    Each workflow transition must be performed by a dedicated
    application-service use case.

    `admin_id` is intentionally absent.

    When a Ticket is created directly by Admin,
    Ticket.admin_id is determined from actor_admin_id
    inside the application service.

    When a Ticket is created automatically from TicketUser,
    Ticket.admin_id is set to 0 by the Ticket aggregate factory.
    """

    actor_admin_id: int

    ticket_id: int = 0

    client_id: int = 0

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


@dataclass(kw_only=True, frozen=True)
class TicketResponseDTO:
    """
    Response DTO for the internal Ticket aggregate.

    admin_id:
        Admin who originally created the internal Ticket.

        For a Ticket created automatically from TicketUser:
            admin_id == 0.

        Workflow actors, including the Admin who accepted
        the Ticket, are stored in status records.
    """

    ticket_id: int

    client_id: int
    admin_id: int

    user_id: int
    contact_user_id: int
    user_ticket_id: int

    department_id: int

    text_of_ticket: str
    description: str

    date_created: datetime
    date_finished: datetime | None

    is_remote: bool
    urgency_level: int

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
    Command DTO for TicketUser-related use cases.

    department_id and is_remote belong to the internal Ticket,
    but may be required by the application service when creating
    a linked Ticket together with TicketUser.
    """

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