# Первичное независимое заключение ведущего Python-разработчика — раунд 01

## Вход и границы

- Репозиторий: `tegasae/simple_tickets`, ветка `api-new-client-scheme`.
- Код: `bbf7a392dafe0fede2d5d017af36281b6f4f40a2`.
- Единый входной пакет: `/workspace/work/input-bbf7a39`.
- SHA256 `/workspace/work/manifest-bbf7a39.json`: `8ad0911db59c2828a58f8e215d2ef0da291117ad20be52647d424573472e267d`; проверен командой `sha256sum`.
- Среда проверок: `/tmp/tickets-bbf7a39-venv/bin/python`, Python 3.12.14, FastAPI 0.143.0, зависимости текущего requirements, HTTP TestClient.
- Прочитаны `readme.md`, `OWNER-NOTES.md`, `rules.md`, документы по concurrency control, API, workflow, TicketUser, техническому долгу и принятию работы. Корневой README рассматриваю как TODO. При расхождении старой документации о восстановлении с OWNER-NOTES приоритет у OWNER-NOTES: SUSPENDED окончателен; finish-work оставляет READY_FOR_REVIEW; AT_WORK при отключении продолжается.
- Старые экспертизы и результаты других экспертов до сдачи этого текста не читались.
- Исходники не редактировались. Данные и сценарии только синтетические в `/tmp`; реальные БД, `.env`, реальные учётные данные не открывались. HTTP проверки проходили с настоящим login и сгенерированными локальными credentials, без отключения auth/RBAC. Значения токенов/паролей не приведены.
- Фокус: API → application → domain → UoW → SQLite, mapper, исключения, откат, повтор, конкуренция. Это первичная экспертиза, а не доказательство отсутствия любых других ошибок.

## Вывод

Подтверждены пять конкретных ошибок: потеря классификации SQLite-конфликта (HTTP 500), отсутствие обработки части ожидаемых application-ошибок, HTTP 500 на слишком длинное описание, неверная проверка назначения пользовательских ролей и неверная UTC-интерпретация времени новых сотрудников/отделов на хосте с ненулевым часовым поясом. Также подтверждены два неоднозначных поведения API/политики и установлен конкретный пробел concurrency-протокола для будущего PostgreSQL. Разделяю эти категории ниже.

Целостность обычной транзакции не следует объявлять сломанной: принудительный сбой после INSERT обоих связанных корней откатил корни, истории и версии guard-агрегатов; optimistic locking старой версии сработал. В воспроизведённой SQLite-конкуренции один запрос откатывается с 500, потери истории или частичного commit не обнаружено.

## Подтверждённые ошибки

### PY-01. Конкурентное изменение заявки выдаёт 500 вместо распознаваемого конфликта/повторяемой ошибки — P2

**Путь от API.** `PATCH /admin/tickets/{id}/description` → router `src/web/routers/admin/tickets.py:404–435` → `TicketApplicationService.update_description`, `src/application/services/ticket_service.py:255–282` → `Ticket.update_description`, `src/domain/ticket.py:484–490` → `_save_and_to_dto`, application `ticket_service.py:1177–1198` → `TicketRepositorySQLite.save`, `src/adapters/repositories/ticket_repository.py:311–325` → `_exec`, `src/adapters/repositories/base_repository.py:46–57` → `Query._execute`, `utils/db/query.py:17–27` → SQLite.

**Условие.** Две request-scoped UoW прочитали одну заявку до записи. Используются обычные `BEGIN TRANSACTION` (`utils/db/connect.py:46–59`) и разные подключения (`src/web/dependencies/services.py:22–32`). SQLite может отвергнуть повышение read-транзакции до write ещё до того, как `UPDATE ... WHERE version` сможет вернуть rowcount=0.

**Доказательство.** В синтетической БД по `db/schema.sql` синхронизировал два настоящих HTTP PATCH сразу после `_get_ticket` barrier-ом. Результат: один 200, второй 500 `{"detail":"Internal server error"}`. Зафиксированная причина второго: `PersistenceError ... database is locked`. Итоговое описание принадлежит успешному запросу. Auth, SQL, commit и rollback оставлены настоящими.

