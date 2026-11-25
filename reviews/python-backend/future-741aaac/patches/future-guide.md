# Именованные проверки доступа и обработка ошибок GET

Патчи подготовлены для ветки `api-new-client-scheme` на снимке `741aaac6221f07669332d0106b6b6c6db02b6cbc`. Ветка содержит файлы патчей и это руководство. Применение к исходникам выполняется отдельно. [Базовый коммит](https://github.com/tegasae/simple_tickets/commit/741aaac6221f07669332d0106b6b6c6db02b6cbc)

| Патч | Изменение |
| --- | --- |
| [future-name-application-access-checks.patch](future-name-application-access-checks.patch) | Даёт бизнес-имена трём проверкам в `UserApplicationService` и `TicketUserApplicationService`. Существующие адаптеры создания обращаются к ним через совместимый метод. |
| [future-remove-redundant-get-exception-handlers.patch](future-remove-redundant-get-exception-handlers.patch) | Удаляет повторный перехват исключений в пяти пользовательских GET заявок. |

Патчи независимы друг от друга. Оба проверены отдельно от серии `01-create-response-operation.patch` и `02-test-comment-replay.patch`, а также вместе с ней. В обеих очередностях получились одинаковые файлы исходников и тестов. Для этой серии обновление схемы SQLite не требуется.

## Именованные проверки

| Метод | Где выполняется | Условие допуска |
| --- | --- | --- |
| `UserApplicationService.require_create_user(user_dto)` | При создании пользователя и выдаче сохранённого результата повторного запроса | Администратор обладает `USER_OPERATION`. Непустой список ролей в запросе дополнительно требует `ROLE_USER_ASSIGN`. |
| `TicketUserApplicationService.require_create_ticket(ticket_user_dto)` | При пользовательском создании заявки и выдаче сохранённого результата повторного запроса | Пользователь обладает `TICKET_OPERATION`. |
| `TicketUserApplicationService.require_view_ticket(actor_user_id=..., ticket_user=...)` | В сервисе чтения одной пользовательской заявки | Владелец обладает `TICKET_VIEW` или `TICKET_VIEW_ALL`. Другой пользователь обладает `TICKET_VIEW_ALL`. Актор и заявка принадлежат одному клиенту. |

В обоих сервисах `require_create_access` делегирует проверку именованному методу. Поэтому обычные маршруты и адаптеры `CreationOperation` из серии `01/02` используют одну и ту же политику. Новый запрос проверяет полномочия внутри бизнес-транзакции. При повторе проверяются актуальные полномочия перед сравнением отпечатка и выдачей сохранённого ответа. Отказ в новом запросе откатывает резервирование ключа. Отказ при повторе сохраняет ранее записанный результат.

При чтении одной заявки сервис сначала загружает объект, затем вызывает `require_view_ticket`. Правила формирования списков остаются в соответствующих методах сервиса. Например, `/open` выбирает свои открытые заявки при `TICKET_VIEW` или открытые заявки своего клиента при `TICKET_VIEW_ALL`. [Создание пользователя](https://github.com/tegasae/simple_tickets/blob/f556802/src/application/services/user_service.py#L129-L140) · [Чтение заявки](https://github.com/tegasae/simple_tickets/blob/f556802/src/application/services/ticket_user_service.py#L438-L455) · [Выборка открытых](https://github.com/tegasae/simple_tickets/blob/f556802/src/application/services/ticket_user_service.py#L546-L583)

## Ошибки в пользовательских GET

| Маршрут | Успешный ответ |
| --- | --- |
| `GET /user/tickets/` | `200`, список своих заявок |
| `GET /user/tickets/all` | `200`, список заявок клиента при `TICKET_VIEW_ALL` |
| `GET /user/tickets/open` | `200`, доступные открытые заявки |
| `GET /user/tickets/closed` | `200`, доступные закрытые заявки |
| `GET /user/tickets/{ticket_user_id}` | `200`, карточка доступной заявки |

Декораторы маршрутов и модели ответа сохранены. До патча локальный `except` вызывал `_domain_error(exc)`, а эта функция сразу выполняла `raise exc`. После удаления блока то же исключение поступает в зарегистрированный `ExceptionHandlerRegistry` по обычному пути FastAPI. Для пяти GET сохранены порядок проверок, HTTP-статусы и JSON. Вызовы `_domain_error` в изменяющих маршрутах остаются на своих местах. [Пользовательские маршруты](https://github.com/tegasae/simple_tickets/blob/f556802/src/web/routers/user/tickets.py#L153-L298) · [Общий обработчик](https://github.com/tegasae/simple_tickets/blob/f556802/src/web/main.py#L52-L93)

Например, тело обработчика чтения по ID сводится к прежним трём шагам.

```python
dto = TicketUserDTO(
    actor_user_id=user_id,
    ticket_user_id=ticket_user_id,
)
response_dto = service.get_by_id(ticket_user_dto=dto)
return TicketUserResponse.from_dto(response_dto)
```

Преобразование DTO и списков уже выполняет `BaseResponse`, сериализацию HTTP выполняет FastAPI. Упрощение пяти GET поэтому состоит в удалении повторного перехвата. У `create_response` остаётся своя работа по идемпотентному созданию. [BaseResponse](https://github.com/tegasae/simple_tickets/blob/f556802/src/web/models/base_response.py#L6-L16) · [Идемпотентность](https://github.com/tegasae/simple_tickets/blob/f556802/src/web/idempotency.py#L112-L155)

## Как проверить патчи в чистой копии

Команды запускаются из корня клона `tegasae/simple_tickets`. Временная копия получает Python-исходники, тесты и схему. Для тестов используются временные базы и синтетические данные.

```bash
set -euo pipefail
git fetch origin api-new-client-scheme
published=$(git rev-parse FETCH_HEAD)
base=741aaac6221f07669332d0106b6b6c6db02b6cbc
patch_dir=reviews/python-backend/future-741aaac/patches
scratch=$(mktemp -d)
mkdir -p "$scratch/source" "$scratch/patches"

git archive "$base" src utils db/schema.sql tests scripts/migrate_backend_storage.py \
    main.py pytest.ini requirements.txt requirements-test.txt |
    tar -x -C "$scratch/source"

for file in future-name-application-access-checks.patch \
    future-remove-redundant-get-exception-handlers.patch; do
    git show "$published:$patch_dir/$file" > "$scratch/patches/$file"
done

(
    cd "$scratch/source"
    git apply --check --whitespace=error-all "$scratch"/patches/future-*.patch
    git apply --whitespace=error-all "$scratch"/patches/future-*.patch
    python3.12 -m venv "$scratch/venv"
    "$scratch/venv/bin/python" -m pip install -r requirements.txt -r requirements-test.txt
    "$scratch/venv/bin/python" main.py -o addopts='' -p no:cacheprovider -q tests
)
```

Для проверки с серией `01/02` можно добавить её к этой же копии. Команды выполняются в исходном клоне после предыдущего блока, в той же Bash-сессии.

```bash
previous=reviews/python-backend/creation-operation-f556802/patches
for file in 01-create-response-operation.patch 02-test-comment-replay.patch; do
    git show "$base:$previous/$file" > "$scratch/patches/$file"
done

(
    cd "$scratch/source"
    git apply --check --whitespace=error-all \
        "$scratch/patches/01-create-response-operation.patch" \
        "$scratch/patches/02-test-comment-replay.patch"
    git apply --whitespace=error-all \
        "$scratch/patches/01-create-response-operation.patch" \
        "$scratch/patches/02-test-comment-replay.patch"
    "$scratch/venv/bin/python" main.py -o addopts='' -p no:cacheprovider -q tests
)
```

## HTTP-проверки

Для ручной проверки используйте отдельную тестовую БД. Подготовьте пользователя с открытой и закрытой заявками. Для подготовки выдайте пользователю `TICKET_OPERATION`. Создайте две заявки через `POST /user/tickets/` с разными текстами в `{"text_of_ticket": "Тестовая заявка"}`. Одну отмените через `PATCH /user/tickets/{id}/cancel` с телом `{"comment": "Закрытие для проверки"}`. Дайте пользователю `TICKET_VIEW_ALL` на своём клиенте. Повторяйте запросы с тем же действующим JWT, меняя роли через административные маршруты.

| Действие | Ожидаемый результат |
| --- | --- |
| Вызвать все пять GET с действующей ролью | `200`. `/open` содержит открытую, `/closed` закрытую заявку. Детали совпадают с сохранённой карточкой. |
| Вызвать каждый GET без заголовка Authorization | `401` и `WWW-Authenticate: Bearer`. |
| Передать несуществующий положительный ID, строку вместо ID или ID `0` | Соответственно `404`, `422` и `400`. |
| Отозвать право просмотра и запросить те же существующие заявки тем же JWT | Все пять GET дают `403`. Детали отсутствующей заявки по-прежнему дают `404`. |
| Перейти с `TICKET_VIEW` на `TICKET_VIEW_ALL` и вызвать `/open` | Сначала свои заявки, затем доступные заявки всего клиента. Заявки другого клиента отсутствуют. |
| Отправить `Idempotency-Key` на GET | Статус и тело определяются текущими данными и правами. В `creation_results` записей от GET не появляется. |
| Вызвать `POST /admin/users/` с `USER_OPERATION` без `ROLE_USER_ASSIGN` | Тело без ролей даёт `201`. Тело с ролями даёт `403`, резерв ключа и запись пользователя не сохраняются. |
| Выдать `ROLE_USER_ASSIGN`, повторить создание с ролью, затем отозвать право | Прежний запрос с тем же ключом даёт `201`. Повтор при действующем праве возвращает сохранённый ответ. После отзыва права повтор даёт `403`. |

Для двух вариантов `POST /admin/users/` используйте разные ключи. Повторяйте запрос с ролями с тем ключом и телом, которые использовали при первой попытке назначения роли.

## Фактически выполнено

Проверка сделана на Python 3.12.14. Все HTTP-тесты использовали FastAPI TestClient и синтетическую SQLite.

- `git apply --check --whitespace=error-all` прошёл на `741aaac`. Патчи также проверены с серией `01/02` в обеих очередностях.
- Прогон с патчами `future` дал **23 успешных теста**. В него вошли штатные тесты и дополнительные проверки прав, чтения, повтора создания и границ UoW.
- Прогон с `future` и серией `01/02` дал **132 успешных теста**. В него вошли штатные тесты и дополнительные регрессии на создание с ключом и без него, повторы, нормализацию, конкурирующие записи и откат.
- Отдельная регрессия всех пяти GET прошла на каждом из трёх снимков. Проверены успешные ответы со списками и карточкой, статусы `401/403/404/400/422` и сохранение формы ошибок.
- Документы OpenAPI побайтно совпали после канонической сериализации на исходной версии, с `future` и с `future` вместе с `01/02`. `GET /health` вернул `200` во всех трёх копиях.
- Команды выше воспроизводят штатный набор из репозитория. Запуск через `python main.py` дал **18 успешных тестов** с `future` и **19 успешных тестов** с `future` и `01/02`. Дополнительные тесты выполнялись во временной копии по сценариям из таблицы и проверяли состояние SQLite после HTTP-вызовов.
