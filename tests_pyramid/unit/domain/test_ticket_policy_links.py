from __future__ import annotations

from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit

from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket import TicketPolicy


TICKET_ID = 1001
TICKET_USER_ID = 5001
CLIENT_ID = 10
USER_ID = 20
CONTACT_USER_ID = 30


def make_ticket(**overrides: int) -> SimpleNamespace:
    data = {
        "ticket_id": TICKET_ID,
        "user_ticket_id": TICKET_USER_ID,
        "client_id": CLIENT_ID,
        "user_id": USER_ID,
        "contact_user_id": CONTACT_USER_ID,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_ticket_user(**overrides: int) -> SimpleNamespace:
    data = {
        "ticket_id": TICKET_USER_ID,
        "client_id": CLIENT_ID,
        "user_id": USER_ID,
        "contact_user_id": CONTACT_USER_ID,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_matching_linked_ticket_and_ticket_user_are_accepted() -> None:
    TicketPolicy.ensure_ticket_matches_ticket_user(
        ticket=make_ticket(),
        ticket_user=make_ticket_user(),
    )


def test_link_mismatch_is_rejected() -> None:
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_matches_ticket_user(
            ticket=make_ticket(user_ticket_id=TICKET_USER_ID + 1),
            ticket_user=make_ticket_user(),
        )


def test_client_mismatch_is_rejected() -> None:
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_matches_ticket_user(
            ticket=make_ticket(),
            ticket_user=make_ticket_user(client_id=CLIENT_ID + 1),
        )


def test_user_mismatch_is_rejected() -> None:
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_matches_ticket_user(
            ticket=make_ticket(),
            ticket_user=make_ticket_user(user_id=USER_ID + 1),
        )


def test_contact_user_mismatch_is_rejected() -> None:
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_matches_ticket_user(
            ticket=make_ticket(),
            ticket_user=make_ticket_user(
                contact_user_id=CONTACT_USER_ID + 1,
            ),
        )
