from __future__ import annotations

import pytest
from fastapi.routing import APIRoute

from src.web.main import create_app

pytestmark = pytest.mark.web


EXPECTED_ROUTES = {
    ("POST", "/auth/admin/login", 200),
    ("POST", "/auth/admin/refresh", 200),
    ("POST", "/auth/admin/logout", 200),
    ("POST", "/auth/user/login", 200),
    ("POST", "/auth/user/refresh", 200),
    ("POST", "/auth/user/logout", 200),

    ("POST", "/admin/clients/", 201),
    ("GET", "/admin/clients/", 200),
    ("GET", "/admin/clients/{client_id}", 200),
    ("PUT", "/admin/clients/{client_id}/contact", 200),
    ("PATCH", "/admin/clients/{client_id}/disable", 200),
    ("PATCH", "/admin/clients/{client_id}/enable", 200),
    ("DELETE", "/admin/clients/{client_id}", 204),

    ("POST", "/admin/admins/", 201),
    ("GET", "/admin/admins/", 200),
    ("GET", "/admin/admins/permissions", 200),
    ("GET", "/admin/admins/by-login/{login}", 200),
    ("GET", "/admin/admins/{employee_id}", 200),
    ("PUT", "/admin/admins/{employee_id}", 200),
    ("POST", "/admin/admins/{employee_id}/account", 200),
    ("DELETE", "/admin/admins/{employee_id}/account", 200),
    ("PATCH", "/admin/admins/{employee_id}/password", 200),
    ("POST", "/admin/admins/{employee_id}/roles", 200),
    ("DELETE", "/admin/admins/{employee_id}/roles", 200),
    ("PATCH", "/admin/admins/{employee_id}/disable", 200),
    ("PATCH", "/admin/admins/{employee_id}/enable", 200),
    ("DELETE", "/admin/admins/{employee_id}", 204),
    ("PATCH", "/admin/admins/{employee_id}/department", 200),
    ("DELETE", "/admin/admins/{employee_id}/department", 200),

    ("POST", "/admin/users/", 201),
    ("GET", "/admin/users/", 200),
    ("GET", "/admin/users/by-login/{login}", 200),
    ("GET", "/admin/users/{employee_id}", 200),
    ("PUT", "/admin/users/{employee_id}", 200),
    ("POST", "/admin/users/{employee_id}/account", 200),
    ("DELETE", "/admin/users/{employee_id}/account", 200),
    ("PATCH", "/admin/users/{employee_id}/password", 200),
    ("POST", "/admin/users/{employee_id}/roles", 200),
    ("DELETE", "/admin/users/{employee_id}/roles", 200),
    ("PATCH", "/admin/users/{employee_id}/disable", 200),
    ("PATCH", "/admin/users/{employee_id}/enable", 200),
    ("DELETE", "/admin/users/{employee_id}", 204),

    ("POST", "/admin/departments/", 201),
    ("GET", "/admin/departments/", 200),
    ("GET", "/admin/departments/{department_id}", 200),
    ("PUT", "/admin/departments/{department_id}", 200),
    ("PATCH", "/admin/departments/{department_id}/enable", 200),
    ("PATCH", "/admin/departments/{department_id}/disable", 200),
    ("DELETE", "/admin/departments/{department_id}", 204),

    ("GET", "/admin/roles/admin/permissions", 200),
    ("GET", "/admin/roles/user/permissions", 200),
    ("POST", "/admin/roles/admin", 201),
    ("GET", "/admin/roles/admin", 200),
    ("GET", "/admin/roles/admin/{role_id}", 200),
    ("DELETE", "/admin/roles/admin/{role_id}", 204),
    ("POST", "/admin/roles/user", 201),
    ("GET", "/admin/roles/user", 200),
    ("GET", "/admin/roles/user/{role_id}", 200),
    ("DELETE", "/admin/roles/user/{role_id}", 204),

    ("POST", "/admin/tickets/", 201),
    ("GET", "/admin/tickets/", 200),
    ("GET", "/admin/tickets/all", 200),
    ("GET", "/admin/tickets/{ticket_id}", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/details", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/department", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/accept", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/reject", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/defer", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/schedule", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/executor", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/ready-to-work", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/at-work", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/pause", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/resume", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/submit-for-review", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/record-completed-work-for-review", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/confirm-execution", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/execute", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-work", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-assigned", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-scheduled", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-ready-to-work", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-deferred", 200),
    ("PATCH", "/admin/tickets/{ticket_id}/cancel", 200),
    ("POST", "/admin/tickets/{ticket_id}/comments", 200),
    ("DELETE", "/admin/tickets/{ticket_id}", 204),

    ("POST", "/user/tickets/", 201),
    ("GET", "/user/tickets/", 200),
    ("GET", "/user/tickets/{ticket_user_id}", 200),
    ("PATCH", "/user/tickets/{ticket_user_id}/cancel", 200),
    ("PATCH", "/user/tickets/{ticket_user_id}/confirm-execution", 200),

    ("GET", "/health", 200),
}


def _public_routes() -> set[tuple[str, str, int]]:
    app = create_app()
    result: set[tuple[str, str, int]] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        status_code = route.status_code or 200
        for method in route.methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            result.add((method, route.path, status_code))
    return result


def test_all_public_backend_routes_are_registered_with_expected_contracts() -> None:
    assert _public_routes() == EXPECTED_ROUTES


def test_route_names_are_unique_per_method_and_path() -> None:
    app = create_app()
    keys = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods:
                if method not in {"HEAD", "OPTIONS"}:
                    keys.append((method, route.path))
    assert len(keys) == len(set(keys))
