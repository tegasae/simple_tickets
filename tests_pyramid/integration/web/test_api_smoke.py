from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.domain.exceptions import DomainOperationError
from src.web.dependencies.auth import (
    get_current_admin,
    get_current_user,
    get_employee_id_from_request,
)
from src.web.dependencies.services import (
    get_application_service_factory,
    get_ticket_user_service,
)
from src.web.main import create_app

pytestmark = [pytest.mark.integration, pytest.mark.web]


def _ticket_response(ticket_id: int = 1) -> dict:
    return {
        "ticket_id": ticket_id,
        "client_id": 10,
        "admin_id": 101,
        "user_id": 0,
        "contact_user_id": 0,
        "user_ticket_id": 0,
        "department_id": 0,
        "text_of_ticket": "Need help",
        "description": "",
        "date_created": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "date_finished": None,
        "is_remote": False,
        "urgency_level": 0,
        "version": 0,
        "is_closed": False,
        "time_spent": 0,
        "statuses": [],
        "comments": [],
    }


def _user_ticket_response(ticket_id: int = 1) -> dict:
    return {
        "ticket_id": ticket_id,
        "client_id": 10,
        "user_id": 202,
        "contact_user_id": 0,
        "text_of_ticket": "Need help",
        "description": "",
        "urgency_level": 0,
        "current_status": "created",
        "is_closed": False,
        "date_created": "2026-01-01T00:00:00+00:00",
        "date_finished": None,
        "statuses": [],
        "comments": [],
    }


class FakeTicketService:
    def __init__(self) -> None:
        self.created_dto = None
        self.fail = False

    def create_ticket(self, *, ticket_dto):
        self.created_dto = ticket_dto
        if self.fail:
            raise DomainOperationError("cannot create")
        return _ticket_response()

    def get_all(self, *, ticket_dto):
        return [_ticket_response()]


class FakeFactory:
    def __init__(self, ticket_service: FakeTicketService) -> None:
        self._ticket_service = ticket_service

    def ticket_service(self):
        return self._ticket_service


class FakeTicketUserService:
    def __init__(self) -> None:
        self.created_dto = None

    def create_from_user(self, *, ticket_user_dto):
        self.created_dto = ticket_user_dto
        return _user_ticket_response()


def _client_with_admin(ticket_service: FakeTicketService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_admin] = lambda: None
    app.dependency_overrides[get_employee_id_from_request] = lambda: 101
    app.dependency_overrides[get_application_service_factory] = lambda: FakeFactory(ticket_service)
    return TestClient(app)


def test_health_endpoint() -> None:
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_ticket_create_wires_authenticated_actor_into_command_dto() -> None:
    service = FakeTicketService()
    client = _client_with_admin(service)

    response = client.post(
        "/admin/tickets/",
        json={"client_id": 10, "text_of_ticket": "Need help"},
    )

    assert response.status_code == 201
    assert response.json()["ticket_id"] == 1
    assert service.created_dto.actor_admin_id == 101
    assert service.created_dto.client_id == 10
    assert service.created_dto.text_of_ticket == "Need help"
    assert not hasattr(service.created_dto, "admin_id")


def test_admin_ticket_domain_error_is_mapped_to_http_400() -> None:
    service = FakeTicketService()
    service.fail = True
    client = _client_with_admin(service)

    response = client.post(
        "/admin/tickets/",
        json={"client_id": 10, "text_of_ticket": "Need help"},
    )

    assert response.status_code == 400
    assert response.json()["error_type"] == "DomainOperationError"


def test_user_ticket_create_wires_authenticated_user_into_command_dto() -> None:
    app = create_app()
    service = FakeTicketUserService()
    app.dependency_overrides[get_current_user] = lambda: None
    app.dependency_overrides[get_employee_id_from_request] = lambda: 202
    app.dependency_overrides[get_ticket_user_service] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/user/tickets/",
        json={"client_id": 10, "text_of_ticket": "Need help"},
    )

    assert response.status_code == 201
    assert response.json()["ticket_id"] == 1
    assert service.created_dto.actor_user_id == 202
    assert service.created_dto.client_id == 10
    assert service.created_dto.ticket_user_id == 0
