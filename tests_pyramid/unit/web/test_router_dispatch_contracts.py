from __future__ import annotations

import ast
import inspect

import pytest
from fastapi.routing import APIRoute

from src.web.main import create_app

pytestmark = pytest.mark.web


# The web layer is intentionally thin. This table freezes which application/auth
# service owns every public endpoint. Request payload mapping is covered separately.
EXPECTED_DISPATCH = {
    ("POST", "/auth/admin/login"): "auth_manager.login",
    ("POST", "/auth/admin/refresh"): "auth_manager.refresh",
    ("POST", "/auth/admin/logout"): "auth_manager.logout",
    ("POST", "/auth/user/login"): "auth_manager.login",
    ("POST", "/auth/user/refresh"): "auth_manager.refresh",
    ("POST", "/auth/user/logout"): "auth_manager.logout",

    ("POST", "/admin/clients/"): "client_service.create_client",
    ("GET", "/admin/clients/"): "client_service.get_all",
    ("GET", "/admin/clients/{client_id}"): "client_service.get_by_id",
    ("PUT", "/admin/clients/{client_id}/contact"): "client_service.update_contact",
    ("PATCH", "/admin/clients/{client_id}/disable"): "client_service.disable",
    ("PATCH", "/admin/clients/{client_id}/enable"): "client_service.enable",
    ("DELETE", "/admin/clients/{client_id}"): "client_service.delete",

    ("POST", "/admin/admins/"): "admin_service.create_admin",
    ("GET", "/admin/admins/"): "admin_service.get_all",
    ("GET", "/admin/admins/permissions"): "admin_service.get_permissions",
    ("GET", "/admin/admins/by-login/{login}"): "admin_service.find_by_login",
    ("GET", "/admin/admins/{employee_id}"): "admin_service.get_by_id",
    ("PUT", "/admin/admins/{employee_id}"): "admin_service.update_admin",
    ("POST", "/admin/admins/{employee_id}/account"): "admin_service.attach_account",
    ("DELETE", "/admin/admins/{employee_id}/account"): "admin_service.detach_account",
    ("PATCH", "/admin/admins/{employee_id}/password"): "admin_service.change_password",
    ("POST", "/admin/admins/{employee_id}/roles"): "admin_service.grant_role",
    ("DELETE", "/admin/admins/{employee_id}/roles"): "admin_service.revoke_role",
    ("PATCH", "/admin/admins/{employee_id}/disable"): "admin_service.disable",
    ("PATCH", "/admin/admins/{employee_id}/enable"): "admin_service.enable",
    ("DELETE", "/admin/admins/{employee_id}"): "admin_service.delete",
    ("PATCH", "/admin/admins/{employee_id}/department"): "admin_service.change_department",
    ("DELETE", "/admin/admins/{employee_id}/department"): "admin_service.remove_department",

    ("POST", "/admin/users/"): "user_service.create_user",
    # GET collection is conditional: all users or users by client.
    ("GET", "/admin/users/"): {"user_service.get_all", "user_service.get_by_client_id"},
    ("GET", "/admin/users/by-login/{login}"): "user_service.find_by_login",
    ("GET", "/admin/users/{employee_id}"): "user_service.get_by_id",
    ("PUT", "/admin/users/{employee_id}"): "user_service.update_user",
    ("POST", "/admin/users/{employee_id}/account"): "user_service.attach_account",
    ("DELETE", "/admin/users/{employee_id}/account"): "user_service.detach_account",
    ("PATCH", "/admin/users/{employee_id}/password"): "user_service.change_password",
    ("POST", "/admin/users/{employee_id}/roles"): "user_service.grant_role",
    ("DELETE", "/admin/users/{employee_id}/roles"): "user_service.revoke_role",
    ("PATCH", "/admin/users/{employee_id}/disable"): "user_service.disable",
    ("PATCH", "/admin/users/{employee_id}/enable"): "user_service.enable",
    ("DELETE", "/admin/users/{employee_id}"): "user_service.delete",

    ("POST", "/admin/departments/"): "department_service.create_department",
    ("GET", "/admin/departments/"): "department_service.get_all",
    ("GET", "/admin/departments/{department_id}"): "department_service.get_by_id",
    ("PUT", "/admin/departments/{department_id}"): "department_service.update_department",
    ("PATCH", "/admin/departments/{department_id}/enable"): "department_service.enable_department",
    ("PATCH", "/admin/departments/{department_id}/disable"): "department_service.disable_department",
    ("DELETE", "/admin/departments/{department_id}"): "department_service.delete_department",

    ("POST", "/admin/roles/admin"): "admin_role_service.create_role",
    ("GET", "/admin/roles/admin"): "admin_role_service.get_all_roles",
    ("GET", "/admin/roles/admin/{role_id}"): "admin_role_service.get_role",
    ("DELETE", "/admin/roles/admin/{role_id}"): "admin_role_service.delete_role",
    ("POST", "/admin/roles/user"): "user_role_service.create_role",
    ("GET", "/admin/roles/user"): "user_role_service.get_all_roles",
    ("GET", "/admin/roles/user/{role_id}"): "user_role_service.get_role",
    ("DELETE", "/admin/roles/user/{role_id}"): "user_role_service.delete_role",

    ("POST", "/admin/tickets/"): "ticket_service.create_ticket",
    # Search service is postponed. The active collection endpoint must use get_all.
    ("GET", "/admin/tickets/"): "ticket_service.get_all",
    ("GET", "/admin/tickets/all"): "ticket_service.get_all",
    ("GET", "/admin/tickets/{ticket_id}"): "ticket_service.get_by_id",
    ("PATCH", "/admin/tickets/{ticket_id}/details"): "ticket_service.update_details",
    ("PATCH", "/admin/tickets/{ticket_id}/department"): "ticket_service.change_department",
    ("PATCH", "/admin/tickets/{ticket_id}/accept"): "ticket_service.accept",
    ("PATCH", "/admin/tickets/{ticket_id}/reject"): "ticket_service.reject",
    ("PATCH", "/admin/tickets/{ticket_id}/defer"): "ticket_service.defer",
    ("PATCH", "/admin/tickets/{ticket_id}/schedule"): "ticket_service.schedule",
    ("PATCH", "/admin/tickets/{ticket_id}/executor"): "ticket_service.assign_executor",
    ("PATCH", "/admin/tickets/{ticket_id}/ready-to-work"): "ticket_service.ready_to_work",
    ("PATCH", "/admin/tickets/{ticket_id}/at-work"): "ticket_service.at_work",
    ("PATCH", "/admin/tickets/{ticket_id}/pause"): "ticket_service.pause_work",
    ("PATCH", "/admin/tickets/{ticket_id}/resume"): "ticket_service.resume_work",
    ("PATCH", "/admin/tickets/{ticket_id}/submit-for-review"): "ticket_service.submit_for_review",
    ("PATCH", "/admin/tickets/{ticket_id}/record-completed-work-for-review"): "ticket_service.record_completed_work_for_review",
    ("PATCH", "/admin/tickets/{ticket_id}/confirm-execution"): "ticket_service.confirm_execution",
    ("PATCH", "/admin/tickets/{ticket_id}/execute"): "ticket_service.execute",
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-work"): "ticket_service.return_to_work",
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-assigned"): "ticket_service.return_to_assigned",
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-scheduled"): "ticket_service.return_to_scheduled",
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-ready-to-work"): "ticket_service.return_to_ready_to_work",
    ("PATCH", "/admin/tickets/{ticket_id}/return-to-deferred"): "ticket_service.return_to_deferred",
    ("PATCH", "/admin/tickets/{ticket_id}/cancel"): "ticket_service.cancel",
    ("POST", "/admin/tickets/{ticket_id}/comments"): "ticket_service.add_comment",
    ("DELETE", "/admin/tickets/{ticket_id}"): "ticket_service.delete",

    ("POST", "/user/tickets/"): "service.create_from_user",
    ("GET", "/user/tickets/"): "service.get_by_user",
    ("GET", "/user/tickets/{ticket_user_id}"): "service.get_by_id",
    ("PATCH", "/user/tickets/{ticket_user_id}/cancel"): "service.cancel_by_user",
    ("PATCH", "/user/tickets/{ticket_user_id}/confirm-execution"): "service.confirm_execution_by_user",
}


def _calls(endpoint) -> set[str]:
    tree = ast.parse(inspect.getsource(endpoint))
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        # asf.foo_service().method(...)
        owner = node.func.value
        if isinstance(owner, ast.Call) and isinstance(owner.func, ast.Attribute):
            base = owner.func.value
            if isinstance(base, ast.Name) and base.id == "asf":
                found.add(f"{owner.func.attr}.{node.func.attr}")
        # direct injected service.method(...) / auth_manager.method(...)
        if isinstance(owner, ast.Name) and owner.id in {"service", "auth_manager"}:
            found.add(f"{owner.id}.{node.func.attr}")
    return found


def test_every_service_backed_route_dispatches_to_the_expected_application_service() -> None:
    app = create_app()
    actual = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods:
            key = (method, route.path)
            if key not in EXPECTED_DISPATCH:
                continue
            calls = _calls(route.endpoint)
            expected = EXPECTED_DISPATCH[key]
            if isinstance(expected, set):
                assert calls == expected, key
            else:
                assert calls == {expected}, key
            actual[key] = calls
    assert set(actual) == set(EXPECTED_DISPATCH)
