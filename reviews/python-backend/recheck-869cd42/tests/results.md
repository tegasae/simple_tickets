# Протокол приёмки

Основной протокол относится к первоначальной серии. Результаты комплекта с переработанными репозиториями приведены в [отдельном разделе](#проверка-редакции-репозиториев).

Фактический runtime Python 3.12.14, SQLite 3.53.1. Результаты ниже разобраны из JUnit временных запусков. Поля и значения секретов из выводов исключены. Параметризованные случаи перечислены по отдельности.

| Прогон | Версия | Успешно | Падения | Ошибки | Пропуски |
|---|---|---:|---:|---:|---:|
| Текущий код | `869cd424b1b9f13babd720884a3cbb7e0f6a10bb` | 92 | 66 | 0 | 39 |
| Серия 05–10 | `869cd424b1b9f13babd720884a3cbb7e0f6a10bb + 05–10` | 195 | 0 | 0 | 2 |
| Только 05, без функций 06–10 | `869cd424b1b9f13babd720884a3cbb7e0f6a10bb + 05` | 67 | 0 | 0 | 2 |
| Контроль F-01–F-05 на 5288dea | `5288dea85d8f7e7e4c84d4801781d297e0e14475 (rotation configured 5/7)` | 1 | 10 | 0 | 0 |
| Контроль D01–D04 на 5288dea | `5288dea85d8f7e7e4c84d4801781d297e0e14475` | 11 | 7 | 0 | 0 |
| Исторические 70, до | `869cd424b1b9f13babd720884a3cbb7e0f6a10bb` | 70 | 0 | 0 | 0 |
| Исторические 70, после | `869cd424b1b9f13babd720884a3cbb7e0f6a10bb + 05–10` | 70 | 0 | 0 | 0 |

Две legacy-проверки сроков проходят в текущих SQLite и memory. При едином хранилище эти записи выводятся из обращения, поэтому в итоговой серии их заменяют две проверки CLI и отказа старому refresh. Пропуски исходника состоят из 11 сценариев отзыва и общей транзакции, 4 тестов миграции и 24 тестов нового реестра результатов, включая границу COMMIT, CHECK и повторное чтение после UNIQUE. [Команды запуска](README.md)

Применённые файлы и их SHA-256

- `05-shared-refresh-and-versions.patch` — `b8aa74a4b452125e93e7023fb86a575c4797b9f44f94fa6ffe441d9ffbd948f7`
- `06-creation-idempotency.patch` — `b4f23a7fe12962da1153271a2e776e05b1b1a53ecc08511c708e2a95d4d56e15`
- `07-department-initial-state.patch` — `209f627480d993f18e56e1c377841770e7b7e361ece7ac92342977c3b9aa4b5f`
- `08-preserve-admin-department.patch` — `282bd85c1d8dcbe7e1cb0379c125d5a2489335b0b518519dd50380a97ff15a72`
- `09-normalize-login-check.patch` — `13385bbdbda258abf543599deab1cd5fc3be45626856bb126367ca13d340897e`
- `10-preserve-work-mode-null.patch` — `d4537eb4d36374d95c4e6b64d65e9410c79a993c167ba0692f07fc0d6b66cc2d`

## F-01

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_admin_response_comment_contract_includes_empty_and_status_text[user]`](test_comment_api.py#L30) | Admin GET/create/comment returns plain strings and preserves author after reload. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_admin_response_comment_contract_includes_empty_and_status_text[admin_for_user]`](test_comment_api.py#L30) | Admin GET/create/comment returns plain strings and preserves author after reload. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_admin_response_comment_contract_includes_empty_and_status_text[standalone]`](test_comment_api.py#L30) | Admin GET/create/comment returns plain strings and preserves author after reload. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_comment_preserves_history[missing-admin]`](test_comment_api.py#L57) | Reject omitted, null or blank comments; neither history is changed. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_comment_preserves_history[missing-user]`](test_comment_api.py#L57) | Reject omitted, null or blank comments; neither history is changed. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_comment_preserves_history[null-admin]`](test_comment_api.py#L57) | Reject omitted, null or blank comments; neither history is changed. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_comment_preserves_history[null-user]`](test_comment_api.py#L57) | Reject omitted, null or blank comments; neither history is changed. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_comment_preserves_history[blank-admin]`](test_comment_api.py#L57) | Reject omitted, null or blank comments; neither history is changed. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_comment_preserves_history[blank-user]`](test_comment_api.py#L57) | Reject omitted, null or blank comments; neither history is changed. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## F-02

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_central_default_lifetimes`](test_lifetime.py#L37) | Settings default to 5 minutes and 7 days. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_issue_uses_five_minutes_and_seven_days[sqlite]`](test_lifetime.py#L48) | 200 with 300 seconds and persisted 7 days; wrong password gives 401. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_issue_uses_five_minutes_and_seven_days[memory]`](test_lifetime.py#L48) | 200 with 300 seconds and persisted 7 days; wrong password gives 401. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## F-03

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_rotation_has_one_deadline_and_single_use[sqlite]`](test_lifetime.py#L63) | Rotations keep t0, cap access, consume the old credential and reject at expiry. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_rotation_has_one_deadline_and_single_use[memory]`](test_lifetime.py#L63) | Rotations keep t0, cap access, consume the old credential and reject at expiry. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_rotation_encoding_error_preserves_old_session[sqlite]`](test_lifetime.py#L85) | Encoding failure gives 500 and preserves the valid old credential. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_rotation_encoding_error_preserves_old_session[memory]`](test_lifetime.py#L85) | Encoding failure gives 500 and preserves the valid old credential. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_two_refreshes_consume_credential_only_once`](test_lifetime.py#L99) | Concurrent rotations yield one usable successor and at most one success. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_legacy_naive_session_timestamps_are_interpreted_in_utc[sqlite]`](test_lifetime.py#L121) | The current legacy storage rotates UTC-normalized dates without extending TTL. | Прошёл, ожидаемый результат получен | Пропуск. Старое хранилище закрыто, см. F-07 |
| [`test_legacy_naive_session_timestamps_are_interpreted_in_utc[memory]`](test_lifetime.py#L121) | The current legacy storage rotates UTC-normalized dates without extending TTL. | Прошёл, ожидаемый результат получен | Пропуск. Старое хранилище закрыто, см. F-07 |

## F-04

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_new_assignment_advances_the_executor_guard_version[self]`](test_executor_guard.py#L9) | Valid assignment stores executor, synchronized state and one version increment. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_new_assignment_advances_the_executor_guard_version[other]`](test_executor_guard.py#L9) | Valid assignment stores executor, synchronized state and one version increment. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_guard_failure_rolls_back_assignment_and_both_histories[self]`](test_executor_guard.py#L39) | 409 from a stale executor leaves both histories and versions unchanged. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_wrong_department_preserves_assigned_pair`](test_executor_guard.py#L90) | Same department gives 200; another department gives 400 with both histories intact. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_partial_ticket_save_rolls_back_pair_and_employee_version[assign]`](test_executor_guard.py#L155) | Failure after actual writes restores both tickets and the touched executor. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_accept_has_body_and_separate_permission`](test_http_roles.py#L33) | Пустой JSON для accept обязателен, право на обычную операцию даёт только смену отдела. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_user_ticket_create_does_not_accept_department_field`](test_http_roles.py#L77) | User POST с внутренним department_id получает 422, пара не создаётся. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## F-05

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_new_assignment_advances_the_executor_guard_version[remote_self]`](test_executor_guard.py#L9) | Valid assignment stores executor, synchronized state and one version increment. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_guard_failure_rolls_back_assignment_and_both_histories[remote_self]`](test_executor_guard.py#L39) | 409 from a stale executor leaves both histories and versions unchanged. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_remote_rejection_leaves_pair_and_guard_unchanged[no-department]`](test_executor_guard.py#L114) | Invalid remote start gives 400, preserving both statuses and executor version. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_remote_rejection_leaves_pair_and_guard_unchanged[not-recommended]`](test_executor_guard.py#L114) | Invalid remote start gives 400, preserving both statuses and executor version. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_remote_rejection_leaves_pair_and_guard_unchanged[other-executor]`](test_executor_guard.py#L114) | Invalid remote start gives 400, preserving both statuses and executor version. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_remote_rejection_leaves_pair_and_guard_unchanged[repeat]`](test_executor_guard.py#L114) | Invalid remote start gives 400, preserving both statuses and executor version. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_remote_start_after_assignment_keeps_one_executor`](test_executor_guard.py#L137) | ASSIGNED → AT_WORK records remote work without a second assignment. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_partial_ticket_save_rolls_back_pair_and_employee_version[remote-self]`](test_executor_guard.py#L155) | Failure after actual writes restores both tickets and the touched executor. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_remote_work_requires_more_rights_for_preparation`](test_http_roles.py#L45) | Один remote scope даёт старт подготовленной заявки, подготовка требует отдельных прав. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## F-06

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_client_disable_and_session_publication_use_one_ordinary_commit[disable-login]`](test_client_session_order.py#L22) | Один из двух COMMIT, другой HTTP 503, после отключения пара и сессии закрыты. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_client_disable_and_session_publication_use_one_ordinary_commit[disable-refresh]`](test_client_session_order.py#L22) | Один из двух COMMIT, другой HTTP 503, после отключения пара и сессии закрыты. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_client_disable_and_session_publication_use_one_ordinary_commit[session-login]`](test_client_session_order.py#L22) | Один из двух COMMIT, другой HTTP 503, после отключения пара и сессии закрыты. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_client_disable_and_session_publication_use_one_ordinary_commit[session-refresh]`](test_client_session_order.py#L22) | Один из двух COMMIT, другой HTTP 503, после отключения пара и сессии закрыты. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_attach_account_to_existing_employee_retires_previous_sessions[admin]`](test_refresh_attach_replacement.py#L14) | POST account даёт 200, две старые сессии удалены, новый и посторонний вход действуют. | 200, обе прежние записи refresh сохранились | Прошёл, ожидаемый результат получен |
| [`test_attach_account_to_existing_employee_retires_previous_sessions[user]`](test_refresh_attach_replacement.py#L14) | POST account даёт 200, две старые сессии удалены, новый и посторонний вход действуют. | 200, обе прежние записи refresh сохранились | Прошёл, ожидаемый результат получен |
| [`test_attach_cas_and_revocation_share_commit[admin]`](test_refresh_attach_replacement.py#L46) | 500 при ошибке отзыва откатывает Account, версии и сессии, следующий POST даёт 200. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_attach_cas_and_revocation_share_commit[user]`](test_refresh_attach_replacement.py#L46) | 500 при ошибке отзыва откатывает Account, версии и сессии, следующий POST даёт 200. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[password-admin]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[password-user]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[employee-enable-admin]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[employee-enable-user]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[account-enable-admin]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[account-enable-user]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[replacement-admin]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[replacement-user]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | Мутации 200, обе прежние сессии выдали новые пары с 200 | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[delete-admin]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | DELETE 204, refresh 401. Отдельное хранилище сохранило запись | Прошёл, ожидаемый результат получен |
| [`test_mutation_permanently_revokes_all_refresh[delete-user]`](test_shared_sessions.py#L80) | Successful mutation permanently rejects every old refresh with 401. | DELETE 204, refresh 401. Отдельное хранилище сохранило запись | Прошёл, ожидаемый результат получен |
| [`test_client_cascade_revokes_sessions_and_preserves_ticket_history`](test_shared_sessions.py#L123) | Disable Client closes review pair and revokes that Client's refresh sessions. | Каскад и enable успешны, оба старых refresh вернули 200 | Прошёл, ожидаемый результат получен |
| [`test_logout_realm_and_single_session_scope`](test_shared_sessions.py#L144) | Logout only removes the selected session; wrong realm 401 leaves it usable. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_username_logout_revokes_own_sessions`](test_shared_sessions.py#L158) | Bearer plus current username revokes only that subject, across app instances. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_fresh_app_uses_the_same_durable_session`](test_shared_sessions.py#L170) | A separate create_app() reads the committed refresh and rotates it once. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_revoke_write_failure_rolls_back_everything[password]`](test_shared_sessions.py#L182) | Injected failure after DELETE leaves password, sessions and pair unchanged. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_revoke_write_failure_rolls_back_everything[client-cascade]`](test_shared_sessions.py#L182) | Injected failure after DELETE leaves password, sessions and pair unchanged. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_rotation_insert_failure_rolls_back_guard_and_credentials`](test_shared_sessions.py#L223) | A failed successor INSERT leaves old hash and employee version intact. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_password_change_orders_against_session_publication[login]`](test_shared_sessions.py#L248) | A credential request paused before its guard cannot publish after revocation. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_password_change_orders_against_session_publication[refresh]`](test_shared_sessions.py#L248) | A credential request paused before its guard cannot publish after revocation. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |

## F-07

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_migration_normalizes_versions_and_preserves_relations`](test_migration.py#L57) | NULL → 0, existing integers unchanged; FK, uniqueness, CAS and sequence hold. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_migration_rolls_back_on_fk_failure`](test_migration.py#L101) | An invalid relation stops the upgrade without a partially normalized schema. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_upgrade_requires_login_and_never_uses_old_refresh[separate-file]`](test_migration.py#L118) | Old token gets 401 after upgrade; a new login creates shared valid storage. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |
| [`test_upgrade_requires_login_and_never_uses_old_refresh[main-file]`](test_migration.py#L118) | Old token gets 401 after upgrade; a new login creates shared valid storage. | Пропуск, нужный компонент появляется в патче 05 | Прошёл, ожидаемый результат получен |

## F-08

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_creation_results_check_requires_paired_status_and_body[fresh]`](test_creation_storage_rules.py#L19) | При свежей установке и миграции CHECK принимает полную запись и исключает частичную. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_creation_results_check_requires_paired_status_and_body[migrated]`](test_creation_storage_rules.py#L19) | При свежей установке и миграции CHECK принимает полную запись и исключает частичную. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_unique_claim_fallback_reads_committed_result_once[True-201]`](test_creation_storage_rules.py#L50) | После реального UNIQUE происходит одно новое чтение. Ответ 201 с исходным ID либо 503. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_unique_claim_fallback_reads_committed_result_once[False-503]`](test_creation_storage_rules.py#L50) | После реального UNIQUE происходит одно новое чтение. Ответ 201 с исходным ID либо 503. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_later_keyed_success_marks_pending_result_for_full_window`](test_idempotency_commit_boundary.py#L16) | Восстановление другим ключом помечает ранее зафиксированный результат на полные 24 часа. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_sqlite_busy_at_commit_rolls_back_business_data_and_key`](test_idempotency_commit_boundary.py#L51) | SQLite отказывает на COMMIT с 503, ключ и Client откатываются. Новая команда даёт один Client. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_domain_normalized_input_replays_saved_result[department-name]`](test_idempotency_normalized_input.py#L14) | 201 на обе формы. Пробелы в имени отдела или логине не создают вторую запись. | 201 для первого входа. Повтор 409 из-за уникальности имени | Прошёл, ожидаемый результат получен |
| [`test_domain_normalized_input_replays_saved_result[admin_with_account-login]`](test_idempotency_normalized_input.py#L14) | 201 на обе формы. Пробелы в имени отдела или логине не создают вторую запись. | 201 для первого входа. Нормализованный повтор логина даёт 500 | Прошёл, ожидаемый результат получен |
| [`test_domain_normalized_input_replays_saved_result[user_with_account-login]`](test_idempotency_normalized_input.py#L14) | 201 на обе формы. Пробелы в имени отдела или логине не создают вторую запись. | 201 для первого входа. Нормализованный повтор логина даёт 500 | Прошёл, ожидаемый результат получен |
| [`test_employee_name_and_contact_values_use_domain_normalization[admin]`](test_idempotency_normalized_input.py#L31) | Внешние пробелы и регистр email сохраняют эквивалентный результат, Employee создаётся один раз. | Оба вызова дали 201, второй создал другой ID | Прошёл, ожидаемый результат получен |
| [`test_employee_name_and_contact_values_use_domain_normalization[user]`](test_idempotency_normalized_input.py#L31) | Внешние пробелы и регистр email сохраняют эквивалентный результат, Employee создаётся один раз. | Оба вызова дали 201, второй создал другой ID | Прошёл, ожидаемый результат получен |
| [`test_client_address_contact_and_description_use_domain_normalization`](test_idempotency_normalized_input.py#L58) | Адрес, email, телефон и описание нормализуются как в домене. Повтор возвращает исходный Client. | Оба вызова дали 201, второй создал другой ID | Прошёл, ожидаемый результат получен |
| [`test_invalid_whitespace_only_value_does_not_match_omitted_value[client-optional_fields0]`](test_idempotency_normalized_input.py#L90) | Незаполненное поле отличается от пробельного. Обычный ввод даёт 400, повтор ключа 409. | 400 вместо 409, механизм ключей отсутствует | Прошёл, ожидаемый результат получен |
| [`test_invalid_whitespace_only_value_does_not_match_omitted_value[admin-optional_fields1]`](test_idempotency_normalized_input.py#L90) | Незаполненное поле отличается от пробельного. Обычный ввод даёт 400, повтор ключа 409. | 400 вместо 409, механизм ключей отсутствует | Прошёл, ожидаемый результат получен |
| [`test_invalid_whitespace_only_value_does_not_match_omitted_value[user-optional_fields2]`](test_idempotency_normalized_input.py#L90) | Незаполненное поле отличается от пробельного. Обычный ввод даёт 400, повтор ключа 409. | 400 вместо 409, механизм ключей отсутствует | Прошёл, ожидаемый результат получен |
| [`test_whitespace_preserved_by_business_field_remains_significant[admin_role-description]`](test_idempotency_normalized_input.py#L110) | Пробелы в поле без доменной нормализации меняют запрос, ответ 409, записи неизменны. | Повтор с изменённым телом дал 201 | Прошёл, ожидаемый результат получен |
| [`test_whitespace_preserved_by_business_field_remains_significant[user_role-description]`](test_idempotency_normalized_input.py#L110) | Пробелы в поле без доменной нормализации меняют запрос, ответ 409, записи неизменны. | Повтор с изменённым телом дал 201 | Прошёл, ожидаемый результат получен |
| [`test_whitespace_preserved_by_business_field_remains_significant[admin-job_title]`](test_idempotency_normalized_input.py#L110) | Пробелы в поле без доменной нормализации меняют запрос, ответ 409, записи неизменны. | Повтор с изменённым телом дал 201 | Прошёл, ожидаемый результат получен |
| [`test_different_password_is_a_conflict_with_the_same_login`](test_idempotency_normalized_input.py#L124) | Изменённый пароль при том же ключе даёт 409, версия создания Account сохраняется. | 400 по занятому логину вместо 409 по конфликту ключа | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[client]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[department]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[admin]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[user]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[admin_role]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[user_role]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[admin_ticket]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[user_ticket]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[admin_comment]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[user_comment]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[admin_with_account]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_after_result_write_rolls_back_key_and_business_rows[user_with_account]`](test_idempotency_transactions.py#L26) | 500 after saving result rolls back any entity, history and key before retry. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_failure_to_prepare_http_response_rolls_back_pair`](test_idempotency_transactions.py#L47) | Failure constructing the response DTO leaves no pair or key. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_business_rejection_leaves_key_available`](test_idempotency_transactions.py#L65) | A rejected domain command can be corrected with the same unused key. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_lost_response_is_replayed_after_commit`](test_idempotency_transactions.py#L85) | If response delivery breaks, stored status/body survive and avoid a new pair. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_deadline_is_set_after_commit_and_key_can_be_reused_at_expiry`](test_idempotency_transactions.py#L111) | Replay until 24h after commit, then ordinary creation with the same key. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_deadline_maintenance_failure_does_not_lose_success`](test_idempotency_transactions.py#L145) | Committed result survives failed expiry maintenance and is repaired on replay. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_concurrent_replay_returns_one_effect_with_standard_sqlite_busy`](test_idempotency_transactions.py#L164) | 503 during actual contention, then client replay returns durable 201. | Пропуск, нужный компонент появляется в патче 06 | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[client]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[department]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Первый 201, повтор 409 по уникальности имени | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[admin]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[user]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[admin_role]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[user_role]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[admin_ticket]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[user_ticket]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[admin_comment]`](test_idempotent_creations.py#L106) | 200. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[user_comment]`](test_idempotent_creations.py#L106) | 200. Same key and request return original success and one set of database effects. | Успешный повтор добавил второй набор записей | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[admin_with_account]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Первый 201, повтор 400 по занятому логину | Прошёл, ожидаемый результат получен |
| [`test_same_key_replays_original_success_with_one_business_effect[user_with_account]`](test_idempotent_creations.py#L106) | 201. Same key and request return original success and one set of database effects. | Первый 201, повтор 400 по занятому логину | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[client]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[department]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[admin]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[user]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[admin_role]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[user_role]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[admin_ticket]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[user_ticket]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[admin_comment]`](test_idempotent_creations.py#L123) | 200. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[user_comment]`](test_idempotent_creations.py#L123) | 200. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[admin_with_account]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_creation_accepts_omitted_optional_key[user_with_account]`](test_idempotent_creations.py#L123) | 201. No key keeps the original success status and one business effect. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-client]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-department]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-admin]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-user]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-admin_role]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-user_role]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-admin_ticket]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-user_ticket]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-admin_comment]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-user_comment]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-admin_with_account]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[no-key-user_with_account]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-client]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-department]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-admin]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-user]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-admin_role]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-user_role]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-admin_ticket]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-user_ticket]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-admin_comment]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-user_comment]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-admin_with_account]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_separate_commands_keep_ordinary_creation_semantics[different-keys-user_with_account]`](test_idempotent_creations.py#L149) | Separate operations both succeed and both effects persist. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[client]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[department]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[admin]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[user]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[admin_role]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[user_role]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[admin_ticket]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[user_ticket]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[admin_comment]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 200 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[user_comment]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 200 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[admin_with_account]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_same_key_changed_body_is_conflict[user_with_account]`](test_idempotent_creations.py#L165) | Committed key with changed request returns 409 and keeps first effects. | Повтор с другим телом вернул 201 | Прошёл, ожидаемый результат получен |
| [`test_header_optional_in_openapi_on_creation_routes_only`](test_idempotent_creations.py#L184) | All ten routes advertise the optional header; Account attach does not. | OpenAPI 200, заголовок отсутствует | Прошёл, ожидаемый результат получен |
| [`test_invalid_key_rejected_with_no_writes[]`](test_idempotent_creations.py#L204) | Invalid optional header gives 422 before creating the pair. | 201, заголовок проигнорирован | Прошёл, ожидаемый результат получен |
| [`test_invalid_key_rejected_with_no_writes[contains space]`](test_idempotent_creations.py#L204) | Invalid optional header gives 422 before creating the pair. | 201, заголовок проигнорирован | Прошёл, ожидаемый результат получен |
| [`test_invalid_key_rejected_with_no_writes[entry2]`](test_idempotent_creations.py#L204) | Invalid optional header gives 422 before creating the pair. | 201, заголовок проигнорирован | Прошёл, ожидаемый результат получен |
| [`test_default_fields_and_role_sets_replay`](test_idempotent_creations.py#L212) | Omitted defaults and reordering an unordered permission list replay. | При разных формах defaults создалась вторая пара | Прошёл, ожидаемый результат получен |
| [`test_key_scope_separates_commands_and_authenticated_subjects`](test_idempotent_creations.py#L228) | One key has independent results across subjects and commands. | Создания отдельных субъектов успешны, повтор возвращает другой ID | Прошёл, ожидаемый результат получен |
| [`test_replay_checks_current_permissions_and_survives_access_rotation`](test_idempotent_creations.py#L261) | 200 refresh preserves subject scope; revoked permission denies replay. | После refresh 200 вернулась другая заявка при том же ключе | Прошёл, ожидаемый результат получен |
| [`test_comment_key_fingerprints_the_target`](test_idempotent_creations.py#L287) | The same key and comment text on another ticket are a conflict. | Второе добавление комментария вернуло 200 | Прошёл, ожидаемый результат получен |
| [`test_duplicate_key_header_rejected_before_write`](test_idempotent_creations.py#L297) | Ambiguous multiple header values give 422 without an entity write. | 201, заголовок проигнорирован | Прошёл, ожидаемый результат получен |

## F-09

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_create_department_saves_requested_initial_state[default]`](test_department_initial_state.py#L12) | 201. Missing enabled defaults to true, explicit false is persisted. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_create_department_saves_requested_initial_state[true]`](test_department_initial_state.py#L12) | 201. Missing enabled defaults to true, explicit false is persisted. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_create_department_saves_requested_initial_state[false]`](test_department_initial_state.py#L12) | 201. Missing enabled defaults to true, explicit false is persisted. | 201, ответ, GET и запись SQLite содержат true вместо false | Прошёл, ожидаемый результат получен |
| [`test_null_initial_department_state_rejected`](test_department_initial_state.py#L27) | Explicit null gives 422 and does not create a Department. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_department_create_and_followup_get_have_distinct_permissions`](test_http_roles.py#L63) | Создание даёт 201 при DEPARTMENT_OPERATION, GET требует DEPARTMENT_VIEW. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## F-10

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_omitted_department_preserves_department_during_profile_update[idle]`](test_admin_profile_department.py#L22) | 200 and a changed name with the original department and assignment. | 200, но отдел сброшен в 0 | Прошёл, ожидаемый результат получен |
| [`test_omitted_department_preserves_department_during_profile_update[current-executor]`](test_admin_profile_department.py#L22) | 200 and a changed name with the original department and assignment. | 400, изменение имени отклонено из-за текущего назначения | Прошёл, ожидаемый результат получен |
| [`test_explicit_zero_respects_the_assignment_guard[idle]`](test_admin_profile_department.py#L38) | Explicit zero clears only an idle Admin's department. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_explicit_zero_respects_the_assignment_guard[current-executor]`](test_admin_profile_department.py#L38) | Explicit zero clears only an idle Admin's department. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_explicit_other_department_for_idle_admin`](test_admin_profile_department.py#L57) | A positive enabled target preserves the ordinary department update. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_department_value_preserves_profile[null]`](test_admin_profile_department.py#L70) | NULL and unknown targets leave the old profile and department intact. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_invalid_department_value_preserves_profile[unknown-id]`](test_admin_profile_department.py#L70) | NULL and unknown targets leave the old profile and department intact. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## F-11

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_duplicate_normalized_login_is_client_error[canonical-admins]`](test_account_creation_input.py#L10) | 400 for an existing canonical login, with no partial Employee or Account. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_duplicate_normalized_login_is_client_error[canonical-users]`](test_account_creation_input.py#L10) | 400 for an existing canonical login, with no partial Employee or Account. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_duplicate_normalized_login_is_client_error[outer-spaces-admins]`](test_account_creation_input.py#L10) | 400 for an existing canonical login, with no partial Employee or Account. | 500 для логина с внешними пробелами, прежние записи сохранены | Прошёл, ожидаемый результат получен |
| [`test_duplicate_normalized_login_is_client_error[outer-spaces-users]`](test_account_creation_input.py#L10) | 400 for an existing canonical login, with no partial Employee or Account. | 500 для логина с внешними пробелами, прежние записи сохранены | Прошёл, ожидаемый результат получен |

## F-12

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_ticket_work_mode_round_trip[False]`](test_ticket_work_mode_roundtrip.py#L13) | Поле без режима остаётся null, событие работы сохраняет true или false после повторного GET. | Начальный POST содержит null, GET выдаёт false для нерабочих событий | Прошёл, ожидаемый результат получен |
| [`test_ticket_work_mode_round_trip[True]`](test_ticket_work_mode_roundtrip.py#L13) | Поле без режима остаётся null, событие работы сохраняет true или false после повторного GET. | Начальный POST содержит null, GET выдаёт false для нерабочих событий | Прошёл, ожидаемый результат получен |
| [`test_legacy_null_for_required_mode_still_reloads`](test_ticket_work_mode_roundtrip.py#L50) | Старый AT_WORK с NULL читается как false, GET успешен. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## Контроль авторства

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_telephone_registration_keeps_two_meanings_of_actor`](test_comment_api.py#L72) | 201. External CREATED is User; internal registration and comment are Admin. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## Контроль контакта

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_contact_can_change_in_initial_state[admin]`](test_contact_policy.py#L8) | 200 and the positive new contact in both freshly read initial cards. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_contact_can_change_in_initial_state[user]`](test_contact_policy.py#L8) | 200 and the positive new contact in both freshly read initial cards. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_disabling_only_contact_closes_review_pair`](test_contact_policy.py#L28) | Disabling the contact in READY closes both cards with the owner still active. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## Сквозные сценарии

| Имя исполняемого теста | Ожидаемое наблюдение | Текущий код | После серии 05–10 |
|---|---|---|---|
| [`test_pair_completes_and_user_can_read_history[office]`](test_full_workflow.py#L9) | Early confirm rejects without changes; finished work confirms both cards. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |
| [`test_pair_completes_and_user_can_read_history[remote]`](test_full_workflow.py#L9) | Early confirm rejects without changes; finished work confirms both cards. | Прошёл, ожидаемый результат получен | Прошёл, ожидаемый результат получен |

## Исторические регрессии

Набор `recheck-bbf7a39/tests` запускался отдельным процессом на каждой версии. Для каждого случая ожидается прохождение исходного контракта. Все исходные test ID и статусы по версиям приведены в [run-data.json](run-data.json).

На контроле 5288dea тот же набор из 11 проверок F-01–F-05 дал 1 успех (обычное назначение другого Admin) и 10 ожидаемых падений. Для ротации явно выставлены 5/7, чтобы проверить дедлайн при одинаковых настройках. Тест Settings очищает эти overrides. Те же 11 кейсов прошли на 869cd42.

На контроле D01–D04 на 5288dea выполнены те же 18 кейсов, что в F-09–F-12. Из них 7 упали с теми же наблюдаемыми результатами, что на 869cd42. Сценарии каждого дефекта приведены выше. Это подтверждает, что четыре отклонения присутствовали до изменения четырёх Python-файлов.

## Синтаксис, вход и DDL

На 869cd42 проверены 167 Python-файлов, в серии 173 плюс отдельный скрипт миграции. Импорты main, src.web.main, src.oauth2.main прошли. В обоих вариантах /health и /openapi.json дали 200, схема подготовила 115 запросов gateway, integrity_check вернул ok, foreign_key_check не нашёл нарушений. Всего 83 пути OpenAPI. Запросы новых хранилищ выполнены в HTTP-тестах.

Отдельно в синтетической SQLite на серии проверены состояния creation_results: резервирование с двумя пустыми полями и завершённый 201 принимаются, отсутствующий статус с заполненным телом, отсутствующее тело и 400 отвергаются ограничением CHECK. [Данные smoke](smoke-results.json) · [Команды](README.md#синтаксис-схема-и-точки-входа)

Обычная коллекция pytest для Git-снимка не нашла заданный default tests и завершилась кодом 5. Поэтому использовались явные цели. В тестовом окружении Starlette предупреждает об устаревании используемого HTTPX в TestClient. Python 3.14, живые данные и адаптер PostgreSQL в этом прогоне отсутствовали.

## Проверка редакции репозиториев

Снимок `869cd424b1b9f13babd720884a3cbb7e0f6a10bb`. Python 3.12.14 и синтетическая SQLite 3.53.1. Команды выполнялись из этого комплекта в новых временных копиях. [Команды](README.md#запуск-из-отдельного-комплекта)

| Запуск | Прошло | Падения | Пропуски |
|---|---:|---:|---:|
| Переработанные 05 и 06, затем 07–10 | 196 | 0 | 2 |
| Только переработанный 05, выборка из первого прохода | 67 | 0 | 2 |
| Исторический набор, полная серия | 70 | 0 | 0 |
| Новый SQL-сценарий на базовом снимке | 0 | 0 | 1 |

Два пропуска относятся к прежнему хранилищу refresh. Целевой сценарий на базовом снимке пропущен, поскольку реестр результатов добавляет 06. К 195 успешным проверкам первого прохода добавилась проверка ошибки SQL при обслуживании TTL. Она прошла на первоначальном 05+06, а затем в итоговом комплекте. Статусы остальных кейсов совпали по идентификаторам. [Машинные результаты](run-data.json)

`test_busy_maintenance_sql_leaves_durable_creation` имитирует SQLite BUSY в точке Query после бизнес-COMMIT. Проверены сохранённый 201, повторное получение того же тела, восстановление срока и единственная запись Client. Это покрывает перевод исключения через `BaseRepository`. [Тест](test_idempotency_transactions.py)

Синтаксис проверен у 177 Python-файлов, подготовлены 127 SQL-запросов. Импорты приложения, `/health` и OpenAPI прошли. Отдельное сравнение показало полное совпадение OpenAPI для 83 путей первоначальных и новых 05+06. Очищенный дамп восстановлен в памяти с той же схемой, 536 строками и нулём нарушений FK. Дополнительно проверены ABC, оба конструктора `connection=` и параметризация `create_response`. [Smoke](smoke-results.json)

**SHA-256 патчей в этом комплекте**

- `05-shared-refresh-and-versions.patch` — `ca95f6ab2300552e79b4ec659ae7f9cdee8287790d34c7def97625c911b88e6e`
- `06-creation-idempotency.patch` — `aad302a5a961193aa574207dedc9cb5539a66f2caa84110fb8442546d1afb23b`
- `07-department-initial-state.patch` — `209f627480d993f18e56e1c377841770e7b7e361ece7ac92342977c3b9aa4b5f`
- `08-preserve-admin-department.patch` — `282bd85c1d8dcbe7e1cb0379c125d5a2489335b0b518519dd50380a97ff15a72`
- `09-normalize-login-check.patch` — `13385bbdbda258abf543599deab1cd5fc3be45626856bb126367ca13d340897e`
- `10-preserve-work-mode-null.patch` — `d4537eb4d36374d95c4e6b64d65e9410c79a993c167ba0692f07fc0d6b66cc2d`
