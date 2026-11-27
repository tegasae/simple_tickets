# Финальная проверка Git и состава материалов

Подключённый репозиторий: `/workspace/simple_tickets`, ветка `api-new-client-scheme`.
Его HEAD сохранён: `d497e75d4937e8edea98783a5af924c247622e06`.
Анализируемая связанная копия: `/workspace/work/simple_tickets-5288dea`, HEAD `5288dea85d8f7e7e4c84d4801781d297e0e14475`.
Причина отдельной копии и неизменный снимок описаны в [input-state.md](input-state.md).

## Сохранность исходного состояния

- Все 70 заранее существовавших файлов из начального status сохранены с исходными SHA256 и теми же статусами Git. Их перечень — в initial-git-state.json.
- `git diff --binary HEAD -- . ':(exclude)reviews/python-backend/recheck-5288dea/'` имеет прежний SHA256 `fd54d271467c6ce607e76ba1b156bb3cc8cf8be23c591ae1b677c635a0abdc60`.
- После исключения нового каталога status подключённой копии совпадает с начальным. У связанной копии нет изменений вне этого каталога.
- 204 Git-файла общего входа сверены с blobs полного SHA5288dea; все205 файлов слепого пакета, два дополнения и четыре первичных заключения совпадают с зафиксированными хешами.
- Все четыре опубликованных patch повторно прошли отдельный и последовательный apply-check с whitespace=error-all, реально применены в новой временной копии. Полученный source побайтно совпал с копией выполненного прогона65pass/39fail.
- Временные копии и диагностические логи не включены в Git. В каталоге нет DB, .env, бинарных архивов, raw HTTP/JUnit captures или действительных токенов.

## Доступность изменений задачи

Материалы из связанной копии побайтно перенесены в новый каталог подключённого репозитория. Только для этого каталога выполнен `git add -N --sparse`: файлы видны в обычном `git diff`, содержимое не закоммичено. Прежние изменения не индексировались заново, ветка не переключалась. PR, merge и push не выполнялись.

Финальные команды проверки: `git rev-parse HEAD`, `git branch --show-current`, `git status --short --untracked-files=all`, `git diff --name-only`, сравнение путей и SHA256 с начальным JSON. Status содержит 70 прежних файлов плюс 48 новых файлов этого прохода. Добавленных или изменённых этим проходом путей вне `reviews/python-backend/recheck-5288dea/` нет.

Манифест [artifact-manifest.json](artifact-manifest.json) фиксирует все файлы ниже, кроме самого себя. Машинные результаты контроля исходников/патчей — [results/artifact-checks.json](results/artifact-checks.json).

## Новые файлы этого прохода

Все пути ниже относительно `reviews/python-backend/recheck-5288dea/`:

- `README.md`
- `artifact-manifest.json`
- `decisions-full.md`
- `experts/arbiter-final.md`
- `experts/arbiter-initial.md`
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
- `git-verification.md`
- `initial-git-state.json`
- `input-manifest.json`
- `input-notes.md`
- `input-state.md`
- `owner-confirmation.md`
- `patches/01-created-actor.patch`
- `patches/02-admin-comment-json.patch`
- `patches/03-session-lifetime.patch`
- `patches/04-executor-version-guard.patch`
- `patches/05-refresh-revocation-plan.md`
- `patches/06-idempotency-plan.md`
- `patches/README.md`
- `previous-findings.md`
- `requirements-manifest.json`
- `results/artifact-checks.json`
- `results/entrypoint-results.json`
- `results/existing-results.json`
- `results/new-baseline.json`
- `results/patched-results.json`
- `results/qa-creation-admin-before.json`
- `results/smoke-results.json`
- `tests/README.md`
- `tests/check_backend.py`
- `tests/conftest.py`
- `tests/environment.json`
- `tests/requirements-lock.txt`
- `tests/test_admin_refresh_revocation.py`
- `tests/test_creation_idempotency.py`
- `tests/test_current_contracts.py`
- `tests/test_executor_guard.py`
- `tests/test_history_and_json.py`
- `tests/test_session_lifetime.py`
