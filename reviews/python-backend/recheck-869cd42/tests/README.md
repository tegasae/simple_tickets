# Воспроизведение приёмки

Фиксированный исходник `869cd424b1b9f13babd720884a3cbb7e0f6a10bb`. Проверка исполнена с Python 3.12.14 и SQLite 3.53.1. Из значимых зависимостей использовались FastAPI 0.143.0, Starlette 1.8.0, Pydantic 2.14.1, PyJWT 2.15.1, HTTPX 0.28.1 и pytest 9.2.0. [Полный список пакетов](requirements-lock.txt)

Из корня подключённого Git репозитория создайте среду во временном каталоге. Для запуска необходим объект коммита из указанной ветки и установленный Python 3.12.

```bash
REVIEW="$PWD/reviews/python-backend/recheck-869cd42"
ACCEPTANCE_VENV=$(mktemp -d)
uv venv --python 3.12 "$ACCEPTANCE_VENV/.venv"
uv pip install --python "$ACCEPTANCE_VENV/.venv/bin/python" -r "$REVIEW/tests/requirements-lock.txt"
export ACCEPTANCE_PYTHON="$ACCEPTANCE_VENV/.venv/bin/python"

bash "$REVIEW/tests/reproduce.sh" current
bash "$REVIEW/tests/reproduce.sh" patched
bash "$REVIEW/tests/reproduce.sh" refresh -k 'not idempotent_creations and not idempotency and not creation_storage_rules and not http_roles and not department_initial_state and not admin_profile_department and not account_creation_input and not ticket_work_mode_roundtrip'
bash "$REVIEW/tests/reproduce.sh" historical-current
bash "$REVIEW/tests/reproduce.sh" historical-patched
```

Каждый вызов распаковывает исходник из Git во временный каталог, сохраняет отдельно точный предыдущий DDL для миграции и применяет diff только в этой копии. Порядок серии `05 → 06 → 07 → 08 → 09 → 10`. Рабочая ветка может указывать на другой коммит. Скрипт передаёт `ACCEPTANCE_LEGACY_SCHEMA` и `PYTHONPATH` и выключает запись bytecode и pytest cache. В каждом тесте отдельные синтетические база и логины. HTTP-запрос проходит через реальный FastAPI TestClient. Соответствие сохранённого состояния проверяется отдельным чтением из SQLite.

Для выбора одного теста используйте `-k`. Например, команда ниже проверяет и успешное сохранение исполнителя, и отказ при несовпадении отделов с повторным чтением пары.

```bash
bash "$REVIEW/tests/reproduce.sh" current -k wrong_department_preserves_assigned_pair
bash "$REVIEW/tests/reproduce.sh" patched -k lost_response_is_replayed_after_commit
```

Финальные запуски используют те же первые пять команд с `ACCEPTANCE_PYTHON=/tmp/tickets-bbf7a39-venv/bin/python` и отдельным `--junitxml` во временном каталоге. Например

```bash
bash "$REVIEW/tests/reproduce.sh" patched --disable-warnings \
  --junitxml=/tmp/tickets-accept-869cd42-te5tqc/safe-results/published-after.xml
```

Исходный прогон включает ожидаемые падения отсутствующих N01/N06 и подтверждённых D01–D04, а также пропуски тестов будущей миграции и нового хранилища. Серия содержит два пропуска прежней формы сессий. Причины по каждому случаю приведены в протоколе. Исходные JUnit и журналы остаются во временной области. Исторические 70 регрессий из `recheck-bbf7a39/tests` запускаются отдельным процессом. Их исходники взяты из Git без правок. [Протокол](results.md) · [Идентификаторы и статусы](run-data.json)

## Синтаксис, схема и точки входа

Выполнены обе команды. Они вызывают `check_backend.py` из материалов 5288dea, сохранённых в целевом коммите. Патченная сборка дополнительно проверяет AST скрипта миграции.

```bash
bash "$REVIEW/tests/reproduce.sh" smoke-current
bash "$REVIEW/tests/reproduce.sh" smoke-patched
```

Команда `"$ACCEPTANCE_PYTHON" -m pytest -o addopts='' -p no:cacheprovider --collect-only -q` в оригинальной временной копии дала 5. Файл `pytest.ini` указывает на отсутствующий штатный каталог tests. Выводы smoke записаны отдельно. [Результаты](smoke-results.json)

Контроль прежней версии выполнялся с Git archive снимка `5288dea85d8f7e7e4c84d4801781d297e0e14475` и теми же модулями приёмки. Для контроля D01–D04 использовались цели `test_department_initial_state.py`, `test_admin_profile_department.py`, `test_account_creation_input.py` и `test_ticket_work_mode_roundtrip.py`. Для 11 сравнений F-01–F-05 использовались модуль комментариев без телефонной атрибуции, начальные settings, тесты сохранения дедлайна и варианты назначения из `test_executor_guard.py`. [Список выполненных test ID](run-data.json)

Штатный runtime в контейнере Python 3.14 и будущий PostgreSQL проверяются после подготовки окружения и соответствующего адаптера. Для PostgreSQL нужны независимые соединения и управляемые порядки фиксации назначения, отзыва и ключа. Фактические значения среды production и реальные данные исключены из тестов.