**Причина и последствия.** `Query` превращает все исключения драйвера в общий DBOperationError, `_exec` — в PersistenceError; sqlite error code теряется. `src/web/main.py:68–92` знает только OptimisticLockError→409 и общий Exception→500. Поэтому обычная конкуренция выглядит как поломка сервера; клиент не может отличить её от постоянной SQL-ошибки. Дополнительно `DepartmentRepositorySQLite.save`, `src/adapters/repositories/department_repository.py:58–86`, любую PersistenceError объявляет дублем имени: lock/I/O/иная ошибка там может стать ложным ItemAlreadyExistsError/409.

**Исправление.** Сохранить тип/код первопричины, различить integrity, busy/locked и неизвестную persistence-ошибку. Выбрать явный HTTP контракт для конкурентного отказа. При автоматическом повторе заново выполнять всю application-операцию в новой транзакции с повторным чтением/проверкой прав и бизнес-условий, а не повторять один SQL. В Department переводить в duplicate только нарушение конкретного unique constraint.

**Проверка после исправления.** Два подключения и barrier после чтения; assert одного commit, отсутствия частичных историй у отказавшего запроса и ожидаемого кода отказа. Отдельно конфликт имени отдела и заблокированная запись должны иметь разные классификации. Уверенность высокая; HTTP-сценарий воспроизведён несколько раз.

### PY-02. Ожидаемые ApplicationValidateError не зарегистрированы в HTTP обработчиках — P2

**Путь от API.** `PATCH /admin/admins/{own_id}/disable` → router `src/web/routers/admin/admins.py:340–359` → `AdminApplicationService.disable`, `src/application/services/admin_service.py:410–435` → self-disable guard на `:420–421` поднимает ApplicationValidateError → UoW откатывается → общий обработчик 500 (`src/web/main.py:68–92`). К domain и SQL изменениям этот отказ не доходит.

**Доказательство.** Синтетический активный admin с ADMIN_OPERATION отключает самого себя: HTTP 500 и общий Internal server error. Это штатная проверка входной операции, не внутренняя авария. ApplicationValidateError наследует ApplicationError, а не один из зарегистрированных DomainError (`src/application/exceptions.py:10–27`).

**Другие достижимые места.** Удаление системной/назначенной роли: `src/application/services/role_service.py:96–106`. Даже когда `is_assigned` возвращает правильно True, штатный отказ также попадёт в 500. Избирательно обработан только подкласс TicketInputValidationError.

**Исправление.** Обрабатывать ApplicationValidateError согласованным 400/409 либо заменить конкретные guards на уже обрабатываемые семантические исключения. Не регистрировать все ApplicationError как клиентские: ApplicationStoreError должен оставаться внутренней ошибкой.

**Проверка.** Self-disable, системная роль, назначенная admin-роль: ожидаемый 4xx, понятное публичное сообщение, неизменённые данные. Уверенность высокая; self-disable подтверждён HTTP.

### PY-03. Описание длиннее 4000 символов проходит web-валидацию и заканчивается HTTP 500 — P2

**Путь от API.** `PATCH /admin/tickets/{id}/description` → `TicketDescriptionRequest.description: str` без длины (`src/web/models/tickets.py:88–91`) → application `src/application/services/ticket_service.py:265–280` → domain facade `src/domain/services/ticket_service.py:151–152` → `Ticket.update_description`, `src/domain/ticket.py:484–490` → `Description`, `src/domain/value_objects.py:218–240` → обычный ValueError, который `src/web/main.py:68–92` не классифицирует как валидационный.

**Доказательство.** Для существующей редактируемой заявки `description='x' * 4001` вернул 500 `Internal server error`. Транзакция откатилась. Это воспроизводится при правильной аутентификации и достаточных правах. Та же конструкция Description используется при создании Ticket/TicketUser и редактировании TicketUser; эти пути требуют такой же проверки.

**Последствия.** Некорректный пользовательский ввод отображается как серверная авария; лимит не виден из request schema.

**Исправление.** Общий тип DescriptionText с нормализацией/верхней границей в web-схемах; доменный вход должен переводить ошибки VO в ItemValidationError или другое точное семантическое исключение. Глобальный перехват всех ValueError как 400 опасен: им можно скрыть дефекты программирования.

**Проверка.** 4000/4001 символ, пробельная нормализация, create/update для обеих карточек, сохранение прежнего описания после отказа. Уверенность высокая; HTTP PATCH подтверждён.

