# OpenAPI compatibility notes

Frontend was reconciled with the provided Simple Tickets OpenAPI 3.1 schema.

## Fixed in this frontend

- Admin logout sends `{ "refresh_token": ... }` and skips server logout when no refresh token exists.
- Ticket workflow actions now follow the current 14-state transition matrix.
- `CANCELLED` is not offered from `CREATED` / `CREATED_FROM_TICKET_USER`.
- `ACCEPTED` is offered from `DEFERRED`, `SCHEDULED`, `ASSIGNED`, `READY_TO_WORK`.
- `READY_FOR_REVIEW` uses only the dedicated `return-to-*` operations.
- Legacy `/execute` is no longer exposed in the UI; `/confirm-execution` is used.
- Required executor/date/comment fields disable actions until valid.
- Planned/actual end times cannot precede start times in the UI.
- Ticket/User/Admin lookup data is loaded independently; unavailable lookups fall back to raw IDs.
- Admin update no longer sends `department_id`; department changes use the dedicated endpoint.
- Navigation is filtered by current Admin permissions.
- A non-401 error from the permissions endpoint no longer destroys the local login session.

## Backend changes still recommended

### 1. Current Admin permissions endpoint

`GET /admin/admins/permissions` is used to determine the UI capabilities of the authenticated Admin.
It should require a valid authenticated Admin, but should not require `AdminPermission.ADMIN_OPERATION`.
Otherwise an Admin who has only `ticket.view` / `ticket.operation` can log in but cannot discover their own permissions.

### 2. AdminUpdateRequest

`department_id` should preferably be removed from `AdminUpdateRequest`, because department changes already have dedicated endpoints:

- `PATCH /admin/admins/{employee_id}/department`
- `DELETE /admin/admins/{employee_id}/department`

The frontend already follows that split.

### 3. Auth response schema

Login/refresh 200 responses currently have an empty OpenAPI schema. A response model such as
`TokenResponse(access_token, refresh_token, token_type)` would make the contract machine-verifiable.
