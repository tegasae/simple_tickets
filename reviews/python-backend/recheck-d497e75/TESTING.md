# Воспроизведение проверок

Проверки выполнены на Python 3.12.14, SQLite 3.53.1, FastAPI 0.143.0, Pydantic 2.14.1 и pytest 9.1.1. В окружении с предыдущего аудита был установлен тот же `requirements.txt`. Приведённые ниже команды создают автономную временную копию. Они извлекают Python, схему и тестовые исходники. Временные базы создаются из DDL и собственных фикстур.

Выполнить из корня checkout `tegasae/simple_tickets` с этим каталогом результатов:

```bash
recheck_sha=d497e75d4937e8edea98783a5af924c247622e06
audit_dir="$PWD/reviews/python-backend/recheck-d497e75"
audit_scratch="$(mktemp -d)"
mkdir -p "$audit_scratch"/{base,patched}
git archive "$recheck_sha" src utils main.py config.py models.py db/schema.sql \
  pytest.ini requirements.txt tests_pyramid |
  tar -x -C "$audit_scratch/base"
mkdir "$audit_scratch/base/old_review_tests"
git archive "$recheck_sha" reviews/python-backend/89498c8/tests |
  tar -x --strip-components=4 -C "$audit_scratch/base/old_review_tests"
cp -a "$audit_dir/tests" "$audit_scratch/base/recheck_tests"
cp -a "$audit_scratch/base/." "$audit_scratch/patched/"
uv --no-cache venv "$audit_scratch/venv"
uv --no-cache pip install --python "$audit_scratch/venv/bin/python" \
  -r "$audit_scratch/base/requirements.txt"
git -C "$audit_scratch/patched" apply --check --whitespace=error-all "$audit_dir"/patches/*.patch
git -C "$audit_scratch/patched" apply "$audit_dir"/patches/*.patch
```

В обеих копиях из их корня:

```bash
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 "$audit_scratch/venv/bin/python" \
  -m pytest -o addopts='' -p no:cacheprovider -q --tb=short recheck_tests
```

На текущем коммите запускались все `old_review_tests`. В исправленной копии проверялись остальные 37 прежних сценариев. Два прежних ожидания для каскадов заменены новыми проверками. В них `READY_FOR_REVIEW` при отключении клиента или отдельного владельца закрывается как `SUSPENDED`, а непосредственно активная пара `AT_WORK/IN_WORK` остаётся открытой.

```bash
# В корне base.
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 "$audit_scratch/venv/bin/python" \
  -m pytest -o addopts='' -p no:cacheprovider -q --tb=short old_review_tests

# В корне patched.
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 "$audit_scratch/venv/bin/python" \
  -m pytest -o addopts='' -p no:cacheprovider -q --tb=short old_review_tests \
  -k 'not test_client_disable_preserves_in_progress_and_review_pairs and not test_user_disable_keeps_review_and_saves_linked_suspension'
```

Штатные тесты в `tests_pyramid` используют файл `db/admins.db` как исходную схему. Для этого прогона из корня `base`:

```bash
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 "$audit_scratch/venv/bin/python" -B - <<'PY'
import os
import secrets
import sqlite3
import sys
from pathlib import Path

import pytest

os.environ["SECRET_KEY"] = secrets.token_hex(32)
with sqlite3.connect("db/admins.db") as db:
    db.executescript(Path("db/schema.sql").read_text())
sys.exit(pytest.main([
    "-o", "addopts=", "-c", "tests_pyramid/pytest.ini", "-p", "no:cacheprovider",
    "--continue-on-collection-errors", "-q", "--tb=no", "tests_pyramid",
]))
PY
```

`tests_pyramid` использует старые имена классов, модули и контракты. Например, сборка ссылается на отсутствующий `src.web.models.mappers`. Маршрутные контрактные тесты обходят `app.routes` в формате, на который влияют изменения FastAPI. Smoke `/openapi.json` и реальные запросы отдельно подтвердили наличие действующих маршрутов. Пирамида остаётся красной. Серию патчей следует оценивать по новым целевым тестам и пройденной части прежних регрессий.

После уточнения о закрытии `READY_FOR_REVIEW` при отключении владельца добавлен тест `test_owner_disable_closes_both_tickets_awaiting_review`. Он проверяет исходное состояние пары, два ответа 200, даты закрытия и единственную запись `SUSPENDED` в каждой истории. Полный повтор `recheck_tests` дал 20 падений и один пройденный тест на исходном SHA, 21 пройденный тест после серии патчей.
