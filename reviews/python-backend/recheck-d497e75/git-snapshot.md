# Снимок Git

- Репозиторий `tegasae/simple_tickets`, ветка `api-new-client-scheme`.
- Локальный HEAD и удалённая ветка при фиксации — `d497e75d4937e8edea98783a5af924c247622e06`.
- Родитель последнего коммита — `4b3cb82106c5031d4c5bbbae5a6d18cb8effda59`.
- Первый аудит — `89498c8318d587f197b0ae584d95899d5939c8d8` из `tegasae/simple_tickets_copy`. Код сравнивался по деревьям двух коммитов.
- Перед первым раундом `git status --porcelain=v1 --untracked-files=all` был пуст. Рабочих правок для присоединения к SHA не было.

`git diff --name-status HEAD^ HEAD`:

```text
M	reviews/python-backend/89498c8/README.md
```

Сравнение деревьев целиком, `git diff --shortstat <old> <new>`:

```text
941 files changed, 728240 insertions(+), 331 deletions(-)
```

Список в охвате Python-аудита из `git diff --name-status <old> <new> -- <paths>`:

```text
M	db/schema.sql
A	dockerfiles/backend/Dockerfile
M	main.py
A	reviews/python-backend/89498c8/README.md
M	src/adapters/repositories/gateways/ticket_gateway.py
M	src/adapters/repositories/gateways/ticket_user_gateway.py
M	src/adapters/repositories/mappers/ticket_mapper.py
M	src/adapters/repositories/mappers/ticket_user_mapper.py
M	src/adapters/repositories/ticket_repository.py
M	src/adapters/uow/sqlite_unit_of_work.py
M	src/application/dto/ticket_dto.py
M	src/application/exceptions.py
M	src/application/services/admin_service.py
M	src/application/services/ticket_service.py
M	src/application/services/ticket_user_service.py
M	src/application/services/user_service.py
M	src/domain/services/ticket_service.py
M	src/domain/services/ticket_user_service.py
M	src/domain/statuses/ticket_user_status_transitions.py
M	src/domain/value_objects.py
M	src/web/auth/services/services.py
M	src/web/auth/storage.py
M	src/web/config.py
M	src/web/dependencies/auth.py
M	src/web/execeptions/exception_handlers.py
M	src/web/main.py
M	src/web/models/tickets.py
M	src/web/routers/auth.py
A	tests_pyramid/__init__.py
A	tests_pyramid/conftest.py
A	tests_pyramid/contract/test_gateway_sql_contracts.py
A	tests_pyramid/full/test_full_ticket_lifecycle_sqlite.py
A	tests_pyramid/integration/application/test_active_services_sqlite.py
A	tests_pyramid/integration/repositories/test_sqlite_repositories.py
A	tests_pyramid/integration/web/test_api_smoke.py
A	tests_pyramid/pytest.ini
A	tests_pyramid/support/__init__.py
A	tests_pyramid/support/fakes.py
A	tests_pyramid/support/service_imports.py
A	tests_pyramid/unit/adapters/test_base_repository.py
A	tests_pyramid/unit/adapters/test_mappers.py
A	tests_pyramid/unit/application/test_admin_application_service.py
A	tests_pyramid/unit/application/test_client_application_service.py
A	tests_pyramid/unit/application/test_department_application_service.py
A	tests_pyramid/unit/application/test_factory.py
A	tests_pyramid/unit/application/test_helpers_and_assemblers.py
A	tests_pyramid/unit/application/test_role_application_service.py
A	tests_pyramid/unit/application/test_ticket_application_service.py
A	tests_pyramid/unit/application/test_ticket_user_application_service.py
A	tests_pyramid/unit/application/test_user_application_service.py
A	tests_pyramid/unit/domain/test_account.py
A	tests_pyramid/unit/domain/test_admin.py
A	tests_pyramid/unit/domain/test_client.py
A	tests_pyramid/unit/domain/test_department.py
A	tests_pyramid/unit/domain/test_domain_services.py
A	tests_pyramid/unit/domain/test_employee_base.py
A	tests_pyramid/unit/domain/test_policies.py
A	tests_pyramid/unit/domain/test_rbac.py
A	tests_pyramid/unit/domain/test_ticket.py
A	tests_pyramid/unit/domain/test_ticket_creator_semantics.py
A	tests_pyramid/unit/domain/test_ticket_policy_links.py
A	tests_pyramid/unit/domain/test_ticket_status.py
A	tests_pyramid/unit/domain/test_ticket_status_record.py
A	tests_pyramid/unit/domain/test_ticket_status_record_actor.py
A	tests_pyramid/unit/domain/test_ticket_user.py
A	tests_pyramid/unit/domain/test_user.py
A	tests_pyramid/unit/domain/test_value_objects.py
A	tests_pyramid/unit/web/test_auth.py
A	tests_pyramid/unit/web/test_dependencies_and_errors.py
A	tests_pyramid/unit/web/test_middleware.py
A	tests_pyramid/unit/web/test_request_mappers.py
A	tests_pyramid/unit/web/test_router_contracts.py
A	tests_pyramid/unit/web/test_router_dispatch_contracts.py
```
