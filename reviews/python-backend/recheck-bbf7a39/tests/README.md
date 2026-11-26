# Проверки и воспроизведение

Источник — bbf7a392dafe0fede2d5d017af36281b6f4f40a2. Здесь70 pytest-проверок, включая параметры. Все используют временную SQLite из исходного DDL, синтетические сущности и случайные учётные значения. Фикстура world выполняет реальные Admin/User login; auth/repositories для этих сценариев не подменяются. Инъекции только для оговорённых отказов записи и барьера конкурентных запросов. `.env` и существующие БД для запуска не нужны.

[Версии среды](environment.json): Python3.12.14, SQLite3.53.1, FastAPI0.143.0, Starlette1.8.0, Pydantic2.14.1, pytest9.2.0, httpx0.28.1. Проверка Python3.13 и PostgreSQL не выполнялась. Зависимости установлены из requirements.txt + requirements-test.txt через uv в отдельное venv. Инструкции ниже создают такую же изоляцию; фактические временные пути текущего прогона перечислены дальше.

## Состав

| Модуль | Количество | Предмет |
|---|---:|---|
| test_current_workflows.py |7| Новые правила отключения, AT_WORK, сохранение контакта/комментария, автор, refresh identity memory/SQLite |
| test_contact_and_department.py |22| Две стороны контакта и статусы; ограничение description; enable Admin/Department и guard версии |
| test_rbac_and_validation.py |17| Права create/revoke; пароль/login/permissions/description; ожидаемые отказы; DELETE назначенной User-роли |
| test_persistence_and_dates.py |15| Assigned SQL; новые UTC defaults; SQL/HTTP roundtrip; сохранение исторических дат |
| test_atomicity_and_contention.py |3| Реальный второй save и rollback create/cancel; два HTTP PATCH и один временный отказ |
| test_database_error_classification.py |6| Locks insert/commit, rollback, duplicate409, неизвестная ошибка500 |
| **Итого** |**70**| Число параметров не равно числу независимых дефектов |

## Безопасная подготовка временной копии

Выполнять из shell на машине с Git/Python3.12/uv. AUDIT_REPO — путь к репозиторию, содержащему Git-объект нужного SHA и новый каталог отчёта. Рабочие файлы репозитория не исправляются. Нельзя брать production DATABASE_URL или копировать рабочие БД.

```bash
AUDIT_REPO=/path/to/simple_tickets
AUDIT_SHA=bbf7a392dafe0fede2d5d017af36281b6f4f40a2
AUDIT_REVIEW="$AUDIT_REPO/reviews/python-backend/recheck-bbf7a39"
AUDIT_TMP=$(mktemp -d)
git -C "$AUDIT_REPO" archive "$AUDIT_SHA" \
  src utils db/schema.sql main.py models.py config.py \
  requirements.txt requirements-test.txt pytest.ini .coveragerc \
  run_pyramid.sh run_coverage.sh | tar -x -C "$AUDIT_TMP"
cp -R "$AUDIT_REVIEW/tests" "$AUDIT_TMP/recheck_tests"
uv venv --python 3.12 "$AUDIT_TMP/.venv"
uv --no-cache pip install --python "$AUDIT_TMP/.venv/bin/python" \
  -r "$AUDIT_TMP/requirements.txt" -r "$AUDIT_TMP/requirements-test.txt"
cd "$AUDIT_TMP"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest \
  -c pytest.ini -o addopts='' -p no:cacheprovider -q --tb=short recheck_tests
```

conftest.py задаёт случайный SECRET_KEY до импорта app, а каждая фикстура задаёт собственный DATABASE_URL и memory backend. Дополнительный тест refresh создаёт отдельный временный SQLite backend. Не записывайте значения токенов, паролей или секретного ключа в отчёт. Для импортов без conftest установите случайный ключ в окружении Python-процесса, не печатая его.

На исходнике ожидается **29 passed,41 failed**, exit1. Это намеренные assertions нужного поведения, а не настроенный xfail. Два lock-теста имеют ограниченный барьер; зависший участник не должен ждать бесконечно. Не запускайте timezone-тесты параллельно в одном процессе: они временно меняют process TZ с гарантированным восстановлением.

## Применение серии только во временной копии

Каждый diff отдельно проверен против исходного SHA. Для полного варианта используйте порядок имён:

```bash
for AUDIT_PATCH in "$AUDIT_REVIEW"/patches/*.patch; do
  git apply --check --whitespace=error-all "$AUDIT_PATCH"
  git apply --whitespace=error-all "$AUDIT_PATCH"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest \
  -c pytest.ini -o addopts='' -p no:cacheprovider -q --tb=short recheck_tests
```

Эти команды выполняются после `cd "$AUDIT_TMP"`, **не** в AUDIT_REPO. Для индивидуального check каждого diff нужна новая исходная временная копия; второй check в примере уже учитывает предыдущие исправления серии. Ожидается **70 passed**, exit0. До/после сравнивается только зафиксированный код, без пользовательских БД.

