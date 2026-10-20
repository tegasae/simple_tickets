# Simple Tickets: CI/CD через GitHub, локальный Registry и pull-based deployment

**Статус:** проект схемы для тестового окружения  
**Компоненты:** GitHub → build-server + Docker Registry → application-server  
**Принцип:** application-server сам обнаруживает и устанавливает новые версии; build-server никогда не подключается к нему по SSH.

## 1. Требования и принятые решения

1. На рабочем компьютере выполняются только `git commit` и `git push` в GitHub.
2. Отдельный **build-server** периодически проверяет заданную ветку GitHub, собирает backend image и публикует его в **локальном Docker Registry на том же сервере**.
3. Отдельный **application-server** периодически проверяет Registry, самостоятельно загружает новый image и обновляет backend. Система сборки не управляет application-server.
4. Сейчас проект тестовый, схема SQLite может меняться. **В image помещается эталонный `admins.db`**, соответствующий исходникам конкретного commit.
5. Рабочая SQLite находится **вне контейнера**, в каталоге application-server. В тестовом режиме при каждом новом image она **заменяется** эталонной БД из нового image, с предварительным backup старой БД.
6. Backend остаётся доступен снаружи на опубликованном порту. Используется **один Uvicorn worker**, в частности из-за `TokenStorageMemory`.
7. Никаких Forgejo, GitLab, Jenkins, Kubernetes и push-deployment по SSH пока не требуется.

> **Важно:** сценарий ниже намеренно *сбрасывает изменения рабочей тестовой базы* при установке нового image. Для настоящих пользовательских данных нужна другая схема — сохранение БД и миграции. В GitHub и image должна находиться исключительно обезличенная тестовая база без реальных паролей, персональных данных и секретов.

## 2. Архитектура

```text
┌─────────────────┐
│ Рабочий ПК      │
│ git commit/push │
└────────┬────────┘
         │
         ▼
┌───────────────────────────────┐
│ GitHub                        │
│ branch: test-deploy           │
└────────┬──────────────────────┘
         │ git ls-remote / clone (polling)
         ▼
┌─────────────────────────────────────────────────────┐
│ BUILD-SERVER                                        │
│                                                     │
│ systemd timer → check GitHub SHA                    │
│             → clone конкретной версии               │
│             → tests (по мере настройки)             │
│             → docker build                          │
│             → docker push                           │
│                                                     │
│ Docker Registry: registry.example.lan:5000          │
│   simple-tickets-backend:<commit SHA>               │
│   simple-tickets-backend:test                       │
└──────────────────────┬──────────────────────────────┘
                       │ docker pull (инициатива app-server)
                       ▼
┌─────────────────────────────────────────────────────┐
│ APPLICATION-SERVER                                  │
│                                                     │
│ systemd timer → docker pull :test                   │
│             → сравнить image ID                     │
│             → сохранить точный image digest         │
│             → остановить backend                    │
│             → backup SQLite                         │
│             → извлечь bootstrap SQLite              │
│             → docker compose up -d                  │
│             → проверить /health                     │
│                                                     │
│ /srv/simple-tickets/db/admins.db  → /app/db/admins.db│
│ Backend: host:8080 → container:8000                  │
└─────────────────────────────────────────────────────┘
```

**Контракт между сборкой и эксплуатацией — только OCI/Docker image в Registry.** Завтра можно заменить GitHub, builder и registry, не меняя принцип работы application-server: достаточно изменить ссылку на отслеживаемый image и доступ к Registry.

## 3. Имена и каталоги в примерах

В примерах используются **условные адреса**, их нужно заменить:

| Параметр | Значение в примере |
|---|---|
| GitHub repository | `git@github.com:ORG/simple_tickets.git` |
| Отслеживаемая ветка | `test-deploy` |
| Registry | `registry.example.lan:5000` |
| Репозиторий образов | `registry.example.lan:5000/simple-tickets-backend` |
| Подвижный тег | `:test` |
| Build state | `/var/lib/simple-tickets-builder/` |
| Registry data | `/srv/docker-registry/data/` |
| Application directory | `/srv/simple-tickets/` |
| Backend host port | `8080` |

