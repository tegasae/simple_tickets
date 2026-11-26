# Независимое первичное заключение QA Python/FastAPI — раунд 01

Дата: 2026-11-23. Роль: инженер QA Python/FastAPI. Другие экспертные заключения и старые отчёты не читались.

## Вход и метод

- Репозиторий: tegasae/simple_tickets, ветка api-new-client-scheme.
- Коммит: **bbf7a392dafe0fede2d5d017af36281b6f4f40a2**.
- Единый пакет: `/workspace/work/input-bbf7a39`.
- Манифест: `/workspace/work/manifest-bbf7a39.json`, SHA256 фактически проверен: `8ad0911db59c2828a58f8e215d2ef0da291117ad20be52647d424573472e267d`.
- Прочитаны `readme.md`, `OWNER-NOTES.md`, протокол `docs/notes/simple_tickets_testing_protocol_acceptance.md`, схема SQLite, реальные web/application/domain/adapters для рассмотренных сценариев. TODO в README не трактовался как доказательство отсутствия реализации. При конфликте старых заметок с OWNER-NOTES использованы актуальные требования владельца.
- Python 3.12.14, FastAPI 0.143.0, Pydantic 2.14.1, httpx 0.28.1. `httpx` уже установлен, дополнительно устанавливать его не потребовалось.
- Прогоны через **реальный `src.web.main:app` и TestClient**, без подмены зависимостей авторизации/репозиториев. SQLite создана в `/tmp` из поставляемого `db/schema.sql`; начальная синтетическая запись администратора и роли заведены локально, дальше использованы реальные HTTP login и команды. `.env` и реальные БД не открывались; импорт приложения выполнялся с cwd `/tmp` и явными синтетическими настройками.
- Исходные файлы не исправлялись. Синтетические сценарии: `/tmp/qa-bbf7a39.py`, `/tmp/test_qa_bbf7a39.py`; результаты: `/tmp/qa-bbf7a39-results.jsonl`, `/tmp/qa-bbf7a39-pytest.txt`. Артефакты в `/tmp` содержат только синтетику и не предназначены для постоянного хранения.

Итог целевой матрицы: **16 проверок: 12 failed, 4 passed**. Падающие проверки требуют ожидаемого корректного поведения и воспроизводят четыре причины ниже; это не 12 отдельных дефектов. Все HTTP 500 получены с `raise_server_exceptions=False`, то есть проверен внешний ответ, а не только Python-исключение.

Команда повторения:

```text
PYTHONDONTWRITEBYTECODE=1 /tmp/tickets-bbf7a39-venv/bin/python -m pytest -q -p no:cacheprovider /tmp/test_qa_bbf7a39.py
```

## Подтверждённые дефекты

### QA-01. Назначение User-ролей при создании обходит отдельное право role_user.assign

**Приоритет: P1. Уверенность: высокая; HTTP-воспроизведение и точный путь в коде.**

Условия: действующий Admin с единственным правом `user.operation`, без `role_user.assign`; существует Client и User-роль с правами, например `ticket.view.all` / `ticket.operation.all`.

Путь:

1. `POST /admin/users/` → `src/web/routers/admin/users.py:76–87`.
2. `UserApplicationService.create_user`, `src/application/services/user_service.py:75–78`, требует только `USER_OPERATION`.
3. Если тело содержит непустой `roles`, на `src/application/services/user_service.py:100–116` вызывается `RoleManager.grant_roles` с **`required_permission=AdminPermission.USER_OPERATION`**, а не `ROLE_USER_ASSIGN`.
4. `src/domain/rbac/role.py:59–63` проверяет переданное право и назначает роли.

Наблюдение: такой Admin создал User с ролью, дающей все User-права: HTTP **201**, поле `roles` содержит переданный id, связь сохранена. При этом отдельный `POST /admin/users/{id}/roles` с тем же Admin возвращает **403**, поскольку `src/application/services/user_service.py:324–326,344–352` правильно требует `ROLE_USER_ASSIGN`.