### PY-04. SQL is_assigned игнорирует users_roles — P2

**Путь от API.** `DELETE /admin/roles/user/{role_id}` → `src/web/routers/admin/roles.py:229–246` → `RoleApplicationService.delete_role`, `src/application/services/role_service.py:84–108` → `RoleRepositorySQLite.is_assigned`, `src/adapters/repositories/role_repository.py:89–95` → `RoleGateway.EXIST`, `src/adapters/repositories/gateways/role_gateway.py:32–44` → `_exists/_get_one`, `base_repository.py:28–35,59–70` → Query.fetchone.

**Причина.** SQL объединяет два scalar COUNT посредством UNION ALL и применяет LIMIT 1. Первая строка всегда существует: это count из admins_roles, в том числе нулевой. Строка count из users_roles никогда не используется.

**Доказательство.** Создана отдельная пользовательская роль и назначена только синтетическому User. `uow.roles_user.is_assigned(role_id)` вернул False. HTTP DELETE попытался удалить роль и вернул 500. Внешний ключ `db/schema.sql:68–73` с ON DELETE RESTRICT сохранил назначенную роль; потери роли не утверждаю. Удаление доходит до `RoleRepositorySQLite.delete :83–87`, который заворачивает FK error в DBOperationError.

**Исправление.** Одна проверка EXISTS двух наборов (или объединённый набор строк назначений), без LIMIT поверх двух отдельных COUNT. Ожидаемый отказ удаления назначенной роли затем должен корректно отображаться по PY-02. Не снимать FK.

**Проверка.** 0 назначений, только admin, только user, оба набора. Для назначенных ролей assert отказа до DELETE, сохранности роли/связей и нормального 4xx. Уверенность высокая; SQL-предикат и HTTP подтверждены.

### PY-05. Новые Department/Admin/User/Account используют local naive datetime, который mapper объявляет UTC — P2

**Путь от API для проверенного примера.** `POST /admin/departments/` → `src/web/routers/admin/departments.py:44–63` → `DepartmentApplicationService.create_department`, `src/application/services/department_service.py:59–77` → `Department.create`, `src/domain/department.py:27,32–46` (`datetime.now`, без timezone) → `DepartmentMapper.params`, `src/adapters/repositories/mappers/department_mapper.py:29–35` (naive isoformat) → SQLite; затем `GET /admin/departments/{id}` → mapper `:17–23` → `datetime_from_db`, `src/domain/datetime_check.py:86–89`, который делает replace(tzinfo=UTC).

**Доказательство.** На наблюдаемом хосте local timezone MSK/UTC+03. API create вернул `2026-11-23T22:32:20.967405` без offset; следующий GET вернул `2026-11-23T22:32:20.967405Z`. Реальное UTC было примерно 19:32:20. Смещение после roundtrip — 10800 секунд. Пример целиком через HTTP, без подмены часов.

**Аналогичные места.** `src/domain/employee.py:23,97`, `src/domain/account.py:30,76` создают naive local datetime; `AdminMapper.employee_params/account_params`, `src/adapters/repositories/mappers/admin_mapper.py:80,109`, и `UserMapper`, `src/adapters/repositories/mappers/user_mapper.py:55,78`, передают их через datetime_from_db, приписывающий UTC. Ticket/TicketUser используют datetime.now(UTC) и этому конкретному дефекту не подвержены.

**Условие/последствия.** На UTC-хосте сдвиг скрыт; на non-UTC хосте ложные абсолютные времена, различная timezone-семантика POST/GET и несопоставимые даты между типами сущностей. Не заявляю, что из-за этого доказан обход срока токена: auth-токены используют свои aware UTC времена.

**Исправление.** Создавать все новые даты через datetime.now(UTC), сохранять единым datetime_to_db. Для старых naive значений отдельно определить известную timezone происхождения; простая приписка UTC не является конверсией. По OWNER-NOTES миграция рабочих БД не требуется.

**Проверка.** Создание/roundtrip в UTC и UTC+03; абсолютное время не должно меняться, wire datetime должен быть aware в обоих ответах. Уверенность высокая; отдел проверен HTTP, остальные места подтверждены кодом.

## Существенные риски и вопросы контракта, отдельно от доказанных нарушений

### R-01. Удалённое самоназначение не участвует в общем guard по Admin; риск при PostgreSQL

