#!/usr/bin/env bash
set -euo pipefail

REPO="https://tegasae@github.com:tegasae/simple_tickets.git"
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