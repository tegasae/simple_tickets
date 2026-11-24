# Проверки текущего снимка и предлагаемых исправлений

Источник: `5288dea85d8f7e7e4c84d4801781d297e0e14475`. Полные требования включают дополнение владельца «Все последние договорённости уже обязательны». Настоящие данные, `.env` и рабочие DB не нужны и не копировались.

Среда: Python3.12.14, SQLite3.53.1, отдельный `/tmp/tickets-bbf7a39-venv`. Все22 версии runtime/test пакетов записаны в environment.json. Полный список29 установленных distributions зафиксирован в requirements-lock.txt; он используется как constraints для воспроизведения вместо плавающих `>=` тестовых зависимостей. Все pinned runtime requirements нового снимка совпали с этим venv. Dockerfile использует Python3.14: его runtime/контейнер не проверялся. Сборка копирует исключённый по границам `db/admins.db`; рабочая БД не использовалась как тестовый шаблон.

## Новые проверки

| Модуль | Количество | Что проверяется |
|---|---:|---|
| test_current_contracts.py |15| Фактический инициатор, JSON, User lifecycle/refresh обоих backend, repeat-key/different-body, обычные отдельные операции, finish/execute отключённого клиента |
| test_history_and_json.py |9| Admin/User/standalone, optional actor обратная совместимость, исторические actor не переписываются, обычные/статусные/пустые JSON comments |
| test_session_lifetime.py |11| Defaults5/7, несколько rotations, cap access, expiry, legacy naive metadata, ошибки encode/insert с сохранностью прежнего refresh |
| test_executor_guard.py |5| self/other/remote CAS participation, rollback назначения и обеих историй при конфликте guard. Это не PostgreSQL-concurrency proof |
| test_creation_idempotency.py |60|10 маршрутов и2 родительских варианта с Account; replay обоих backend, optional header и обычные независимые команды |
| test_admin_refresh_revocation.py |4| Password/disable-enable другого Admin, оба backend |
| **Всего** |**104**| Нет xfail, нет скрытого пропуска обязательных функций |

Все HTTP-сценарии world используют настоящие Admin/User login и временную SQLite из текущего db/schema.sql. Подмена auth/RBAC не применяется. Барьеры/ошибки для нужных fault-injection сценариев описаны в тестах. Случайные credentials остаются в памяти теста; не переносить их в отчёт или лог. Фикстура conftest.py задаёт синтетические SECRET_KEY/DATABASE_URL/backend. Обычные тесты не предназначены для запуска с рабочей БД.

## Реально полученные результаты

| Набор | Исходник | После4 малых patches |
|---|---:|---:|
| Все104 новые проверки |49 passed,55 failed,0 errors, exit1|65 passed,39 failed,0 errors, exit1|
| История/JSON,9 |4 passed,5 failed|9 passed|
| Срок сессии,11 |6 passed,5 failed|11 passed|
| Общий guard,5 |1 passed,4 failed|5 passed наSQLite, без утверждения оPG|
| Последние70 регрессий bbf7a39 |70 passed|70 passed|
| Более ранние60 |58 passed,2 failed с отменённым ожиданием review|58 passed,2 deselected|
|7 Python-файлов архивных регрессий|4 failed,6 collection errors|Не повторялись: устаревшие imports/signatures, малые patches их не исправляют|

Оставшиеся39 новых failures после patches: **12 отзыва refresh +27 идемпотентности**. Это честно невыполненные обязательные функции. Общий новый набор не объявляется зелёным. Планы05/06 не являются реализацией, и проверка24ч TTL отсутствующего хранилища результата не считается пройденной. Отдельного «полного исправления всех проблем» в проверенной копии нет.

Два исключённых старых теста: test_client_disable_preserves_in_progress_and_review_pairs и test_user_disable_keeps_review_and_saves_linked_suspension. Они требуют оставить READY_FOR_REVIEW при отключении, в то время как последнее правило закрывает обе карточки SUSPENDED. Текущие положительные сценарии проверяют новое требование. Другие старые тесты не исключались для получения результата128.

Несекретные argv/идентификаторы/исходы каждого теста — в ../results/new-baseline.json, patched-results.json, existing-results.json. Логи с captured bodies/XML остаются только в/tmp и в материалы не включены. qa-creation-admin-before.json — отдельный прогон QA, его64 не нужно складывать с104 как новые независимые тесты.

## Воспроизведение новых тестов

Выполнять только во временной копии, не в рабочем репозитории:

```bash
AUDIT_REPO=/path/to/simple_tickets
AUDIT_REVIEW="$AUDIT_REPO/reviews/python-backend/recheck-5288dea"
AUDIT_SHA=5288dea85d8f7e7e4c84d4801781d297e0e14475
AUDIT_TMP=$(mktemp -d)
git -C "$AUDIT_REPO" archive "$AUDIT_SHA" \
  src utils db/schema.sql main.py models.py config.py \
  requirements.txt requirements-test.txt pytest.ini .coveragerc \
  run_pyramid.sh run_coverage.sh | tar -x -C "$AUDIT_TMP"
cp -R "$AUDIT_REVIEW/tests" "$AUDIT_TMP/recheck_tests"
uv venv --python 3.12 "$AUDIT_TMP/.venv"
uv --no-cache pip install --python "$AUDIT_TMP/.venv/bin/python" \
  -c "$AUDIT_REVIEW/tests/requirements-lock.txt" \
  -r "$AUDIT_TMP/requirements.txt" -r "$AUDIT_TMP/requirements-test.txt"
cd "$AUDIT_TMP"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest \
  -c pytest.ini -o addopts='' -p no:cacheprovider -q --tb=short recheck_tests
```