`PATCH /admin/tickets/{id}/start-remote-work` (`src/web/routers/admin/tickets.py:814–843`) → application `ticket_service.py:694–722`: из ACCEPTED выполняется ensure_can_assign по ранее загруженному actor, затем в Ticket добавляются ASSIGNED и AT_WORK. В отличие от обычного assign (`ticket_service.py:581–630`, touch executor на :623), здесь нет admins.touch(actor).

Возможное interleaving при PostgreSQL READ COMMITTED: T1 прочитал enabled Admin в отделе A и ACCEPTED Ticket из A; T2 проверил отсутствие текущих назначений, поменял отдел/отключил Admin и сохранил его; T1 по прежнему объекту прошёл policy, записал только Ticket и commit. Ни проверяемая версия Admin, ни общий guard при T1 не меняются. Получается назначение уже отключённого/чужого отдела Admin.

**Граница вывода:** на текущей SQLite read→write upgrade не позволяет произвольно успешно записать старый snapshot; при таком конфликте ожидается отказ класса PY-01. Нарушение инварианта на текущей SQLite не воспроизведено и не заявляется. Это конкретный пробел переносимого протокола из `docs/futher/concurrency_control.md` с учётом заявленного PostgreSQL production.

**Исправление/проверка:** touch actor в ветке самоназначения, единая policy/guard-последовательность с обычным assign; детерминированная интеграционная проверка двух PostgreSQL транзакций: remote self-assign против disable/change_department. Уверенность высокая по отсутствию guard; поведение PostgreSQL требует отдельного исполнения.

### R-02. Активный Admin появляется в отключённом Department через enable

Последовательный реальный HTTP сценарий: отключённый Admin принадлежит отделу, в котором нет других активных Admin/Ticket; `PATCH /admin/departments/{id}/disable` успешно; затем `PATCH /admin/admins/{id}/enable` успешно. В синтетической БД подтверждено `department.enabled=0, employee.enabled=1`.

Путь второго вызова: `src/web/routers/admin/admins.py:362–381` → application `src/application/services/admin_service.py:387–407` → `src/domain/services/admin_service.py:169–174` просто admin.enable → save employee, отдел не загружается и не touch-ится. Проверка запрета отключения отдела с enabled admin есть в `src/domain/services/department_service.py:68–98`.

Это подтверждённая асимметрия политики. OWNER-NOTES/rules явно запрещают назначение в отключённый отдел и отключение отдела с enabled Admin, но отдельно enable уже назначенного Admin не определён. Поэтому окончательную классификацию как нарушение бизнес-требования оставляю владельцу. Если инвариант «нет enabled Admin в disabled Department» желателен, enable должен проверять и touch-ить Department; иначе нужно явно описать допустимое состояние и его влияние на работу. Уверенность высокая в сценарии, средняя в нормативной оценке.

### R-03. В Ticket.comment наружу выходит VO-объект, в TicketUser — строка

`TicketAssembler.to_dto`, `src/application/assemblers/assembler.py:44–71`, передаёт `record.comment` и `comment.comment` без `.value`; `TicketResponse.statuses/comments`, `src/web/models/tickets.py:281–286`, — свободные dict[str,Any]. Поэтому настоящий JSON содержит `"comment":{"value":"visible text"}` и для обычного комментария, и для комментария статуса. У TicketUser assembler на `assembler.py:117–139` отдаёт строки. Схема API не фиксирует поля вложенных элементов.

Воспроизведено `POST /admin/tickets/` с непустым comment. Это подтверждённая разница формы, но формальный контракт строкового comment для Ticket в пакете недостаточно строг, поэтому не называю её доказанной несовместимостью конкретного фронтенда. Рекомендуется выбрать единый внешний контракт, добавить типизированные вложенные response-модели и тест реального JSON. Простой переход к `.value` следует проверить на потребителях. Уверенность высокая в наблюдении.

## Что проверено и не является находкой об ошибке