На build-server и application-server должны быть доступны Docker CLI/daemon; на application-server также Docker Compose v2, `curl`, `flock` (util-linux), Python 3 (для SQLite backup/проверки). На build-server нужны `git`, Docker, systemd.

---

# Часть I. Backend image

## 4. Структура GitHub-репозитория

```text
simple_tickets/
├── docker/
│   └── backend/
│       └── Dockerfile
├── src/
├── utils/
├── db/
│   └── admins.db          # обезличенная тестовая база
├── requirements.txt
├── .dockerignore
└── ...
```

Если `db/admins.db` сейчас исключён из Git, следует **осознанно** решить, можно ли хранить его в GitHub. Проверьте:

```bash
git ls-files db/admins.db
```

При отсутствии файла в Git checkout на build-server не сможет включить базу в image. Если в ней есть реальные данные/секреты, **не** добавляйте её: вместо этого используйте отдельный защищённый источник эталонной DB или генерируйте тестовую базу из SQL/fixtures при сборке.

### `.dockerignore`

```dockerignore
.git
.idea
.venv
.venv*
__pycache__
**/__pycache__
*.pyc
.pytest_cache
.env
.env.*
*.zip
db/*.db-wal
db/*.db-shm
db/*.db-journal
```

Не исключайте `db/admins.db`: он нужен как bootstrap DB.

## 5. `docker/backend/Dockerfile`

```dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY utils ./utils

# Тестовая база этого релиза, НЕ рабочая база.
COPY db/admins.db /app/bootstrap/admins.db

# Рабочая БД монтируется с application-server.
ENV DATABASE_URL=/app/db/admins.db

EXPOSE 8000

CMD ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Почему не `COPY db/admins.db /app/db/admins.db`?** Потому что приложение изменяет `/app/db/admins.db`; рабочие изменения должны жить в bind mount, не в writable layer контейнера.

`VOLUME ["/app/db"]` в Dockerfile специально не нужен: mount будет явно указан на целевом сервере в `compose.yml`. Для извлечения bootstrap DB используется независимый путь `/app/bootstrap/admins.db`.

Важное следствие: переменные из `.env` передаются **при запуске** контейнера. Файл с `SECRET_KEY` в image не копируется.

---

# Часть II. Локальный Registry на build-server

## 6. Подготовка Registry

В качестве примера — официальный CNCF Distribution registry. На момент подготовки документа актуальная документация использует `registry:3`.

```bash
sudo mkdir -p /srv/docker-registry/{data,certs,auth}
```

Для доступа **с другого сервера** Registry должен быть доступен по сети. Рекомендуется HTTPS с сертификатом на `registry.example.lan` и базовая аутентификация. Разместите заранее полученные сертификат и ключ:

```text
/srv/docker-registry/certs/fullchain.pem
/srv/docker-registry/certs/privkey.pem
```

Для приватного домена можно использовать свою CA. Её сертификат должен быть доверенным Docker daemon на **обоих** серверах. Например:

```text
/etc/docker/certs.d/registry.example.lan:5000/ca.crt
```

После установки CA может потребоваться перезапуск Docker daemon. **Не отключайте TLS-проверку без необходимости.** Для временных лабораторных испытаний Docker поддерживает `insecure-registries`, но это отдельное, сознательно менее безопасное решение.

Создайте пользователей для Registry (утилита `htpasswd`, пакет `apache2-utils`):

```bash
sudo htpasswd -B -c /srv/docker-registry/auth/htpasswd builder
sudo htpasswd -B    /srv/docker-registry/auth/htpasswd deployer
```

Команды интерактивно попросят пароли. Встроенная htpasswd-аутентификация **не** предоставляет раздельных ролей на push/pull: эти пользователи не являются строго `write-only` и `read-only`. Для полноценной RBAC понадобится другая система авторизации или proxy.

### `/srv/docker-registry/compose.yml`

```yaml
services:
  registry:
    image: registry:3
    container_name: local-registry
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      REGISTRY_HTTP_ADDR: "0.0.0.0:5000"
      REGISTRY_HTTP_TLS_CERTIFICATE: "/certs/fullchain.pem"
      REGISTRY_HTTP_TLS_KEY: "/certs/privkey.pem"
      REGISTRY_AUTH: "htpasswd"
      REGISTRY_AUTH_HTPASSWD_REALM: "Local Registry"
      REGISTRY_AUTH_HTPASSWD_PATH: "/auth/htpasswd"
    volumes:
      - /srv/docker-registry/data:/var/lib/registry
      - /srv/docker-registry/certs:/certs:ro
      - /srv/docker-registry/auth:/auth:ro