Последствия: отдельная граница управления User-ролями обходится через создание новой учётной записи. Администратор с правом только на операции с User может создать подконтрольного User с правами на все заявки организации. Наличие `ROLE_USER_ASSIGN` и отличающееся поведение специальной команды дают основание считать это ошибкой, а не просто предложением ужесточить политику.

Исправление: для непустого `roles` требовать `ROLE_USER_ASSIGN` до сохранения пользователя и применять это же право в RoleManager. Создание без ролей должно остаться доступным через `USER_OPERATION`.

Конкретная регрессия: `test_create_user_with_roles_needs_role_user_assign`. Сначала подтвердить 403 на отдельном назначении, затем POST создания с `roles` тем же actor должен дать 403; количество `employees/users/users_roles` не увеличивается. Дополнить успешным созданием без ролей и успешным созданием с ролями при наличии обоих прав.

### QA-02. Отзыв User-роли ошибочно требует ещё и право управления Admin-ролями

**Приоритет: P2. Уверенность: высокая; HTTP-воспроизведение и прямое расхождение констант.**

Условия: действующий Admin имеет `role_user.assign`, не имеет `role.assign`. Целевой User и его User-роль существуют.

Путь: `DELETE /admin/users/{employee_id}/roles` → `src/web/routers/admin/users.py:330–345` → `UserApplicationService.revoke_role`, `src/application/services/user_service.py:363–389`.

На строках **369–372** проверяется правильное `ROLE_USER_ASSIGN`, но повторная проверка RoleManager на строках **380–388** получает **`AdminPermission.ROLE_ASSIGN`**. В результате выдать роль тот же actor может, а отозвать — нет.

Наблюдение: `POST /admin/users/{id}/roles` с таким actor → **200**; `DELETE` с тем же телом `{"roles":[<user_role_id>]}` → **403**, `Subject lacks permission: role.assign`. Роль остаётся назначенной.

Последствия: оператор User-ролей не может снимать разрешения; для штатного отзыва ему приходится выдавать несвязанное право управления ролями администраторов.

Исправление: передавать `ROLE_USER_ASSIGN` и во вторую проверку. Сохранять заявленную в коде возможность отзыва при отключённом Client.

Конкретная регрессия: `test_revoke_user_role_needs_only_role_user_assign`: actor только с `role_user.assign` успешно отзывает User-роль (200, связь удалена); actor без этого права получает 403. Право `role.assign` для успеха не добавляется. Отдельно проверить отключённый Client.

### QA-03. Некорректные значения пароля, логина, permission и description проходят web-модель и дают HTTP 500

**Приоритет: P2. Уверенность: высокая; шесть фактически исполненных HTTP-вариантов.**

Общая причина: часть web-полей объявлена просто `str`/`list[str]`, а соответствующая доменная проверка поднимает обычный `ValueError`, который не преобразуется в ожидаемую ошибку входа. В `src/web/main.py:68–92` есть обработчик `ItemValidationError:400`, но `ValueError` попадает в catch-all и возвращает `{"detail":"Internal server error"}`.

Подтверждённые варианты:

| Реальный вход API | Условия/тело | Путь к источнику исключения | Факт |
|---|---|---|---|
| `PATCH /admin/admins/{id}/password` | Admin с `admin.operation`, целевой Admin с Account; `password` длины 1 | router `src/web/routers/admin/admins.py:331–350` → application `src/application/services/admin_service.py:271–296` → `src/domain/employee.py:199–201` → `src/domain/account.py:85–89` → `src/domain/value_objects.py:422–425` | 500 |
| `PATCH /admin/users/{id}/password` | Admin с `user.operation`, активные User/Client, Account; тот же короткий пароль | `src/web/routers/admin/users.py:288–305` → `src/application/services/user_service.py:280–312` → тот же `Password.from_plain` | 500 |
| `POST /admin/admins/{id}/account` | Свободный login с внутренним пробелом, валидный синтетический пароль | `src/application/services/admin_service.py:181–209` → `src/domain/employee.py:167–179` → `Account.create` → `src/domain/value_objects.py:336–337` | 500 |
| `POST /admin/roles/admin` | Actor с `role.assign`; `name` валиден, `permissions:["unknown.permission"]` | `src/web/routers/admin/roles.py:87–101` → application role service → `src/domain/services/role_service.py:21–23` (`map(AdminPermission, permissions)`) | 500 |
| `PATCH /admin/tickets/{id}/description` | Actor с `ticket.operation`, открытая заявка, description длины 4001 | `src/web/models/tickets.py:88–91` → application/domain service → `src/domain/ticket.py:484–490` → `src/domain/value_objects.py:237–238` | 500 |
| `PATCH /user/tickets/{id}/description` | Автор с `ticket.operation`, открытая собственная заявка, description длины 4001 | `src/web/models/tikcets_user.py:45–46` → `src/application/services/ticket_user_service.py:235–263` → domain service → `src/domain/ticket_user.py:223` → тот же Description | 500 |

Последствия: обычная ошибка формы выглядит как отказ сервера, клиент не получает корректную причину исправления и может выполнять ненужные повторы. Это не доказательство повреждения данных: во всех приведённых ветках ожидается отказ до сохранения; отдельная регрессия должна закрепить отсутствие изменений.

Исправление: типизировать permissions соответствующим enum на web-границе; для строк применить общие ограничения, согласованные с value objects. В доменных командах преобразовывать ожидаемый `ValueError` валидаторов в `ItemValidationError`/специализированную ошибку входа. Не добавлять глобальный обработчик всех `ValueError` как 400: это скроет настоящие программные ошибки.

Конкретная регрессия: шесть параметров `test_bad_input_is_4xx` в синтетическом тесте. Для каждого требуется согласованный 400/422 с понятной ошибкой поля, отсутствие записи/изменения, успешная операция на границе валидности (пароль достаточной длины, существующий enum permission, description ровно 4000). Проверить User-вариант создания роли с неизвестным permission: `src/domain/services/role_service.py:41–43` имеет тот же механизм, но этот дополнительный вариант в первичном раунде отдельно не выполнялся.

### QA-04. Ожидаемые ApplicationValidateError не зарегистрированы и также возвращаются как 500

**Приоритет: P2. Уверенность: высокая; четыре фактически исполненных HTTP-варианта.**

`ApplicationValidateError` наследуется от `ApplicationError(Exception)`, `src/application/exceptions.py:11–24`. В `src/web/main.py:68–81` зарегистрирован только его подкласс `TicketInputValidationError`; базовый `ApplicationValidateError` отсутствует. Поэтому намеренные отказы вне TicketDTO обрабатываются catch-all на строках 88–92.

Подтверждённые внешние входы:

- `PATCH /admin/admins/{own_id}/disable` с `admin.operation`: намеренный запрет self-disable на `src/application/services/admin_service.py:420–421` → **500**.
- `DELETE /admin/roles/admin/{system_role_id}` с `role.assign`: запрет удаления системной роли на `src/application/services/role_service.py:98–100` → **500**.
- `GET /admin/clients/-1` с `client.view`: `ClientDTO.__post_init__`, `src/application/dto/client_dto.py:22–23` → **500**.
- `GET /admin/roles/admin/-1` с `role.assign`: `RoleDTO.__post_init__`, `src/application/dto/roles_dto.py:19–21` → **500**.

Последствия: сервер сообщает внутренний сбой для нормального запрета/ошибки параметра. Логика запрета срабатывает; сам self-disable или удаление системной роли не выполняются. Также по коду затронуты self-detach/self-disable-account (`src/application/services/admin_service.py:222–223,261–262`) и удаление назначенной роли (`src/application/services/role_service.py:103–105`); эти дополнительные ветки отдельно не прогонялись.