1. **Одна атомарная UoW.** Репозитории создаются с одним Connection (`src/adapters/uow/sqlite_unit_of_work.py:44–70`). Begin/commit/rollback в `:76–159`; выход с исключением не подавляет исходное исключение. Dependency закрывает request-scoped Connection.
2. **Откат связанной пары и guards.** Через admin create-for-user намеренно поднята PersistenceError после настоящего INSERT внутреннего Ticket, когда TicketUser, статусы и touch client/user уже выполнены. HTTP 500 соответствует искусственной внутренней ошибке. После отказа количества tickets/user_tickets/обеих status-таблиц и версия Client совпали с исходными. Частичные записи не остались.
3. **Optimistic root locking.** В отдельной синтетической проверке прочитаны две копии Ticket версии 0; одна сохранена как ACCEPTED; сохранение второй как REJECTED дало OptimisticLockError. В БД остались ровно CREATED→ACCEPTED и version=1. Это не заменяет PY-01: SQLite busy возникает раньше rowcount-проверки.
4. **Workflow по OWNER-NOTES.** Настоящие remote-start и finish-work вернули 200; finish оставил READY_FOR_REVIEW/open. Отключение Client перевело эту заявку в SUSPENDED/closed. В отдельной связанной паре Ticket и TicketUser после finish и disable оба восстановились из SQLite как SUSPENDED/closed. Попытка accept для suspended вернула 400, восстановление запрещено.
5. **Правило отдела при удалённой работе.** Самоназначение Ticket без отдела вернуло 400. В application из ACCEPTED есть ensure_can_assign; отсутствие самой последовательной проверки принадлежности отделу не утверждаю.
6. **SQL против текущего DDL.** Все 115 строковых SQL statements действующих Gateway-классов успешно скомпилировались `EXPLAIN` на чистой SQLite БД из `db/schema.sql`. Это проверка имён/формы, не правильности логики (PY-04 успешно компилируется, но логически неверен).
7. **Пустой обычный комментарий.** HTTP add-comment с пустой строкой вернул 422; первичная гипотеза о raw ValueError здесь не подтвердилась благодаря TicketRequiredCommentRequest. Не включена в ошибки.
8. **Refresh storage.** Оба требуемых режима memory/SQLite существуют; memory имеет Lock и возвращает копии; SQLite replace выполняется под BEGIN IMMEDIATE и в одной транзакции (`src/web/auth/storage_sqlite.py:89–96`). Отсутствие дискового backend не утверждаю. В этом раунде полный security-протокол refresh не тестировался.

## Исправления и следующие проверки

Приоритет ближайшего исправления: типизированные persistence-ошибки/SQLite-конкуренция, корректный SQL is_assigned, ожидаемые application/description отказы, UTC factories. Зафиксировать внешний JSON comment и решение по enable Admin в disabled Department. До перехода на PostgreSQL закрыть R-01 и исполнить двухтранзакционные проверки общего guard.

Для повторов необходимо различать: безопасный повтор после подтверждённого rollback и повтор после неизвестного результата commit/потери HTTP ответа. Идемпотентность не поручена как действующее требование; отсутствие отдельного idempotency key не считаю ошибкой. После rollback нельзя повторно сохранять уже мутированные domain-объекты: repository до commit присваивает ID status/comment/root и увеличивает версии. Нужны новые чтения/объекты; нынешние HTTP application-операции обычно их заново загружают. `EmployeeActorHelper` кэширует actor на срок жизни экземпляра (`src/application/helper/actor_helper.py:239–281`), поэтому долгоживущие service instances при добавлении retry требуют очистки/пересоздания.

Проверки восстановления после потери процесса должны оставаться отдельным сценарием: открыть новую Connection, загрузить корни с историей, проверить date_finished/current_executor projection; не продолжать использование объектов, оставшихся после неуспешной транзакции. Для нынешнего SQLite не найдено оснований утверждать, что rollback автоматически восстанавливает эти Python-объекты, и UoW этого не обещает.

## Воспроизводимость

Первичный синтетический HTTP harness: `/tmp/python_review_bbf7a39.py`; очищенный вывод без credentials: `/tmp/python-review-bbf7a39-results.json`; SQL compilation: `/tmp/python_review_bbf7a39_sql.py`. Все БД этих сценариев — явно созданные `/tmp/python-review-*.sqlite3`. Скрипты генерируют случайные credentials в памяти и не печатают токены. Наблюдения и существенные условия полностью изложены выше, наличие временных файлов не требуется для понимания заключения.

Первичное заключение завершено. Результаты других ролей до фиксации этого файла не использовались; пересмотр и полемика оставлены следующим раундам.