```

Запуск:

```bash
cd /srv/docker-registry
docker compose up -d
curl --cacert /path/to/ca.crt https://registry.example.lan:5000/v2/
```

При включённой авторизации ответ **`401 Unauthorized` без credentials** означает, что Registry жив и требует входа.

На build-server:

```bash
docker login registry.example.lan:5000
```

На application-server делается отдельный `docker login` с его учётной записью. Авторизация и доверие CA должны быть настроены для того **пользователя и Docker daemon**, от имени которых реально выполняются systemd jobs.

Проверка вручную (из корня проекта):

```bash
docker build -f docker/backend/Dockerfile \
    -t registry.example.lan:5000/simple-tickets-backend:manual-test .

docker push registry.example.lan:5000/simple-tickets-backend:manual-test
```

---

# Часть III. Автоматическая сборка на build-server

## 7. Идея polling GitHub

Build-server раз в минуту выполняет:

```bash
git ls-remote git@github.com:ORG/simple_tickets.git refs/heads/test-deploy
```

Git возвращает SHA текущей вершины ветки. SHA сравнивается с **последним успешно опубликованным SHA**, сохранённым локально:

```text
/var/lib/simple-tickets-builder/last-successful.sha
```

Если SHA не изменился — ничего не делаем. Если изменился — clone нужного состояния, тесты, сборка, push. **SHA обновляем только после успешного push обоих тегов**. При ошибке следующая проверка повторит попытку.

Polling видит **текущее состояние ветки**, а не каждое промежуточное событие: если между двумя проверками в ветку отправлены несколько commit, будет собран последний. Для тестового канала это обычно правильно.

Для приватного GitHub-репозитория настройте на build-server SSH deploy key с правом чтения. Скрипт не должен иметь доступ к вашему личному GitHub-токену.

## 8. Скрипт проверки и сборки

Путь: `/usr/local/bin/simple-tickets-build-check.sh`.

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="git@github.com:ORG/simple_tickets.git"
BRANCH="test-deploy"
IMAGE="registry.example.lan:5000/simple-tickets-backend"
STATE_DIR="/var/lib/simple-tickets-builder"
SUCCESS_FILE="$STATE_DIR/last-successful.sha"

mkdir -p "$STATE_DIR"

# Не допустить параллельных сборок (timer + ручной запуск).
exec 9>"$STATE_DIR/build.lock"
flock -n 9 || exit 0

REMOTE_SHA="$(git ls-remote "$REPO" "refs/heads/$BRANCH" | awk '{print $1}')"
[[ "$REMOTE_SHA" =~ ^[0-9a-f]{40}$ ]] || {
    echo "Unable to resolve remote branch SHA" >&2
    exit 1
}

LAST_SHA="$(cat "$SUCCESS_FILE" 2>/dev/null || true)"
if [[ "$REMOTE_SHA" == "$LAST_SHA" ]]; then
    exit 0
fi

echo "New GitHub revision: $REMOTE_SHA"
WORK_DIR="$(mktemp -d "$STATE_DIR/work.XXXXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

git clone --quiet --depth 1 --single-branch --branch "$BRANCH" \
    "$REPO" "$WORK_DIR"

CHECKED_OUT_SHA="$(git -C "$WORK_DIR" rev-parse HEAD)"
[[ "$CHECKED_OUT_SHA" == "$REMOTE_SHA" ]] || {
    echo "Branch advanced during clone; will retry on next poll" >&2
    exit 1
}

cd "$WORK_DIR"

# -----------------------------------------------------------
# Tests: включить, когда согласована команда тестирования.
# Например (только при настроенном Python/test environment):
# python -m pytest tests_pyramid
# -----------------------------------------------------------

COMMIT_IMAGE="$IMAGE:$REMOTE_SHA"
TEST_IMAGE="$IMAGE:test"

docker build \
    -f docker/backend/Dockerfile \
    -t "$COMMIT_IMAGE" \
    -t "$TEST_IMAGE" \
    .

# Сначала публикуем постоянный tag, затем подвижный.
docker push "$COMMIT_IMAGE"
docker push "$TEST_IMAGE"

printf '%s\n' "$REMOTE_SHA" > "$SUCCESS_FILE"
echo "Published $COMMIT_IMAGE and $TEST_IMAGE"
```