## Регрессии старых аудитов

Их исходные файлы не переписывались. Для выполнения потребовались имена временных пакетов, на которые ссылаются старые тесты:

```bash
mkdir -p "$AUDIT_TMP/old-materials"
git -C "$AUDIT_REPO" archive "$AUDIT_SHA" \
  reviews/python-backend/89498c8/tests \
  reviews/python-backend/recheck-d497e75/tests | tar -x -C "$AUDIT_TMP/old-materials"
cp -R "$AUDIT_TMP/old-materials/reviews/python-backend/89498c8/tests" \
  "$AUDIT_TMP/old_review_tests"
cp -R "$AUDIT_TMP/old-materials/reviews/python-backend/recheck-d497e75/tests" \
  "$AUDIT_TMP/previous_recheck_tests"
rm -rf "$AUDIT_TMP/old-materials"
```

На исходнике полный прогон `old_review_tests previous_recheck_tests recheck_tests` дал86 passed,44 failed. На исправленной копии команда:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python -m pytest \
  -c pytest.ini -o addopts='' -p no:cacheprovider -q --tb=short \
  -k 'not test_client_disable_preserves_in_progress_and_review_pairs and not test_user_disable_keeps_review_and_saves_linked_suspension' \
  old_review_tests previous_recheck_tests recheck_tests
```

дала **128 passed,2 deselected**, exit0,848 warnings,39.85s в данной среде. Исключены ровно два названных старых сценария: они требуют оставить READY_FOR_REVIEW при отключении. Это противоречит актуальному требованию владельца; новые тесты проверяют SUSPENDED и сохранность обеих историй. Прежний COMMIT/re-entry тест входит в прошедшие37; скрытого третьего исключения нет.

На первоначальном промежуточном комплекте патчей он остановился на regex `commit` в тексте исключения. Диагностический контекст фазы сохранён в финальном08, после чего проверены rollback и повторное использование UoW. Промежуточные черновые числа до этой корректировки не являются финальным результатом.

## Другие фактически выполненные команды

Фактическая среда: `/tmp/tickets-bbf7a39-venv/bin/python`. Координаторские копии — `/tmp/tickets-third-bbf7a39/verified-base` и `verified-final`. Общая команда совпадает с приведённой выше; XML создавался через `--junitxml` в `/tmp`. [results.json](results.json) сохраняет идентификаторы, исходы и точную argv команды; captured stdout, credentials и тела запросов туда не переносились.

- `ast.parse` всех src/utils/root Python:166 исходных,167 после добавления адаптера; оба прохода успешны.
- Импорты `main`, `src.web.main`, `src.oauth2.main` в отдельном процессе с синтетическим окружением:3/3 на исходнике и после патчей.
- Все115 SQL-констант действующих gateway-классов подготовлены `EXPLAIN` на новой БД. Оба варианта схемы прошли integrity_check и foreign_key_check. Это не заменяет проверки логики SQL. Воспроизводимый алгоритм приведён ниже.
- `pytest --collect-only` на Python-layout исходного репозитория с историческими review/tests: exit2, два старых recheck-модуля импортируют временный old_review_tests. В очищенном общем пакете без старых отчётов pytest не нашёл тестов, exit5. Это разные размещения, результаты не противоречат друг другу.
- `bash run_pyramid.sh --collect-only` и `bash run_coverage.sh --collect-only`: до10 exit4, config отсутствует. После10 с явным `recheck_tests --collect-only -p no:cacheprovider` — exit0,70 collected у каждого. Coverage с collect-only не является продуктовой метрикой покрытия; процент в служебном выводе не используется.

Шаблон подготовки SQL, запускать из соответствующей временной копии:

```python
import importlib
import pathlib
import re
import sqlite3

root = pathlib.Path.cwd()
with sqlite3.connect(":memory:") as db:
    db.executescript((root / "db/schema.sql").read_text())
    count = 0
    for path in (root / "src/adapters/repositories/gateways").glob("*.py"):
        module = importlib.import_module(".".join(path.relative_to(root).with_suffix("").parts))
        for cls in vars(module).values():
            if not isinstance(cls, type) or cls.__module__ != module.__name__:
                continue
            for sql in vars(cls).values():
                if not isinstance(sql, str) or not sql.lstrip().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
                    continue
                params = {name: 1 for name in re.findall(r":([a-zA-Z_]\w*)", sql)}
                db.execute("EXPLAIN " + sql, params)
                count += 1
    assert count == 115
    assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
```

Основные848 предупреждений: deprecated sqlite datetime adapter Python3.12, устаревающая class-based Pydantic Config и совместимость TestClient/httpx. Они не считались новыми продуктовым дефектами. Производительность, полное покрытие и PostgreSQL этим набором не подтверждаются.