Исправление: добавить явное сопоставление `ApplicationValidateError` с клиентским статусом, проверить выбранную семантику 400/409 для конфликтов; положительные path-id по возможности отсеивать `Path(gt=0)` с 422. Не преобразовывать все ApplicationError или ошибки хранилища в 400.

Конкретная регрессия: четыре параметра `test_expected_application_rejection_is_4xx`; ожидается согласованный 4xx, понятная причина, неизменность Admin/роли, отсутствие traceback и внутренних деталей. Для контроля существует уже работающий аналог: `GET /admin/departments/-1` → **422**.

## Что проверено и не объявляется дефектом

1. Действительные Admin/User login, создание внутреннего Ticket и пользовательской пары TicketUser/Ticket работают. Данные отвечают заявленным response-моделям.
2. Полный путь через HTTP: User создаёт заявку → Admin задаёт отдел, принимает, назначает себя, начинает, приостанавливает, возобновляет, завершает работу → Ticket **READY_FOR_REVIEW**, TicketUser **WAITING_FOR_CONFIRMATION**, оба открыты → User подтверждает → обе карточки закрыты с **CONFIRMED_BY_USER**. `finish-work` **не** переводит автоматически в EXECUTED — это соответствует OWNER-NOTES.
3. При отключении владельца в READY_FOR_REVIEW обе карточки переходят в финальный SUSPENDED; попытка `accept` внутренней карточки возвращает 400. User с прежним JWT после отключения получает 401. Это соответствует OWNER-NOTES, восстановление не предлагается.
4. При отключении Client у заявки AT_WORK работа сохраняется; прежний User JWT больше не допускается, Admin может выполнить finish-work до READY_FOR_REVIEW. Это соответствует указанному владельцем продолжению активной работы.
5. User-token не допускается на admin-router, Admin-token — на user-router; без токена закрытые маршруты возвращают 401. В этих проверках подпись/тип токена проверяются реальным dependency, не подменой.

В данных проверках не обнаружен отказ в базовой сериализации, маршрутизации статических путей или указанной синхронизации статусов. Это ограниченная подтверждённая матрица, а не утверждение о покрытии всего API.

## Существенный QA-риск и необходимые проверки

**Риск QA-R1, P2: в переданном пакете нет исполняемого автоматического тестового набора.** `pytest.ini` указывает `testpaths=tests`, `requirements-test.txt` перечисляет зависимости, но файлов `test_*.py`, `*_test.py`, `conftest.py` не обнаружено. OWNER-NOTES прямо сообщает об удалении устаревших тестов: не считаю сам факт удаления нарушением требования. Практическое следствие — текущие RBAC/HTTP-регрессии не защищены от повторного появления. Ручной протокол ориентирован на штатные операции и не заменяет проверки прав/ошибочного ввода.

Минимально перенести в постоянный набор: регрессии QA-01–04; успешный workflow и OWNER-NOTES-сценарии выше; матрицу own/other User × same/other Client × VIEW/VIEW_ALL/OPERATION/OPERATION_ALL; отключение Account/User/Client между login и последующим запросом; refresh/logout для memory и sqlite, включая restart/rotation/replay и разделение admin/user realm; откат пары Ticket/TicketUser при сбое второго сохранения. Конкурентные сценарии с независимыми соединениями должны проверять конфликт и атомарность, а не только последовательный вызов одного UOW. Последние группы перечислены как нужное покрытие, а не как уже подтверждённые ошибки.

Рекомендую сначала устранить QA-01 и QA-02, затем согласованно закрыть две независимые причины 500 (QA-03 и QA-04) и закрепить их HTTP-регрессиями. В этом раунде исходники не менялись, полнота PostgreSQL-поведения и конкурентного исполнения не утверждается.