Скрипт выполняется под отдельным техническим пользователем (например, `st-builder`), имеющим доступ к GitHub по SSH, возможность работать с Docker и запись в `STATE_DIR`. **Доступ к Docker daemon практически равен административным правам на хосте**: такой builder нужно считать доверенным.

Подготовка, например:

```bash
sudo install -d -o st-builder -g st-builder -m 0700 \
    /var/lib/simple-tickets-builder
sudo chmod +x /usr/local/bin/simple-tickets-build-check.sh
```

Создание пользователя и выдача доступа к Docker/SSH настраиваются под вашу ОС отдельно.

## 9. systemd на build-server

`/etc/systemd/system/simple-tickets-build-check.service`:

```ini
[Unit]
Description=Check GitHub and build Simple Tickets image
Wants=network-online.target
After=network-online.target docker.service

[Service]
Type=oneshot
User=st-builder
ExecStart=/usr/local/bin/simple-tickets-build-check.sh
```

`/etc/systemd/system/simple-tickets-build-check.timer`:

```ini
[Unit]
Description=Poll Simple Tickets GitHub branch

[Timer]
OnBootSec=1min
OnUnitInactiveSec=1min
AccuracySec=10s
Unit=simple-tickets-build-check.service

[Install]
WantedBy=timers.target
```

Включить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now simple-tickets-build-check.timer
systemctl list-timers | grep simple-tickets
```

Ручная проверка:

```bash
sudo systemctl start simple-tickets-build-check.service
journalctl -u simple-tickets-build-check.service -n 100 --no-pager
```

В итоге build-server публикует:

```text
registry.example.lan:5000/simple-tickets-backend:<40-character-SHA>
registry.example.lan:5000/simple-tickets-backend:test
```

---

# Часть IV. Application-server: самостоятельное обновление

## 10. Каталоги

```text
/srv/simple-tickets/
├── compose.yml
├── runtime.env       # настройки приложения и SECRET_KEY, не Git
├── release.env       # создаёт deployment script, pinned image
├── db/
│   └── admins.db     # рабочая SQLite
└── backups/
    └── admins-*.db
```

`release.env` — состояние уже **выбранного конкретного image**, а не ссылка на подвижный тег. Например:

```dotenv
BACKEND_IMAGE=registry.example.lan:5000/simple-tickets-backend@sha256:012345...<полный digest>
```

Его создаёт deploy-script. Использовать сокращённый digest в настоящем файле нельзя.

Пример `runtime.env`:

```dotenv
APP_NAME=Simple Tickets API
APP_VERSION=1.0.0
SECRET_KEY=REPLACE_WITH_STRONG_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=1
JWT_ISSUER=simple-tickets
JWT_AUDIENCE=simple-tickets-api
ENVIRONMENT=testing
```

Для **`docker run --env-file`** кавычки в значениях не нужны: мы уже сталкивались с тем, что `DATABASE_URL="..."` передавался с кавычками буквально. Здесь `DATABASE_URL` вообще задаётся в `compose.yml`.

Права:

```bash
sudo mkdir -p /srv/simple-tickets/{db,backups}
sudo chmod 0700 /srv/simple-tickets/backups
sudo chmod 0600 /srv/simple-tickets/runtime.env
```

## 11. `/srv/simple-tickets/compose.yml`

```yaml
services:
  backend:
    image: "${BACKEND_IMAGE:?BACKEND_IMAGE must be set}"
    container_name: simple-tickets-backend
    restart: unless-stopped

    ports:
      - "8080:8000"

    env_file:
      - /srv/simple-tickets/runtime.env

    environment:
      DATABASE_URL: /app/db/admins.db

    volumes:
      - /srv/simple-tickets/db:/app/db
