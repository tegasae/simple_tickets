# Финальная сверка Git

Корень `/workspace/simple_tickets`. Ветка `api-new-client-scheme`. Локальный HEAD `d497e75d4937e8edea98783a5af924c247622e06`. Проверенный ref ветки `869cd424b1b9f13babd720884a3cbb7e0f6a10bb`. Полный вход и его отпечатки сохранены отдельно. [Вход](input-state.md) · [Состояние 118 путей](input-state.json)

Повторно выполнены команды

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git status --porcelain=v1 -z --untracked-files=all
git diff --binary HEAD | sha256sum
git diff --cached --binary HEAD | sha256sum
```

SHA-256 рабочего diff совпал с входным `897e268eb9e2844e961220afb0c2dfe5fb110a680adde91ffe4f928f9f3e0d7d`. SHA-256 индексированного diff совпал с входным `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Совпали статусы и содержимое всех 118 входных путей. Хеши всех четырёх независимых первичных отчётов и файлов общего набора совпали.

Git показывает 60 новых файлов со статусом `??`. Все находятся в `reviews/python-backend/recheck-869cd42/`. Каждый diff прошёл `git apply --check --whitespace=error-all` в последовательности серии на архиве проверенного коммита. Те же патчи применены в отдельной временной копии для тестов. [Протокол](tests/results.md)

Список новых файлов

- `README.md`
- `artifact-manifest.json`
- `docs/new-functionality.md`
- `docs/owner-scope.md`
- `docs/requirements.md`
- `experts/arbiter-final.md`
- `experts/arbiter-initial.md`
- `experts/implementation-analyst.md`
- `experts/implementation-python.md`
- `experts/implementation-qa.md`
- `experts/initial-report-hashes.json`
- `experts/round-01/analyst.md`
- `experts/round-01/python.md`
- `experts/round-01/qa.md`
- `experts/round-02/analyst.md`
- `experts/round-02/python.md`
- `experts/round-02/qa.md`
- `experts/round-03/analyst.md`
- `experts/round-03/python.md`
- `experts/round-03/qa.md`
- `features.md`
- `git-verification.md`
- `input-manifest.json`
- `input-state.json`
- `input-state.md`
- `patches/05-shared-refresh-and-versions.patch`
- `patches/06-creation-idempotency.patch`
- `patches/07-department-initial-state.patch`
- `patches/08-preserve-admin-department.patch`
- `patches/09-normalize-login-check.patch`
- `patches/10-preserve-work-mode-null.patch`
- `patches/README.md`
- `previous-findings.md`
- `tests/README.md`
- `tests/conftest.py`
- `tests/environment.json`
- `tests/reproduce.sh`
- `tests/requirements-lock.txt`
- `tests/results.md`
- `tests/run-data.json`
- `tests/smoke-results.json`
- `tests/test_account_creation_input.py`
- `tests/test_admin_profile_department.py`
- `tests/test_client_session_order.py`
- `tests/test_comment_api.py`
- `tests/test_contact_policy.py`
- `tests/test_creation_storage_rules.py`
- `tests/test_department_initial_state.py`
- `tests/test_executor_guard.py`
- `tests/test_full_workflow.py`
- `tests/test_http_roles.py`
- `tests/test_idempotency_commit_boundary.py`
- `tests/test_idempotency_normalized_input.py`
- `tests/test_idempotency_transactions.py`
- `tests/test_idempotent_creations.py`
- `tests/test_lifetime.py`
- `tests/test_migration.py`
- `tests/test_refresh_attach_replacement.py`
- `tests/test_shared_sessions.py`
- `tests/test_ticket_work_mode_roundtrip.py`