Ожидаемый baseline —49 passed/55 failed. Чтобы воспроизвести проверенный частично исправленный вариант:

```bash
for AUDIT_PATCH in "$AUDIT_REVIEW"/patches/*.patch; do
  git apply --check --whitespace=error-all "$AUDIT_PATCH"
  git apply --whitespace=error-all "$AUDIT_PATCH"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest \
  -c pytest.ini -o addopts='' -p no:cacheprovider -q --tb=short recheck_tests
```

Ожидается65 passed/39 failed. Отдельный запуск test_history_and_json.py, test_session_lifetime.py и test_executor_guard.py выбирает25 проверок предложенных малых исправлений; все25 прошли в общем прогоне. Падающие tests отзыва/ключей не заменять xfail только ради зелёного результата. В проверке другого тела для того же ключа409 выбран как предлагаемый HTTP-контракт; обязательное требование — отказ без второго эффекта, а числовой статус отдельно владельцем не утверждён. Исходный201 нарушает и это базовое требование.

## Старые тесты и стандартные точки запуска

Для исторических целевых suites в/tmp использованы имена old_review_tests (89498c8/tests), previous_recheck_tests (recheck-d497e75/tests), last_review_tests (recheck-bbf7a39/tests). Первые два набора импортируют временное имя old_review_tests. Их исходные файлы не менялись. Проверялись раздельными процессами: prior60 и last70, чтобы локальный conftest каждого набора был своим.

Фактические пути: baseline `/tmp/tickets-audit4/base`, patched `/tmp/tickets-audit4/patched`; Python `/tmp/tickets-bbf7a39-venv/bin/python`. Основная команда во всех случаях — `python -m pytest -c pytest.ini -o addopts='' -p no:cacheprovider -q --tb=short <suite>`; после patches для prior60 добавлен `-k 'not test_client_disable_preserves_in_progress_and_review_pairs and not test_user_disable_keeps_review_and_saves_linked_suspension'`. Точные argv сохранены в JSON результатов.

Backend-архив ticket_regression_tests.zip открыт после завершения слепого раунда. Содержит7Python-файлов, извлечённых только в/tmp/archived_tests. Отсутствуют прежние modules auxiliary, ticket_application_service, ticket_user_application_service, TicketManagementService/TicketPolicy и enum SCHEDULED; оставшиеся mapper проверки вызывают старые контракты. Эти ошибки сборки не являются доказательством10 новых продуктовых дефектов. Frontend-архивы не открывались.

В очищенном слепом пакете обычный pytest не нашёл тела tests/ и завершился exit5. В воспроизведённом полном Python Git-layout с историческими review/tests корневой collect-only завершился exit2 на двух старых recheck-модулях с импортом old_review_tests. run_pyramid.sh/run_coverage.sh с явно заданным last_review_tests --collect-only собрали70 тестов, exit0; их старая жёсткая ссылка на удалённый config исправлена. Default CI от этого не считается актуальным.

## Дополнительные проверки и ограничения

Повторяемый smoke сохранён в `check_backend.py`. Из корня временной source-копии без `.git` и `.env`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python recheck_tests/check_backend.py
```

Этот скрипт отдельно реально выполнен для baseline и копии с четырьмя патчами: оба exit0,167 AST,115 SQL preparations,integrity/FK,3imports,health200 и OpenAPI200/83paths. Результат — `../results/smoke-results.json`. Скрипт сам создаёт и удаляет временную БД, задаёт случайный тестовый signing key и не входит в число104 pytest-кейсов.

- AST167 файлов исходника —успех; после patches AST167 —успех.
- Импорт main, src.web.main, src.oauth2.main; создание create_app, HTTP /health200 и /openapi.json200 с83paths —успех до/после.
- Реальная подготовка115 gatewaySQL через EXPLAIN на новом schema.sql —успех; integrity_check=ok, foreign_key_check пуст. Это не доказывает бизнес-логику запросов.
- Все4diff прошли check отдельно против SHA и последовательно с whitespace=error-all; реально применены только в/tmp.
- Истинное t0 старых уже ротировавшихся сессий не восстановлено. Перед строгим семисуточным контрактом нужен переходный режим, а не подстановка вымышленной даты.
- PostgreSQL-адаптера в активном wiring нет; PostgreSQL interleaving не исполнялся. SQLite version/rollback тесты guard не подменяют его.
- Полное покрытие и нагрузка не измерялись. Coverage-вывод при collect-only не является процентом покрытия продукта. Deprecation warnings отдельно не считались дефектами.
