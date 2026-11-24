# Возможности Python API и переход на общее хранилище

Примеры относятся к `869cd42` либо к обозначенному варианту с патчами. Перед выполнением подставьте ID синтетических объектов и Bearer из входа соответствующей роли. JSON в ответах показан в части полей, существенных для операции. Числовые ID иллюстрируют связи и зависят от записей в базе.

## F-01 Строковый текст комментариев

Admin с доступом к заявке читает её через `GET /admin/tickets/{ticket_id}`. Ответ 200 сохраняет исторические события и выдает строки в `statuses[].comment` и `comments[].comment`. У события без текста значение `""`. Добавление обычного комментария требует незакрытой карточки и `TICKET_OPERATION`.

```http
POST /admin/tickets/{ticket_id}/comments
Content-Type: application/json

{"comment":"Ordinary operator note"}
```

Ответ **200**, добавленный элемент `comments` содержит `{"comment":"Ordinary operator note","actor_id":1}` при Admin с ID 1. Вызов чтения возвращает тот же комментарий после фиксации. В сценарии `PATCH /admin/tickets/{ticket_id}/accept` с `{"comment":"Accepted by operator"}` статусный комментарий в успешном ответе и повторном GET равен `"Accepted by operator"`. Текущий код выдаёт строки для заявки User, регистрации Admin за User и самостоятельной карточки Admin. [Тест ответа и повторного чтения](../tests/test_comment_api.py#L30)

У `POST /user/tickets/{ticket_user_id}/comments` сохраняется строковый контракт в пределах разрешённой пользовательской карточки. Для обоих POST `{}`, `{"comment":null}` и `{"comment":"  "}` возвращают **422**. Истории обеих карточек остаются прежними. Пустое значение в старой записи статуса при чтении и недействительный пустой вход при добавлении — разные поля контракта. [Проверка трёх отказов для обеих ролей](../tests/test_comment_api.py)

При телефонной заявке внутреннее событие регистрации хранит Admin, а внешний `CREATED` хранит User. Введённый Admin обычный комментарий имеет автора Admin. Успешный `POST /admin/tickets/` с `client_id`, `user_id`, `text_of_ticket` и `comment` возвращает 201 с двумя связанными ID. Это действующее правило, отклонённый патч 01 для него не нужен. [Тест регистрации по телефону](../tests/test_comment_api.py)

## F-02 Сроки первой выдачи токенов

Для входа User нужен активный User, Account и Client, для Admin — активный Admin и Account. Пароль передаётся как поле формы. Успешный ответ содержит пару токенов, тип `bearer` и длительность access в целых секундах.

```http
POST /auth/user/login
Content-Type: application/x-www-form-urlencoded

username={synthetic_login}&password={synthetic_password}
```

При времени, зафиксированном тестом, ответ **200** содержит `{"token_type":"bearer","expires_in":300}` и поля `access_token` и `refresh_token`. В живом вызове к моменту сборки ответа часть первой секунды уже может пройти, поэтому `expires_in` может быть 299. В сохранённой сессии разница между датами равна 7 суткам. Неверный пароль даёт **401**. Для Admin путь меняется на `/auth/admin/login`; пример Admin выполнен в тестах жизненного цикла. [Тест выдачи и неверного пароля](../tests/test_lifetime.py) · [Фактический Admin login](../tests/test_shared_sessions.py)

Настройки по умолчанию называются `ACCESS_TOKEN_EXPIRE_MINUTES` и `REFRESH_TOKEN_EXPIRE_DAYS`. В тесте проверены исходные значения 5 и 7 без TTL overrides. [Тест Settings](../tests/test_lifetime.py#L37)

## F-03 Ротация до абсолютной даты

```http
POST /auth/user/refresh
Content-Type: application/json

{"refresh_token":"{refresh_from_login_or_last_rotation}"}
```

Ответ **200** возвращает новую пару и новый refresh. Первоначальные `created_at` и `expires_at` сохранены. При 45 оставшихся секундах выдаваемый access ограничен этим интервалом. Refresh предыдущей ротации повторно получает **401**. При достижении абсолютной даты текущий refresh получает **401** и преемник отсутствует. Параллельная ротация даёт один успех и одну отклонённую попытку, включая допустимую занятость SQLite **503**. При исключении кодирования ответ **500**, старая сессия остаётся пригодной для следующего вызова. Для Admin действует `POST /auth/admin/refresh`. [Тесты срока, чтения записи и ротации](../tests/test_lifetime.py)

В старых адаптерах тест отдельно читает UTC даты без смещения, сохранённые до обновления. Они трактуются как UTC. При вводе F-06 старые refresh больше не принимаются, поэтому сценарий чтения прежней формы хранения выполняется в исходном варианте. [Тест старой метаинформации](../tests/test_lifetime.py) · [Тест перехода](../tests/test_migration.py)

## F-04 Назначение исполнителя

Admin с `TICKET_OPERATION` выбирает положительный ID активного Admin в отделе заявки. Тест создаёт пару через `POST /user/tickets/`, получает внутренний ID и выполняет `PATCH /admin/tickets/{id}/accept` с телом `{}` и правом `TICKET_ACCEPTED`. Затем вызывает `PATCH /admin/tickets/{id}/department` с `{"department_id":1}` и правом `TICKET_OPERATION`. [Проверка отдельных прав и тела accept](../tests/test_http_roles.py)

```http
PATCH /admin/tickets/{ticket_id}/executor
Content-Type: application/json

{"executor_id":1}
```

Ответ **200** содержит `current_executor_id: 1` и историю с последним `status: "assigned"`. После открытия новой UoW внутренний статус `ASSIGNED`, внешний `IN_WORK`, и версия выбранного исполнителя выросла на единицу. Выбор другого Admin того же отдела проверен отдельно. Попытка назначить Admin из другого отдела получает **400**, прежний исполнитель, статусы и история обеих карточек сохранены. Ошибка версии исполнителя даёт **409**, а введённый отказ после сохранения заявки даёт **500** с откатом обеих историй и изменения версии Admin. [Тесты назначения и отката](../tests/test_executor_guard.py)

Прямой прикладной вызов выполняет тот же путь с `TicketApplicationService(uow).assign(ticket_dto=TicketDTO(actor_admin_id=1, ticket_id=ticket_id, executor_id=1))`. Свойства актёра и состояние заявки проверяются в открытой этим сервисом UoW. [Реальный вызов через HTTP](../tests/test_executor_guard.py#L9)

## F-05 Начало удалённой работы

Admin с `TICKET_AT_WORK_REMOTE` запускает работу по заявке с разрешённой удалённой работой. Пример создания принадлежит User и использует `{"text_of_ticket":"Synthetic request","remote_work_recommended":true}`. Затем Admin принимает заявку с телом `{}` и правом `TICKET_ACCEPTED` и указывает свой отдел с правом `TICKET_OPERATION`. [Проверка отдельного remote-разрешения](../tests/test_http_roles.py)

```http
PATCH /admin/tickets/{ticket_id}/start-remote-work
Content-Type: application/json

{}
```

Ответ **200** содержит `current_executor_id` инициатора и последние внутренние события `assigned`, `at_work`. У `at_work` стоит `work_is_remote: true`. Новый исполнитель сохраняется, его версия растёт, внешняя карточка имеет `IN_WORK`. Из `ASSIGNED` текущий исполнитель может передать `{"comment":"Started remotely"}`. Ответ **200**, добавлено только событие работы, отдельная запись назначения отсутствует. Отсутствие отдела при новом назначении, выключенная рекомендация, другой текущий исполнитель и повтор из `AT_WORK` дают **400**. Проверки отката совпадают по механизму с F-04. [Тесты self, ASSIGNED, отказов и двух историй](../tests/test_executor_guard.py)

## F-06 Постоянный отзыв refresh

**Работает полностью в предлагаемом варианте с патчем 05.** Текущая ветка выдаёт, ротирует и отзывает отдельные сессии через logout, но при смене пароля и повторном включении старый refresh может остаться действующим. После замены Account того же сотрудника с прежним логином текущий код также принимает старый refresh. Это N01. [Тесты N01 на обеих версиях](../tests/test_shared_sessions.py)

После перехода пользователь входит по F-02. Refresh связан с сохранённым `account_id`, типом и ID субъекта. В основной SQLite хранится отпечаток токена, даты и данные области. Изменение аккаунта и удаление сессий входят в одну транзакцию. Удаление Account удаляет связанные сессии через FK. Общая проверка версии сотрудника согласует выдачу и ротацию с мутациями.

```http
PATCH /admin/users/{employee_id}/password
Content-Type: application/json

{"password":"{new_synthetic_password}"}
```

Admin с `USER_OPERATION` получает **200** и DTO изменённого User. Старый пароль даёт **401** при новом входе. Повтор через `POST /auth/user/refresh` с refresh, выпущенным до смены пароля, после патча даёт **401**, хеш сессии отсутствует. Новый вход даёт **200** и новую рабочую пару. Для сотрудника Admin используются `/admin/admins/{employee_id}/password`, разрешение `ADMIN_OPERATION` и `/auth/admin/refresh`. [Проверки password, admin/user и двух сессий](../tests/test_shared_sessions.py#L80)

| Команда Admin | Результат после патча 05 |
|---|---|
| `PATCH /admin/{users или admins}/{id}/disable`, затем `/enable` | 200 на изменениях, прежний refresh получает 401 после включения |
| `PATCH /admin/{users или admins}/{id}/account/disable`, затем `/account/enable` | 200 на изменениях, старые сессии не возрождаются |
| `DELETE /admin/{users или admins}/{id}/account`, затем `POST` в тот же путь с `login` и `password` | 200 на изменениях, новый Account имеет другой ID и требует login |
| `POST /admin/{users или admins}/{id}/account` с доступным новым логином и паролем при существующем Account | 200 с новым логином. Две прежние записи refresh удалены, новый вход работает. [Проверка Admin и User](../tests/test_refresh_attach_replacement.py) |
| `DELETE /admin/{users или admins}/{id}` | 204 при отсутствии запрещающих ссылок, Account и сессии удалены |
| `PATCH /admin/clients/{id}/disable` | 200, Client и Users отключены, пара на проверке закрыта как SUSPENDED, их refresh отозваны |

Параметры disable, enable и DELETE передаются только в пути. Новые сеансы после enable получают обычные сроки. При отключении клиента его повторное включение само по себе не включает сотрудников, каждый User включается отдельной командой. Искусственный отказ записи при смене пароля, замене Account и каскаде даёт **500** и откат сделанных изменений. При конкуренции SQLite WAL во время Client disable и login или refresh одна команда фиксируется с **200**, вторая получает **503**. Если отключение клиента пришлось повторить, успешная команда удаляет и выданную в промежутке сессию. [Каскад и откат](../tests/test_shared_sessions.py) · [Откат attach](../tests/test_refresh_attach_replacement.py) · [Обе очередности COMMIT](../tests/test_client_session_order.py)

```http
POST /auth/user/logout
Content-Type: application/json

{"refresh_token":"{refresh_issued_to_user}"}
```

Ответ **200** содержит `{"message":"Logged out successfully"}`. Другая сессия того же User остаётся пригодной для обновления. Для отзыва всех своих сессий можно передать `{"username":"{synthetic_login}"}` с Bearer соответствующего User. Запрос в чужой контур возвращает **401**. Один новый экземпляр `create_app()` читает и отзывает сессию, которую выпустил другой экземпляр с тем же `DATABASE_URL`. [Тесты logout и общего доступа](../tests/test_shared_sessions.py)

## F-07 Обновление SQLite и версий

**Только после патча 05, с таблицей ключей после 06.** Сотрудник, выполняющий выкладку, запускает обновление существующей основной БД на поддерживаемой схеме при остановленных writers. Операция получает явный путь. Пример штатного вызова, выполненный в тесте на временном файле.

```bash
python scripts/migrate_backend_storage.py /tmp/legacy-synthetic.sqlite3
```

Код выхода **0**. Для тестового набора исправляется по одной NULL-версии в departments, employees и clients, оставшиеся версии 5, 7 и 9 сохранены. Новые вставки получают `DEFAULT 0`, запись NULL запрещена. Связи, уникальность имени отдела, номера AUTOINCREMENT и CAS старой копии проверены после миграции. Повторный запуск даёт нулевые счётчики. Нарушение FK прерывает переход с откатом всех изменений. Вариант вызова из Python `migrate(connection)` выполняет ту же проверенную функцию CLI с собственной транзакцией. [Тест миграции и отката](../tests/test_migration.py)

Остановите workers старой версии перед сменой хранилища. Обновите основную БД и запустите приложение с прежним `DATABASE_URL`. Переменные `REFRESH_TOKEN_BACKEND` и `REFRESH_TOKEN_SQLITE_PATH` читаются для совместимости развёртывания, но активные маршруты используют основную БД. Старые refresh, в том числе из прежней таблицы в основном файле, получают **401**. Новый login даёт **200**, после чего второй экземпляр приложения успешно ротирует новую сессию. [Проверка CLI и обоих расположений старых сессий](../tests/test_migration.py)

## F-08 Создание с Idempotency-Key

**Повтор результата реализован в варианте с патчем 06 после 05.** На текущем `869cd42` каждый обычный POST работает по собственным условиям, а заголовок игнорируется. Повтор создаёт дополнительные записи либо получает доменный отказ, например 409 при повторе уникального имени Department. N06. [Сравнение фактических прогонов](../tests/results.md#f-08)

```http
POST /user/tickets/
Idempotency-Key: demo-create-1
Content-Type: application/json

{"text_of_ticket":"Synthetic repeated owner request"}
```

User с `TICKET_OPERATION` в активном Client получает **201**, тело содержит новый `ticket_user_id`. Повтор возвращает тот же ID, статус и тело. В SQLite единственная пара и по одной исходной записи истории на карточку. Передача того же ключа и `{"text_of_ticket":"Synthetic repeated owner request updated"}` даёт **409** с полем `detail` «Idempotency-Key already used for a different request». После отказа новой пары нет. Поля `description` и `contact_user_id` можно опустить либо передать с их значениями по умолчанию `""` и `0`. В проверенном примере сервер считает эти варианты одинаковым запросом. [Тесты равного и изменённого запроса](../tests/test_idempotent_creations.py#L106) · [Тест значений по умолчанию](../tests/test_idempotent_creations.py#L212)

У остальных POST тот же заголовок и правила повторов. Ниже вход и поля ответа из параметризованных запросов. Имя `Synthetic creation …` получает отдельное синтетическое окончание в каждом запуске.

| Метод и путь | Кто вызывает и что передаёт в JSON | Успешный ответ и изменения |
|---|---|---|
| POST `/admin/clients/` | Admin с `CLIENT_CREATE`, `CLIENT_OPERATION` или `CLIENT_DECISION`. `{"name":"Synthetic creation …"}` | 201 и `client_id`, один Client |
| POST `/admin/departments/` | Admin с `DEPARTMENT_OPERATION`. `{"name":"Synthetic creation …"}` | 201 и `department_id`, один Department |
| POST `/admin/admins/` | Admin с `ADMIN_OPERATION`. `{"first_name":"Synthetic creation …"}`. Для Account добавляются `login` и `password` | 201 и `employee_id`, один Admin. При переданных реквизитах сохраняется и Account |
| POST `/admin/users/` | Admin с `USER_OPERATION`. `{"first_name":"Synthetic creation …","client_id":1}`, отдельно проверен вложенный Account | 201 и `employee_id`, один User и при указании Account |
| POST `/admin/roles/admin` | Admin с `ROLE_ASSIGN`. `{"name":"Synthetic creation …","permissions":["ticket.view"]}` | 201 и `role_id`, одна роль Admin |
| POST `/admin/roles/user` | Admin с `ROLE_USER_ASSIGN`. Тот же пример с разрешением User `ticket.view` | 201 и `role_id`, одна роль User |
| POST `/admin/tickets/` | Admin с правом создания или операции. `{"client_id":1,"user_id":2,"text_of_ticket":"Synthetic repeated staff request"}` | 201, `ticket_id` и `user_ticket_id` одной пары, история сохраняется один раз |
| POST `/admin/tickets/{ticket_id}/comments` | Admin с `TICKET_OPERATION` для открытой заявки. `{"comment":"Synthetic repeated staff note"}` | 200, `ticket_id` и история с одним добавленным комментарием |
| POST `/user/tickets/{ticket_user_id}/comments` | User с правом операции по карточке своего клиента. `{"comment":"Synthetic repeated owner note"}` | 200, `ticket_user_id` и история с одним добавленным комментарием |

[Фикстуры всех десяти маршрутов и дополнительных вариантов](../tests/test_idempotent_creations.py) · [Результаты F-08](../tests/results.md#f-08)

Без заголовка POST выполняет обычную команду. Разные ключи задают отдельные действия, обычные ограничения уникальности применяются. Один необязательный заголовок виден в OpenAPI. Пустое значение, пробелы, длина больше 128 символов дают **422**. Изменение адресата комментария при прежнем ключе даёт **409**. Обновление access того же субъекта оставляет область ключа прежней. Утрата права даёт **403** даже при совпавшем ключе. [Тест контрактов, прав и разных ключей](../tests/test_idempotent_creations.py)

Клиент повторяет запрос при потере ответа с прежним телом и ключом. При конкуренции тест наблюдает штатный ответ SQLite **503** до завершения записи. Следующий запрос получает сохранённый **201**, эффект один. После отката результата или бизнес-записей очередной вызов может успешно выполнить команду. При истечении 24 часов ключ может использоваться снова. Редкая остановка после COMMIT и до отметки срока оставляет результат доступным, а отметка восстанавливается по принятому правилу. [Прерывание ответа, rollback, 503 и TTL](../tests/test_idempotency_transactions.py) · [503 на COMMIT и восстановление другим ключом](../tests/test_idempotency_commit_boundary.py)

Отпечаток применяет те же правила, что успешная команда. Например, для `POST /admin/departments/` имена `"Synthetic department"` и `" Synthetic department "` совпадают. Повтор с ключом возвращает тот же 201 и ID. Регистр email и внешние пробелы логина также нормализуются. Пробелы в значениях, которые команда хранит как есть, могут менять отпечаток. Изменённый пароль под прежним ключом получает 409. Даже при равном отпечатке текущие права проверяются. [Проверка нормализованных входов и конфликтов](../tests/test_idempotency_normalized_input.py)

## F-09 Начальное состояние Department

**Переданное состояние сохраняется после патча 07.** Admin с `DEPARTMENT_OPERATION` может создать временно выключенный отдел без дополнительной команды.

```http
POST /admin/departments/
Content-Type: application/json

{"name":"Synthetic initial department","enabled":false}
```

Ответ **201** содержит `department_id` и `"enabled":false`. Для Admin с `DEPARTMENT_VIEW` запрос GET `/admin/departments/{department_id}` возвращает 200 с тем же флагом. После отдельной загрузки строки `enabled` ложен. В исходной ветке для этого запроса получен 201 с `true`, и SQLite тоже хранит включённое состояние. D01. Если поле убрать или отправить `true`, отдел включён. Явный `null` даёт **422** и оставляет число отделов прежним. Тот же флаг участвует в отпечатке запроса с ключом. [Приёмка создания](../tests/test_department_initial_state.py) · [Проверка прав чтения](../tests/test_http_roles.py) · [Протокол F-09](../tests/results.md#f-09)

Прикладной путь `DepartmentApplicationService(uow).create_department(department_dto=DepartmentDTO(actor_admin_id=1, name="Synthetic initial department", enabled=False))` проходит через ту же команду, что и HTTP. [Патч](../patches/07-department-initial-state.patch)

## F-10 Профиль Admin и необязательный отдел

**Пропуск сохраняет отдел после патча 08.** Вызывающий Admin имеет `ADMIN_OPERATION`. Для обычной правки имени достаточно тела ниже.

```http
PUT /admin/admins/{employee_id}
Content-Type: application/json

{"first_name":"Updated operator"}
```

Ответ **200** содержит прежний `department_id` и новое имя. Текущая пара с назначенным сотрудником сохраняет состояние. Остальные личные поля PUT по-прежнему используют свои значения по умолчанию, поэтому передайте нужные значения имени, фамилии и контактов полностью. На 869cd42 имя свободного исполнителя менялось вместе со снятием отдела. У текущего исполнителя тот же запрос возвращал **400**. D02. [Модель запроса](https://github.com/tegasae/simple_tickets/blob/869cd424b1b9f13babd720884a3cbb7e0f6a10bb/src/web/models/admins.py#L31-L43) · [Протокол F-10](../tests/results.md#f-10)

| Вход | Проверенный исход с патчем 08 |
|---|---|
| Поле пропущено | 200, прежний отдел и назначение сохраняются |
| `{"first_name":"Updated operator","department_id":0}` для свободного Admin | 200, `department_id:0` после повторного чтения |
| То же с текущим исполнителем | 400, прежние имя, отдел, состояние пары и исполнитель |
| Положительный существующий ID активного отдела | 200 для свободного сотрудника, сохранён новый отдел |
| Неизвестный ID | 404, прежний профиль |
| `null` | 422, прежний профиль |

Отдельное управление назначением отдела остаётся обычной операцией `PATCH /admin/admins/{employee_id}/department`. Прикладной `AdminApplicationService(uow).update_admin(admin_dto=dto, update_department=False)` используется маршрутом для пропуска. Прямой вызов без нового параметра сохраняет прежнее явное правило DTO. [Приёмка HTTP и чтения](../tests/test_admin_profile_department.py) · [Проверка прямых вызовов](../experts/implementation-analyst.md)

## F-11 Нормализованный дубликат логина

Администратор с правом создать сотрудника передаёт существующий синтетический логин. Два прогона отличаются только пробелами по краям.

```http
POST /admin/admins/
Content-Type: application/json

{"first_name":"Synthetic duplicate registration","login":" {existing_login} ","password":"{synthetic_password}"}
```

После патча 09 оба варианта дают **400** с сообщением о занятом логине. В исходнике каноническая форма уже даёт 400, а форма с пробелами возвращает **500**. D03. Повторное чтение `employees`, `admins`, `users` и `accounts` подтверждает прежнее число записей. Пользовательский вариант выполняется через `POST /admin/users/` с включённым `client_id` в тело. Общая предпроверка применяется в прикладных командах создания и прикрепления Account. [Приёмка обеих ролей](../tests/test_account_creation_input.py) · [Патч](../patches/09-normalize-login-check.patch)

## F-12 Значение режима работы в истории

**Повторное чтение сохраняет смысл отсутствующего режима после патча 10.** Для истины используется `work_is_remote:true`, для офисной работы `false`, а для события вне работы — `null`. В тесте Admin создаёт `POST /admin/tickets/` с `client_id`, включённым `department_id` и `{"text_of_ticket":"Work mode round trip"}`, получает 201. С согласованной ролью автоматического приёма ответ содержит события created и accepted.

```http
GET /admin/tickets/{ticket_id}
Authorization: Bearer {admin_access}
```

После патча ответ **200** содержит в истории `{"status":"created","work_is_remote":null}` и `{"status":"accepted","work_is_remote":null}`. На исходнике GET выдаёт `false` для обеих записей, хотя исходный POST и SQL имеют `null`. D04. После назначения и `PATCH /admin/tickets/{ticket_id}/start-work` с `{"work_is_remote":true}` новый `at_work` и последующий GET содержат true. Отдельно проверена явная офисная ветка. Старую рабочую строку со SQL NULL mapper по-прежнему читает как false. [Проверка ответов и legacy](../tests/test_ticket_work_mode_roundtrip.py) · [Протокол F-12](../tests/results.md#f-12)

## Подтверждённые правила контакта

В начальной паре Admin и User могут вызвать соответствующий `PATCH /admin/tickets/{ticket_id}/contact-user` или `PATCH /user/tickets/{ticket_user_id}/contact-user` с `{"contact_user_id":3}`. Ответ **200** и повторное чтение подтверждают сохранение положительного контакта в обеих карточках без смены их статусов. Если эта пара затем оказывается на проверке, отключение только контактного User через `PATCH /admin/users/{contact_user_id}/disable` даёт **200** и закрывает обе в SUSPENDED. Владелец остаётся включён. [Применённый контракт и тесты](../tests/test_contact_policy.py)
