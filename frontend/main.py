from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .api_client import BackendApiError, BackendClient
from .config import settings


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Simple Tickets Frontend",
    version="0.1.1",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates",
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class ClientCreatePayload(BaseModel):
    name: str = Field(min_length=1)
    email: str = ""
    address: str = ""
    phone: str = ""


class ClientContactPayload(BaseModel):
    email: str = ""
    address: str = ""
    phone: str = ""


class ClientEnabledPayload(BaseModel):
    enabled: bool


# ---------------------------------------------------------------------------
# Auth/cookie helpers must be defined before they are used in Depends(...).
# ---------------------------------------------------------------------------


def _require_access_token(request: Request) -> str:
    access_token = _get_access_token(request)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return access_token


def _get_access_token(request: Request) -> str:
    return request.cookies.get(settings.access_cookie_name, "")


def _get_refresh_token(request: Request) -> str:
    return request.cookies.get(settings.refresh_cookie_name, "")


def _set_access_cookie(response: Response, access_token: str) -> None:
    response.set_cookie(
        key=settings.access_cookie_name,
        value=access_token,
        max_age=settings.access_cookie_max_age_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_cookie_max_age_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


def _delete_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.access_cookie_name,
        path="/",
    )
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/",
    )


def _extract_access_token(token_data: dict[str, Any]) -> str:
    candidates = (
        "access_token",
        "token",
        "access",
        "jwt",
    )

    for key in candidates:
        value = token_data.get(key)

        if isinstance(value, str) and value:
            return value

    nested_data = token_data.get("data")

    if isinstance(nested_data, dict):
        for key in candidates:
            value = nested_data.get(key)

            if isinstance(value, str) and value:
                return value

    return ""


def _extract_refresh_token(token_data: dict[str, Any]) -> str:
    candidates = (
        "refresh_token",
        "refresh",
    )

    for key in candidates:
        value = token_data.get(key)

        if isinstance(value, str) and value:
            return value

    nested_data = token_data.get("data")

    if isinstance(nested_data, dict):
        for key in candidates:
            value = nested_data.get(key)

            if isinstance(value, str) and value:
                return value

    return ""


def _http_error_from_backend(exc: BackendApiError) -> HTTPException:
    status_code = exc.status_code

    if status_code == 502:
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.detail,
        )

    return HTTPException(
        status_code=status_code,
        detail=exc.detail,
    )


@app.get(
    "/",
    include_in_schema=False,
    response_model=None,
)
def index(request: Request):
    if _get_access_token(request):
        return RedirectResponse(url="/clients")

    return RedirectResponse(url="/login")


@app.get(
    "/login",
    response_class=HTMLResponse,
    include_in_schema=False,
    response_model=None,
)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Авторизация",
        },
    )


@app.get(
    "/clients",
    response_class=HTMLResponse,
    include_in_schema=False,
    response_model=None,
)
def clients_page(request: Request):
    if not _get_access_token(request):
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "title": "Клиенты",
            "backend_base_url": settings.backend_base_url,
        },
    )


@app.post(
    "/frontend-api/login",
    response_model=None,
)
async def login(payload: LoginRequest):
    client = BackendClient()

    try:
        token_data = await client.login_admin(
            username=payload.username,
            password=payload.password,
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc

    access_token = _extract_access_token(token_data)
    refresh_token = _extract_refresh_token(token_data)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Backend login response does not contain access token",
                "backend_response": token_data,
            },
        )

    response = JSONResponse(
        {
            "ok": True,
        },
    )

    _set_access_cookie(response, access_token)

    if refresh_token:
        _set_refresh_cookie(response, refresh_token)

    return response


@app.post(
    "/frontend-api/logout",
    response_model=None,
)
async def logout(request: Request):
    access_token = _get_access_token(request)

    if access_token:
        client = BackendClient()

        try:
            await client.logout_admin(
                access_token=access_token,
            )
        except BackendApiError:
            # Logout in frontend must still clear local cookies even if backend
            # logout endpoint is unavailable or returns an error.
            pass

    response = JSONResponse(
        {
            "ok": True,
        },
    )

    _delete_auth_cookies(response)

    return response


@app.post(
    "/frontend-api/refresh",
    response_model=None,
)
async def refresh(request: Request):
    refresh_token = _get_refresh_token(request)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    client = BackendClient()

    try:
        token_data = await client.refresh_admin(
            refresh_token=refresh_token,
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc

    access_token = _extract_access_token(token_data)
    new_refresh_token = _extract_refresh_token(token_data)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Backend refresh response does not contain access token",
                "backend_response": token_data,
            },
        )

    response = JSONResponse(
        {
            "ok": True,
        },
    )

    _set_access_cookie(response, access_token)

    if new_refresh_token:
        _set_refresh_cookie(response, new_refresh_token)

    return response


@app.get(
    "/frontend-api/permissions",
    response_model=None,
)
async def get_permissions(
    access_token: str = Depends(_require_access_token),
):
    client = BackendClient()

    try:
        return await client.get_permissions(
            access_token=access_token,
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc


@app.get(
    "/frontend-api/clients",
    response_model=None,
)
async def get_clients(
    access_token: str = Depends(_require_access_token),
):
    client = BackendClient()

    try:
        return await client.get_clients(
            access_token=access_token,
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc


@app.get(
    "/frontend-api/clients/{client_id}",
    response_model=None,
)
async def get_client(
    client_id: int,
    access_token: str = Depends(_require_access_token),
):
    client = BackendClient()

    try:
        return await client.get_client(
            access_token=access_token,
            client_id=client_id,
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc


@app.post(
    "/frontend-api/clients",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
)
async def create_client(
    payload: ClientCreatePayload,
    access_token: str = Depends(_require_access_token),
):
    client = BackendClient()

    try:
        return await client.create_client(
            access_token=access_token,
            payload=payload.model_dump(),
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc


@app.put(
    "/frontend-api/clients/{client_id}/contact",
    response_model=None,
)
async def update_client_contact(
    client_id: int,
    payload: ClientContactPayload,
    access_token: str = Depends(_require_access_token),
):
    client = BackendClient()

    try:
        return await client.update_client_contact(
            access_token=access_token,
            client_id=client_id,
            payload=payload.model_dump(),
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc


@app.patch(
    "/frontend-api/clients/{client_id}/enabled",
    response_model=None,
)
async def set_client_enabled(
    client_id: int,
    payload: ClientEnabledPayload,
    access_token: str = Depends(_require_access_token),
):
    client = BackendClient()

    try:
        if payload.enabled:
            return await client.enable_client(
                access_token=access_token,
                client_id=client_id,
            )

        return await client.disable_client(
            access_token=access_token,
            client_id=client_id,
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc


@app.delete(
    "/frontend-api/clients/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_client(
    client_id: int,
    access_token: str = Depends(_require_access_token),
):
    client = BackendClient()

    try:
        await client.delete_client(
            access_token=access_token,
            client_id=client_id,
        )
    except BackendApiError as exc:
        raise _http_error_from_backend(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/health",
    response_model=None,
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "backend_base_url": settings.backend_base_url,
    }