```

Порт backend **доступен снаружи** как `http://<application-server>:8080`; внутри контейнера Uvicorn слушает `8000`. Доступ извне регулируйте firewall/VPN — особенно если API пока тестовый.

`BACKEND_IMAGE` подставляется Compose из файла `release.env`, переданного через `docker compose --env-file ...`. Это **не то же самое**, что `env_file:` внутри сервиса: последний передаёт переменные приложению в контейнер.

## 12. Почему application-server следит за `:test`, но запускает digest

Проверка:

```bash
docker pull registry.example.lan:5000/simple-tickets-backend:test
```

Сравниваются:

```text
image ID скачанного :test
image ID контейнера simple-tickets-backend
```

Если совпадают **и контейнер работает** — обновление не требуется. Если различаются — у нового тега получаем **неизменяемую ссылку вида `repository@sha256:...`**, её и сохраняем в `release.env`.

Таким образом обновления привязаны не к изменяемому имени `:test`, а к точному артефакту. Это также позволяет затем выполнить откат, если старый digest всё ещё доступен в registry.

## 13. Скрипт проверки и deployment

Путь: `/usr/local/sbin/simple-tickets-update.sh`.

**Поведение:**

- не делает ничего, если работающий backend уже использует image, который сейчас обозначен `:test`;
- скачивает новый image и находит точный digest;
- останавливает backend **до** backup/замены рабочей БД;
- выполняет согласованный SQLite backup через `sqlite3.Connection.backup`;
- извлекает новую эталонную БД из image и проверяет `PRAGMA quick_check`;
- заменяет рабочую БД и пересоздаёт backend;
- проверяет `/health`; при ошибке пытается восстановить прежний image и прежнюю SQLite.

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/srv/simple-tickets"
DB_DIR="$APP_DIR/db"
DB_FILE="$DB_DIR/admins.db"
BACKUP_DIR="$APP_DIR/backups"
RELEASE_FILE="$APP_DIR/release.env"
COMPOSE_FILE="$APP_DIR/compose.yml"
CONTAINER="simple-tickets-backend"

IMAGE_REPO="registry.example.lan:5000/simple-tickets-backend"
TRACK_IMAGE="$IMAGE_REPO:test"
HEALTH_URL="http://127.0.0.1:8080/health"

mkdir -p "$DB_DIR" "$BACKUP_DIR"
exec 9>"$APP_DIR/update.lock"
flock -n 9 || exit 0

# Получение последней версии: никаких команд с build-server.
docker pull "$TRACK_IMAGE"
NEW_IMAGE_ID="$(docker image inspect "$TRACK_IMAGE" --format '{{.Id}}')"

OLD_CONTAINER_ID="$(docker container inspect "$CONTAINER" --format '{{.Image}}' 2>/dev/null || true)"
OLD_RUNNING="$(docker container inspect "$CONTAINER" --format '{{.State.Running}}' 2>/dev/null || true)"

if [[ "$NEW_IMAGE_ID" == "$OLD_CONTAINER_ID" && "$OLD_RUNNING" == "true" ]]; then
    exit 0
fi

# Выбираем digest именно нашего репозитория.
PINNED_REF="$(
    docker image inspect "$TRACK_IMAGE" \
        --format '{{range .RepoDigests}}{{println .}}{{end}}' \
        | grep -F "${IMAGE_REPO}@" | head -n 1 || true
)"

[[ -n "$PINNED_REF" ]] || {
    echo "Cannot resolve image digest for $TRACK_IMAGE" >&2
    exit 1
}

# Неизменяемая ссылка, сохраняемая в release.env.
# Проверяем, что она действительно относится к скачанному image.
PINNED_ID="$(docker image inspect "$PINNED_REF" --format '{{.Id}}')"
[[ "$PINNED_ID" == "$NEW_IMAGE_ID" ]] || exit 1

OLD_RELEASE=""
if [[ -f "$RELEASE_FILE" ]]; then
    OLD_RELEASE="$(sed -n 's/^BACKEND_IMAGE=//p' "$RELEASE_FILE" | head -n 1)"
fi

BACKUP_FILE=""
DB_REPLACED=0
ROLLBACK_REQUIRED=0
EXTRACT_CID=""
STAGING_DIR="$(mktemp -d "$DB_DIR/.incoming.XXXXXXXX")"

