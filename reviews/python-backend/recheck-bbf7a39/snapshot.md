# Зафиксированный снимок

## Выбор исходников

Подключённый репозиторий — `tegasae/simple_tickets`. Ветка продолжения задачи — `api-new-client-scheme`.
Первая проверка локальной копии `/workspace/simple_tickets` показала HEAD `d497e75d4937e8edea98783a5af924c247622e06`
и 26 неотслеживаемых файлов прошлого прохода в `reviews/python-backend/recheck-d497e75/`.
Изменённых отслеживаемых файлов кода не было. Контрольная сумма пустого `git diff --binary HEAD`
до начала работы — `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Прежние неотслеживаемые материалы проверены по SHA256 перед завершением.

Удалённая ветка уже указывала на `bbf7a392dafe0fede2d5d017af36281b6f4f40a2`. Удаление устаревшего tests_pyramid подтверждено её деревом.
Для актуального запроса использована отдельная связанная рабочая копия этого коммита —
`/workspace/work/simple_tickets-bbf7a39`. Её `git status --porcelain=v1 --untracked-files=all`
перед созданием результатов был пустым. HEAD этой копии — `bbf7a392dafe0fede2d5d017af36281b6f4f40a2`.
Незакоммиченных изменений исходников, которые нужно добавлять к пакету, не было.
Контрольная сумма её пустого diff также `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Одинаковый пакет

Эксперты и арбитр получили `/workspace/work/input-bbf7a39`.
166 файлов Python и дополнительные материалы пакета взяты из указанного HEAD.
Всего в пакете 198 файлов. Источники первого раунда включают readme.md, правила, DDL и документы,
а также OWNER-NOTES.md с требованиями владельца и ссылками на их происхождение.
Старые отчёты экспертов, фронтенд, архивы, .env и существующие базы не включены.

Манифест `input-manifest.json` содержит SHA256 каждого файла.
SHA256 сериализованного манифеста — `8ad0911db59c2828a58f8e215d2ef0da291117ad20be52647d424573472e267d`.
Пакет оставался неизменным во время всех раундов. Временные испытательные копии отделены от него.

## Изменения относительно прошлого анализируемого SHA

Команда — `git diff --name-status d497e75d4937e8edea98783a5af924c247622e06 bbf7a392dafe0fede2d5d017af36281b6f4f40a2 -- <backend paths>`.

```text
M	db/schema.sql
M	requirements.txt
M	src/adapters/repositories/gateways/ticket_gateway.py
M	src/adapters/repositories/mappers/ticket_mapper.py
M	src/application/services/ticket_service.py
M	src/domain/services/client_service.py
M	src/domain/services/user_service.py
M	src/domain/statuses/rules/ticket_status_transition.py
M	src/domain/ticket.py
M	src/domain/ticket_user.py
M	src/web/auth/services/services.py
M	src/web/auth/storage.py
A	src/web/auth/storage_sqlite.py
M	src/web/auth/tokens.py
M	src/web/config.py
M	src/web/dependencies/auth.py
M	src/web/main.py
A	src/web/models/ticket_input.py
M	src/web/models/tickets.py
M	src/web/models/tikcets_user.py
M	src/web/routers/admin/departments.py
M	src/web/routers/admin/tickets.py
M	src/web/routers/auth.py
D	tests_pyramid/__init__.py
D	tests_pyramid/conftest.py
D	tests_pyramid/contract/test_gateway_sql_contracts.py
D	tests_pyramid/full/test_full_ticket_lifecycle_sqlite.py
D	tests_pyramid/integration/application/test_active_services_sqlite.py
D	tests_pyramid/integration/repositories/test_sqlite_repositories.py
D	tests_pyramid/integration/web/test_api_smoke.py
D	tests_pyramid/pytest.ini
D	tests_pyramid/support/__init__.py
D	tests_pyramid/support/fakes.py
D	tests_pyramid/support/service_imports.py
D	tests_pyramid/unit/adapters/test_base_repository.py
D	tests_pyramid/unit/adapters/test_mappers.py
D	tests_pyramid/unit/application/test_admin_application_service.py
D	tests_pyramid/unit/application/test_client_application_service.py
D	tests_pyramid/unit/application/test_department_application_service.py
D	tests_pyramid/unit/application/test_factory.py
D	tests_pyramid/unit/application/test_helpers_and_assemblers.py
D	tests_pyramid/unit/application/test_role_application_service.py
D	tests_pyramid/unit/application/test_ticket_application_service.py
D	tests_pyramid/unit/application/test_ticket_user_application_service.py
D	tests_pyramid/unit/application/test_user_application_service.py
D	tests_pyramid/unit/domain/test_account.py
D	tests_pyramid/unit/domain/test_admin.py
D	tests_pyramid/unit/domain/test_client.py
D	tests_pyramid/unit/domain/test_department.py
D	tests_pyramid/unit/domain/test_domain_services.py
D	tests_pyramid/unit/domain/test_employee_base.py
D	tests_pyramid/unit/domain/test_policies.py
D	tests_pyramid/unit/domain/test_rbac.py
D	tests_pyramid/unit/domain/test_ticket.py
D	tests_pyramid/unit/domain/test_ticket_creator_semantics.py
D	tests_pyramid/unit/domain/test_ticket_policy_links.py
D	tests_pyramid/unit/domain/test_ticket_status.py
D	tests_pyramid/unit/domain/test_ticket_status_record.py
D	tests_pyramid/unit/domain/test_ticket_status_record_actor.py
D	tests_pyramid/unit/domain/test_ticket_user.py
D	tests_pyramid/unit/domain/test_user.py
D	tests_pyramid/unit/domain/test_value_objects.py
D	tests_pyramid/unit/web/test_auth.py
D	tests_pyramid/unit/web/test_dependencies_and_errors.py
D	tests_pyramid/unit/web/test_middleware.py
D	tests_pyramid/unit/web/test_request_mappers.py
D	tests_pyramid/unit/web/test_router_contracts.py
D	tests_pyramid/unit/web/test_router_dispatch_contracts.py
```
