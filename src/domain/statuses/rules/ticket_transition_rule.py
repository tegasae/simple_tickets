from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.ticket import Ticket
    from src.domain.statuses.ticket_status_record import TicketStatusRecord


type TransitionValidator = Callable[
    [Ticket, TicketStatusRecord],
    None,
]


@dataclass(frozen=True, slots=True)
class TicketTransitionRule:
    """
    Rules for a transition between two Ticket statuses.

    validators:
        Functions that validate the transition
        using Ticket context and the new status record.

    Each validator:
        - returns None if validation succeeds;
        - raises DomainOperationError if validation fails.

    An empty tuple means that the transition
    requires no additional validation.
    """

    validators: tuple[TransitionValidator, ...] = ()




