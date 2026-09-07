# Simple Tickets — full React admin frontend

React/Vite frontend for the current Simple Tickets backend.

## UI entities

- Clients
- Client Users
- Admin employees
- Internal `Ticket` only (`TicketUser` is intentionally not exposed)
- Departments
- Admin/User roles and permissions

## Ticket workflow

The Ticket card supports the current workflow operations exposed by the backend:

- accept / reject
- defer / schedule
- assign executor / ready-to-work
- at-work / pause / resume
- submit-for-review
- retrospective completed-work-for-review
- execute / confirm-execution
- return-to-work / assigned / scheduled / ready-to-work / deferred
- cancel
- change details / department
- add comments
- delete

The UI filters buttons according to the current Ticket status, while the backend remains authoritative for workflow validation.

## Themes

The theme can be changed on the login screen and in the main shell. The choice is persisted in localStorage.

1. **1C 8.3** — dense grey/yellow desktop-style interface.
2. **Classic** — conventional light administrative web UI.
3. **Futuristic** — dark glass/neon interface.
4. **Barbie** — playful pink/glossy interface.

## Run

Backend is expected at `http://127.0.0.1:8000` by default.

```bash
npm install0
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Vite proxies `/api/*` to the backend and strips `/api`.

Alternative backend:

```bash
BACKEND_BASE_URL=http://192.168.1.10:8000 npm run dev
```

## Production build

```bash
npm run build
```

The generated static files are placed in `dist/`.

## Backend assumptions

This frontend follows the routers currently present under `src/web/routers/admin`.

Important current assumptions:

- `GET /admin/tickets/` returns all internal Ticket records. The frontend also has a 404 fallback to `/admin/tickets/all` for compatibility with the previous router.
- `/auth/admin/logout` accepts a `LogoutRequest` body containing `refresh_token`.
- Admin/User role realms remain separate.
- `TicketUser` endpoints are not used anywhere in this frontend.

## Structure

```text
src/
  App.jsx
  api.js
  permissions.js
  storage.js
  components/
    ClientsPage.jsx
    UsersPage.jsx
    AdminsPage.jsx
    TicketsPage.jsx
    DepartmentsPage.jsx
    RolesPage.jsx
    ...
  styles/
    base.css
    themes.css
```

The original Client/User card implementation from the prototype is retained and extended with separate full-list User/Admin screens.

## OpenAPI-aligned revision

This revision was checked against the supplied Simple Tickets OpenAPI schema. Ticket workflow controls now follow the backend transition matrix, required action fields are validated in the UI, and lookup requests degrade gracefully under granular RBAC. See `OPENAPI_AUDIT.md` for the remaining backend-side recommendations.