compose_up() {
    docker compose \
        -f "$COMPOSE_FILE" \
        --env-file "$RELEASE_FILE" \
        up -d --pull never --force-recreate backend
}

stop_backend() {
    if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
        docker stop --time 30 "$CONTAINER" >/dev/null
    fi
}

check_health() {
    for _ in $(seq 1 30); do
        if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

restore_old_state() {
    echo "Deployment failed; attempting rollback" >&2
    stop_backend || true

    if [[ "$DB_REPLACED" == "1" ]]; then
        # Backend остановлен; старые SQLite sidecar-файлы больше
        # не должны относиться к восстанавливаемой базе.
        rm -f "$DB_FILE-wal" "$DB_FILE-shm" "$DB_FILE-journal"
        if [[ -n "$BACKUP_FILE" && -f "$BACKUP_FILE" ]]; then
            cp "$BACKUP_FILE" "$DB_DIR/.admins.db.restore"
            mv -f "$DB_DIR/.admins.db.restore" "$DB_FILE"
        else
            rm -f "$DB_FILE"   # первой рабочей базы ещё не было
        fi
    fi

    if [[ -n "$OLD_RELEASE" ]]; then
        printf 'BACKEND_IMAGE=%s\n' "$OLD_RELEASE" > "$APP_DIR/.release.rollback"
        mv -f "$APP_DIR/.release.rollback" "$RELEASE_FILE"
        compose_up || echo "Rollback start failed: manual recovery required" >&2
    else
        rm -f "$RELEASE_FILE"
        echo "First deployment failed; no previous release to restart" >&2
    fi
}

on_exit() {
    rc=$?
    trap - EXIT
    if [[ "$rc" -ne 0 && "$ROLLBACK_REQUIRED" == "1" ]]; then
        restore_old_state || true
    fi
    [[ -z "$EXTRACT_CID" ]] || docker rm -f "$EXTRACT_CID" >/dev/null 2>&1 || true
    rm -rf "$STAGING_DIR"
    exit "$rc"
}
trap on_exit EXIT

# Чтобы при аварии во время обновления можно было поднять старый релиз.
ROLLBACK_REQUIRED=1
stop_backend

# В тестовой схеме база меняется целиком, но сначала сохраняем старую.
# Python sqlite3.backup корректно читает SQLite и WAL.
if [[ -f "$DB_FILE" ]]; then
    BACKUP_FILE="$(mktemp "$BACKUP_DIR/admins-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX.db")"
    python3 - "$DB_FILE" "$BACKUP_FILE" <<'PY'
import sqlite3
import sys

src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()
PY
fi

# Временный container для извлечения файла: backend не запускается.
EXTRACT_CID="$(docker create "$PINNED_REF")"
docker cp "$EXTRACT_CID:/app/bootstrap/admins.db" "$STAGING_DIR/admins.db"
docker rm "$EXTRACT_CID" >/dev/null
EXTRACT_CID=""

# Проверить, что image действительно содержит корректную SQLite.
python3 - "$STAGING_DIR/admins.db" <<'PY'
import sqlite3
import sys

uri = "file:" + sys.argv[1] + "?mode=ro"
with sqlite3.connect(uri, uri=True) as con:
    result = con.execute("PRAGMA quick_check").fetchone()[0]
if result != "ok":
    raise SystemExit(f"Invalid bootstrap SQLite: {result}")
PY

# Сначала подготовим replacement, затем атомарно переименуем.
# Предполагается, что этой БД пользуется только остановленный backend.
cp "$STAGING_DIR/admins.db" "$DB_DIR/.admins.db.next"
# С этого момента rollback должен вернуть backup даже при ошибке
# удаления sidecar-файлов или переименования.
DB_REPLACED=1
rm -f "$DB_FILE-wal" "$DB_FILE-shm" "$DB_FILE-journal"
mv -f "$DB_DIR/.admins.db.next" "$DB_FILE"

# release.env меняется только после подготовки базы.
printf 'BACKEND_IMAGE=%s\n' "$PINNED_REF" > "$APP_DIR/.release.next"
mv -f "$APP_DIR/.release.next" "$RELEASE_FILE"

compose_up
check_health || {
    echo "Backend failed health check: $HEALTH_URL" >&2
    exit 1
}

ROLLBACK_REQUIRED=0
echo "Deployment successful: $PINNED_REF"
```

Установите файл и права:

```bash
sudo chmod 0755 /usr/local/sbin/simple-tickets-update.sh
```

**Ограничения этого test-script:**

- Расчёт на **один backend-контейнер и одного владельца SQLite**. Нельзя одновременно иметь второй процесс, пишущий в эту же БД. Особенно важно для SQLite WAL.
- `PRAGMA quick_check` проверяет целостность файла, **но не совместимость схемы с кодом**. `/health` в текущем Simple Tickets возвращает статический `{"status":"ok"}` и тоже **не проверяет БД**. Для более строгого deployment позднее добавьте проверку соединения/схемы или функциональный smoke-test.
- При внезапном отключении питания / `SIGKILL` shell trap не сработает. Поэтому остаются backup-файлы, а ручной recovery должен быть предусмотрен.
- При регулярном `--restart unless-stopped` Docker не должен автоматически запускать backend посреди замены БД. Скрипт предварительно останавливает существующий контейнер; не запускайте одновременно другой supervisor/deploy-process для того же backend.
- `docker pull` проверяет Registry; если сеть или Registry недоступны, работающий контейнер не затрагивается, а systemd попробует снова на следующем запуске.

## 14. systemd timer на application-server

`/etc/systemd/system/simple-tickets-update.service`:

```ini
[Unit]
Description=Check Registry and deploy Simple Tickets backend
Wants=network-online.target
After=network-online.target docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/simple-tickets-update.sh
```

`/etc/systemd/system/simple-tickets-update.timer`:

```ini
[Unit]
Description=Poll Registry for a new Simple Tickets image

[Timer]
OnBootSec=1min
OnUnitInactiveSec=1min
AccuracySec=10s
Unit=simple-tickets-update.service

[Install]
WantedBy=timers.target
```

Включение:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now simple-tickets-update.timer
```

Ручная проверка:

```bash
sudo systemctl start simple-tickets-update.service
journalctl -u simple-tickets-update.service -n 100 --no-pager
```

Отключить автоматические обновления (текущий контейнер продолжит работать):

```bash
sudo systemctl disable --now simple-tickets-update.timer
```

**Почему app-server именно опрашивает Registry?** Он не знает о GitHub и builder. Сегодня следит за `registry.example.lan:5000/simple-tickets-backend:test`, завтра может следить за другим Registry и именем image. Система сборки не должна иметь SSH-доступ к application-server.

---

# Часть V. Проверки, откат, эксплуатация

## 15. Первая установка

1. На build-server вручную проверьте `docker build`/`docker push` и наличие `:test`.
2. На application-server проверьте DNS/TLS/логин, затем вручную `docker pull ...:test`.
3. Создайте `runtime.env`, `compose.yml`, каталоги `db`/`backups`.
4. Если уже существует контейнер `simple-tickets-backend`, созданный через `docker run`, **предварительно остановите и удалите этот контейнер** (не удаляя bind-mounted каталог с БД). Иначе Compose столкнётся с совпадающим именем.
5. Выполните `/usr/local/sbin/simple-tickets-update.sh` вручную. При первой установке скрипт создаст `release.env`, получит bootstrap DB и запустит Compose.
6. Убедитесь, что `curl http://127.0.0.1:8080/health` возвращает `{"status":"ok"}`. Затем настройте timer.

## 16. Диагностика

```bash
# Application server: какие контейнеры работают?
docker ps

# Текущий запущенный image ID:
docker inspect simple-tickets-backend --format '{{.Image}}'

# Какой точный image закреплён в Compose:
cat /srv/simple-tickets/release.env

# Логи backend:
docker logs --tail 100 simple-tickets-backend

# Логи проверки Registry/deployment:
journalctl -u simple-tickets-update.service -n 100 --no-pager

# Проверка health:
curl -fsS http://127.0.0.1:8080/health

# Список backup:
ls -lh /srv/simple-tickets/backups/
```

## 17. Откат

Скрипт автоматически **пытается** вернуть прежнюю БД и прежний image, если новый backend не прошёл `/health` или deployment оборвался обычной ошибкой после остановки старого контейнера.

Для **ручного отката**:

1. Отключите timer обновлений, иначе он снова установит текущий `:test`.
2. Выберите прежний digest из истории `release.env`/логов или нужный commit-tag из Registry.
3. Остановите backend.
4. Восстановите соответствующий backup SQLite (при необходимости — сначала скопировав его в рабочий каталог; после остановки удалите старые `admins.db-wal`/`-shm`/`-journal`).
5. Запишите в `/srv/simple-tickets/release.env` точную ссылку на старый image.
6. Запустите:

```bash
cd /srv/simple-tickets
sudo docker compose --env-file release.env -f compose.yml up -d --pull never --force-recreate backend
curl -fsS http://127.0.0.1:8080/health
```

Для каждого rollback важно подбирать **парную комбинацию backend image + DB backup соответствующего релиза**. Простое переключение тега без восстановления базы может дать несовместимую схему.

## 18. Безопасность и эксплуатационные замечания

- **Не хранить рабочие секреты и настоящие пользовательские данные** в `db/admins.db` внутри публичного GitHub или даже приватного Registry без отдельной оценки рисков. `SECRET_KEY` всегда задаётся на целевом сервере.
- Docker Registry с сетевым доступом желательно использовать через **TLS + аутентификацию + firewall/VPN**.
- У `:test` нет гарантии неизменности. Поэтому после обнаружения обновления приложение запускается по **digest**.
- Не делайте автоматическое `docker image prune -a` без продуманной политики хранения старых images; backup DB и старые digests нужны для отката.
- Копии БД сохраняются **только локально** на application-server. Для защиты от повреждения/утраты самого сервера позже стоит копировать их на другое хранилище.
- Если тестовая SQLite содержит refresh-токены, а приложение использует `TokenStorageMemory`, после замены image пользовательские сессии могут обрываться. Для тестовой стадии это допустимо.
- Синхронный `Dockerfile` и код репозитория должны поддерживать `src.web.main:app`, `utils/`, `requirements.txt`; текущий backend уже используется именно с такой структурой.
- Build script ниже намеренно **не объявляет тесты обязательными**, пока мы не выбрали конкретную команду и окружение для `pytest`. Перед использованием вне тестового стенда это нужно исправить.

## 19. Порядок внедрения

| Этап | Что проверить | Критерий готовности |
|---|---|---|
| 1 | Backend Dockerfile с bootstrap SQLite | Image собирается, `/app/bootstrap/admins.db` существует |
| 2 | Local Registry | `docker push` с build-server, `docker pull` с app-server |
| 3 | Build polling GitHub | Push в `test-deploy` публикует `:<SHA>` и `:test` |
| 4 | Ручной deployment | Image скачан, DB восстановлена из image, `/health` отвечает |
| 5 | Application polling | После публикации нового `:test` backend обновляется без SSH с builder |
| 6 | Rollback/авария | Проверен ручной откат image **и** SQLite |
| 7 | Автономная работа | Оба systemd timer включены, логи доступны |

## 20. Что можно будет заменить впоследствии

```text
Сегодня                         Завтра
----------------------------    ------------------------------
GitHub                          другой Git provider
systemd + build script          Jenkins/GitLab CI/GitHub Actions
Локальный Registry              любой OCI-compatible Registry
SQLite snapshot в image         миграции и отдельная persistent DB
Application polling + Compose   другой rollout-агент/оркестратор
```

**Инвариант архитектуры:** построение артефакта и его запуск не связаны прямым управляющим каналом. Builder **публикует**, application-server **обнаруживает и забирает**.

---

## Ссылки на документацию

- Docker / CNCF Distribution — Deployment Registry: https://distribution.github.io/distribution/about/deploying/
- Docker Compose, подстановка переменных: https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/
- Docker Compose `up`: https://docs.docker.com/reference/cli/docker/compose/up/
- Docker pull и фиксация digest: https://docs.docker.com/reference/cli/docker/image/pull/
- systemd timer: https://www.man7.org/linux/man-pages/man5/systemd.timer.5.html
