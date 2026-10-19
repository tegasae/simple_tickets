from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from src.domain.exceptions import DomainOperationError, ItemNotFoundError
from src.web.dependencies import auth as auth_dep
from src.web.execeptions.exception_handlers import ExceptionHandlerRegistry

pytestmark = pytest.mark.unit


def _request(path: str = "/x") -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("test", 80),
            "scheme": "http",
            "http_version": "1.1",
        }
    )


def test_require_current_admin_and_user_enforce_realm() -> None:
    assert auth_dep.require_current_admin({"subject_type": "admin", "sub": "10"}) == 10
    assert auth_dep.require_current_user({"subject_type": "user", "sub": "20"}) == 20

    with pytest.raises(HTTPException) as exc:
        auth_dep.require_current_admin({"subject_type": "user", "sub": "20"})
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc:
        auth_dep.require_current_user({"subject_type": "admin", "sub": "10"})
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_auth_dependency_stores_employee_id_on_request(monkeypatch) -> None:
    request = _request()

    class FakeAccess:
        def get_admin_id(self) -> int:
            return 101

        def get_user_id(self) -> int:
            return 202

    monkeypatch.setattr(
        auth_dep.TokenService,
        "verify_access_token",
        staticmethod(lambda token: FakeAccess()),
    )

    await auth_dep.get_current_admin(request, token="x")
    assert await auth_dep.get_employee_id_from_request(request) == 101

    await auth_dep.get_current_user(request, token="x")
    assert await auth_dep.get_employee_id_from_request(request) == 202


def test_auth_manager_dependencies_keep_realms_separate() -> None:
    uow = SimpleNamespace()
    admin_manager = auth_dep.get_auth_manager_admin(uow)
    user_manager = auth_dep.get_auth_manager_user(uow)
    assert admin_manager.subject_type == "admin"
    assert user_manager.subject_type == "user"
    assert admin_manager.auth_service.__class__.__name__ == "AdminAuthService"
    assert user_manager.auth_service.__class__.__name__ == "UserAuthService"


def test_exception_registry_standard_handler_returns_expected_json() -> None:
    app = FastAPI()
    registry = ExceptionHandlerRegistry(app, expose_error_type=True)
    registry.add_standard_handler(
        exception_type=DomainOperationError,
        status_code=400,
    )
    registry.register_all()

    @app.get("/boom")
    def boom():
        raise DomainOperationError("bad operation")

    response = TestClient(app).get("/boom")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Operation failed: bad operation",
        "error_type": "DomainOperationError",
    }


def test_exception_registry_can_register_multiple_and_dynamic_handlers() -> None:
    app = FastAPI()
    registry = ExceptionHandlerRegistry(app)
    registry.add_all_standard_handlers(
        exceptions={DomainOperationError: 400, ItemNotFoundError: 404}
    )
    registry.add_all_handlers_from_module(
        module_name="src.domain.exceptions",
        exceptions={"ItemNotFoundError": 404, "DefinitelyMissing": 418},
    )
    registry.register_all()

    assert DomainOperationError in app.exception_handlers
    assert ItemNotFoundError in app.exception_handlers
    assert registry._get_exception_class(
        module_name="src.domain.exceptions",
        class_name="DefinitelyMissing",
    ) is None


def test_exception_registry_validates_exception_type() -> None:
    app = FastAPI()
    registry = ExceptionHandlerRegistry(app)
    with pytest.raises(TypeError):
        registry.add_standard_handler(exception_type=str, status_code=400)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        registry.add_handler(123, lambda request, exc: None)  # type: ignore[arg-type]


def test_exception_registry_error_content_flags() -> None:
    app = FastAPI()
    registry = ExceptionHandlerRegistry(
        app,
        expose_error_type=False,
        expose_traceback=False,
    )
    content = registry._make_error_content(
        exc=ValueError("x"),
        detail="safe",
    )
    assert content == {"detail": "safe"}
