# Simple Tickets — backend test pyramid

Этот каталог содержит новый независимый test-suite для **активного backend** проекта.
Frontend/React не тестируются.

## Что считается активным production surface

В обязательную пирамиду входят:

- `src/domain`: Account, Admin, User, Client, Department, Ticket, TicketUser,
  status records/states, comments, value objects, RBAC, policies, domain services;
- активные application services из `ApplicationServiceFactory`:
  Admin, User, Client, Department, Role, Ticket, TicketUser;
- assemblers/helpers/factory;
- SQLite mappers/repositories/UoW/gateways;
- web auth/tokens/storage/dependencies/exception registry/middleware;
- admin/user/auth routers и их request→DTO/dispatch contracts;
- несколько API smoke и application→SQLite сквозных сценариев.

Отложенные split-services `src/application/services/tickets/*` и
`ticket_search_service.py` не являются обязательным production surface.

## Пирамида

```text
                         API / E2E smoke
                      ───────────────────
                       web + app wiring
                    ───────────────────────
                  SQLite / repository integration
               ───────────────────────────────
                  application service unit
             ───────────────────────────────────
                    domain unit tests
        ─────────────────────────────────────────────
```

### 1. Domain unit — самая широкая база

`tests_pyramid/unit/domain/`

Отдельно представлены:

- `test_admin.py`
- `test_user.py`
- `test_employee_base.py`
- `test_account.py`
- `test_client.py`
- `test_department.py`
- `test_ticket.py`
- `test_ticket_user.py`
- `test_ticket_status.py`
- `test_ticket_status_record.py`
- `test_rbac.py`
- `test_policies.py`
- `test_domain_services.py`
- `test_value_objects.py`

Критичные regression-контракты Ticket creator semantics и Ticket↔TicketUser
вынесены в отдельные файлы.

### 2. Application unit

`tests_pyramid/unit/application/`

Проверяются все сервисы, которые выдаёт текущий `ApplicationServiceFactory`:
Admin/User/Client/Department/Role/Ticket/TicketUser, а также helpers,
assemblers и factory contract.

### 3. Adapter unit + contracts

- `tests_pyramid/unit/adapters/` — mapper/base repository tests;
- `tests_pyramid/contract/` — автоматическая проверка SQL gateway against
  текущей схемы `db/admins.db`.

### 4. Integration

`tests_pyramid/integration/`

- реальные SQLite repositories и optimistic locking;
- SQLiteUnitOfWork commit/rollback/nesting;
- Account repository;
- application→SQLite сценарии для Ticket/TicketUser;
- linked aggregate round trips.

Тестовая БД всегда создаётся как временная копия `db/admins.db` и очищается.
Исходная БД не изменяется.

### 5. Web / API

`tests_pyramid/unit/web/` и `tests_pyramid/integration/web/`

Проверяются:

- JWT/token/auth realm contracts;
- dependencies;
- exception registry;
- middleware helpers;
- request→DTO mapping;
- полный method/path/status route contract;
- endpoint→application-service dispatch contract;
- реальные FastAPI `TestClient` smoke requests для admin/user API;
- HTTP mapping domain errors.

## Запуск

Распаковать каталог в корень проекта, рядом с `src/`, `db/`, `utils/`.

Полный suite:

```bash
pytest -c tests_pyramid/pytest.ini tests_pyramid
```

Только domain:

```bash
pytest -c tests_pyramid/pytest.ini tests_pyramid/unit/domain
```

Только application:

```bash
pytest -c tests_pyramid/pytest.ini tests_pyramid/unit/application
```

Только SQLite/integration:

```bash
pytest -c tests_pyramid/pytest.ini tests_pyramid/integration
```

Только web:

```bash
pytest -c tests_pyramid/pytest.ini tests_pyramid/unit/web tests_pyramid/integration/web
```

SQL/schema contracts:

```bash
pytest -c tests_pyramid/pytest.ini tests_pyramid/contract
```

Coverage активного backend:

```bash
pytest -c tests_pyramid/pytest.ini tests_pyramid \
  --cov=src --cov-config=.coveragerc --cov-report=term-missing
```

## Философия набора

- domain/business contract тестируется напрямую, без DB и FastAPI;
- application tests проверяют orchestration/RBAC/cross-aggregate порядок;
- repository tests проверяют реальную схему, rehydrate, optimistic locking;
- web tests не тестируют FastAPI «сам по себе», а наше wiring;
- существенные regression bugs остаются **строгими failing tests**, а не `xfail`;
- старые development DB records не считаются корректностью domain-кода.
