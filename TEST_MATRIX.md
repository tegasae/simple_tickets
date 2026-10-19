# Production module → test matrix

| Production area | Main tests |
|---|---|
| `domain/account.py` | `unit/domain/test_account.py`, repository integration |
| `domain/employee.py::Admin` | `unit/domain/test_admin.py`, `unit/application/test_admin_application_service.py` |
| `domain/employee.py::User` | `unit/domain/test_user.py`, `unit/application/test_user_application_service.py` |
| shared employee behavior | `unit/domain/test_employee_base.py` |
| `domain/client.py` | `unit/domain/test_client.py`, client application + repository integration |
| `domain/department.py` | `unit/domain/test_department.py`, department application + repository integration |
| value objects | `unit/domain/test_value_objects.py` |
| RBAC/Role | `unit/domain/test_rbac.py`, `unit/application/test_role_application_service.py`, repository integration |
| policies | `unit/domain/test_policies.py`, `test_ticket_policy_links.py` |
| TicketState/Status | `unit/domain/test_ticket_status.py`, `test_ticket_status_record*.py` |
| Ticket aggregate | `unit/domain/test_ticket.py`, `test_ticket_creator_semantics.py` |
| TicketUser aggregate | `unit/domain/test_ticket_user.py` |
| domain services | `unit/domain/test_domain_services.py` |
| assemblers/helpers | `unit/application/test_helpers_and_assemblers.py` |
| ApplicationServiceFactory | `unit/application/test_factory.py` |
| TicketApplicationService | `unit/application/test_ticket_application_service.py`, `integration/application/test_active_services_sqlite.py` |
| TicketUserApplicationService | `unit/application/test_ticket_user_application_service.py`, `integration/application/test_active_services_sqlite.py` |
| mappers | `unit/adapters/test_mappers.py` |
| BaseRepository | `unit/adapters/test_base_repository.py` |
| SQLite repositories | `integration/repositories/test_sqlite_repositories.py` |
| Gateway SQL/schema | `contract/test_gateway_sql_contracts.py` |
| SQLiteUnitOfWork | repository integration |
| auth/tokens/storage | `unit/web/test_auth.py` |
| auth dependencies | `unit/web/test_dependencies_and_errors.py` |
| exception registry | `unit/web/test_dependencies_and_errors.py` |
| middleware | `unit/web/test_middleware.py` |
| request→DTO | `unit/web/test_request_mappers.py` |
| public routes | `unit/web/test_router_contracts.py` |
| route dispatch | `unit/web/test_router_dispatch_contracts.py` |
| FastAPI boundary | `integration/web/test_api_smoke.py` |
