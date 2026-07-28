from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .config import settings


@dataclass(frozen=True, kw_only=True)
class BackendApiError(Exception):
    status_code: int
    detail: Any

    def __str__(self) -> str:
        return f"Backend API error {self.status_code}: {self.detail}"


class BackendClient:
    """Thin async client for the Simple Tickets backend API."""

    def __init__(self) -> None:
        self._base_url = settings.backend_base_url
        self._timeout = settings.request_timeout_seconds

    async def login_admin(self, *, username: str, password: str) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/auth/admin/login",
            form={
                "username": username,
                "password": password,
            },
        )

    async def refresh_admin(self, *, refresh_token: str) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/auth/admin/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )

    async def logout_admin(self, *, access_token: str | None = None) -> dict[str, Any] | None:
        return await self._request(
            method="POST",
            path="/auth/admin/logout",
            access_token=access_token,
        )

    async def get_permissions(self, *, access_token: str) -> dict[str, Any]:
        return await self._request(
            method="GET",
            path="/admin/admins/permissions",
            access_token=access_token,
        )

    async def get_clients(self, *, access_token: str) -> list[dict[str, Any]]:
        result = await self._request(
            method="GET",
            path="/admin/clients/",
            access_token=access_token,
        )

        if not isinstance(result, list):
            raise BackendApiError(
                status_code=502,
                detail="Backend returned non-list response for clients",
            )

        return result

    async def get_client(self, *, access_token: str, client_id: int) -> dict[str, Any]:
        return await self._request(
            method="GET",
            path=f"/admin/clients/{client_id}",
            access_token=access_token,
        )

    async def create_client(
        self,
        *,
        access_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/admin/clients/",
            access_token=access_token,
            json=payload,
        )

    async def update_client_contact(
        self,
        *,
        access_token: str,
        client_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            method="PUT",
            path=f"/admin/clients/{client_id}/contact",
            access_token=access_token,
            json=payload,
        )

    async def enable_client(
        self,
        *,
        access_token: str,
        client_id: int,
    ) -> dict[str, Any]:
        return await self._request(
            method="PATCH",
            path=f"/admin/clients/{client_id}/enable",
            access_token=access_token,
        )

    async def disable_client(
        self,
        *,
        access_token: str,
        client_id: int,
    ) -> dict[str, Any]:
        return await self._request(
            method="PATCH",
            path=f"/admin/clients/{client_id}/disable",
            access_token=access_token,
        )

    async def delete_client(
        self,
        *,
        access_token: str,
        client_id: int,
    ) -> None:
        await self._request(
            method="DELETE",
            path=f"/admin/clients/{client_id}",
            access_token=access_token,
        )

    async def _request(
        self,
        *,
        method: str,
        path: str,
        access_token: str | None = None,
        json: dict[str, Any] | None = None,
        form: dict[str, Any] | None = None,
    ) -> Any:
        headers: dict[str, str] = {}

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        url = f"{self._base_url}{path}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    data=form,
                )
            except httpx.RequestError as exc:
                raise BackendApiError(
                    status_code=502,
                    detail=f"Backend is not available: {exc}",
                ) from exc

        if response.status_code == 204:
            if 200 <= response.status_code < 300:
                return None

        if not 200 <= response.status_code < 300:
            raise BackendApiError(
                status_code=response.status_code,
                detail=_response_detail(response),
            )

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise BackendApiError(
                status_code=502,
                detail="Backend returned invalid JSON",
            ) from exc


def _response_detail(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text
