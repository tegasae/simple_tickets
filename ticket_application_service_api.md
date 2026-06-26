# TicketApplicationService — API первой версии

## 1. Границы текущей версии

В первой версии система работает только с внутренним aggregate `Ticket`.

`TicketUser` пока не создаётся и не обрабатывается. При этом информация об обращении пользователя не теряется:

- `admin_id` — сотрудник, который зарегистрировал внутренний Ticket;
- `user_id` — пользователь клиента, от которого пришло обращение: звонок, email, личное сообщение и т. п.;
- `contact_user_id` — пользователь, в интересах которого выполняется работа;
- `ticket_user_id` — пока всегда `0`, потому что отдельный aggregate `TicketUser` пока не создаётся.

Пример:

> Пользователь `10` сообщил: «У пользователя `11` не работает интернет».

```text
Ticket:
    admin_id = 5          # менеджер, создавший Ticket
    user_id = 10          # инициатор обращения
    contact_user_id = 11  # пользователь, для которого нужна работа
    ticket_user_id = 0
```

## 2. Ответственность TicketApplicationService

`TicketApplicationService`:

1. Проверяет actor и permissions.
2. Загружает `Ticket` и связанные aggregates из репозиториев.
3. Выполняет cross-aggregate проверки: существование и активность Client, Admin, Department; соответствие отдела исполнителя отделу Ticket и т. п.
4. Вызывает domain-метод `Ticket` или специализированный domain service.
5. Сохраняет изменения в одной Unit of Work.
6. Возвращает DTO.

`TicketApplicationService` не должен:

- хранить граф переходов между статусами;
- дублировать проверки из `TicketState`;
- напрямую создавать `TicketStatusRecord`;
- предоставлять общий метод вида `change_status(ticket_id, new_status, payload)`.

Статус изменяется только через предметные команды: `accept_ticket`, `schedule_ticket`, `take_to_work`, `submit_for_review` и т. д.

---

# 3. Public API

```text
# Создание и обычные данные
create_ticket(...)
update_ticket_details(...)
change_ticket_department(...)
add_comment(...)
delete_ticket(...)

# Управление Ticket
accept_ticket(...)
reject_ticket(...)
defer_ticket(...)
schedule_ticket(...)
assign_executor(...)
ready_to_work(...)
cancel_ticket(...)

# Выполнение работы
take_to_work(...)
pause_work(...)
resume_work(...)
submit_for_review(...)
record_completed_work_for_review(...)

# Review и закрытие
confirm_execution(...)
return_to_work(...)
return_to_assigned(...)
return_to_scheduled(...)
return_to_ready_to_work(...)
return_to_deferred(...)

# Чтение
list_tickets(criteria)
get_ticket(ticket_id)
```

---

# 4. Создание и обычные данные

## `create_ticket(...)`

Создаёт внутренний `Ticket` в статусе `CREATED`.

Один и тот же use case применяется, когда Ticket создаёт менеджер, инженер или другой сотрудник с соответствующим permission. Отдельные методы `create_ticket_by_manager(...)` и `create_ticket_by_engineer(...)` не нужны.

### Основные параметры

```text
actor_admin_id
client_id
user_id
contact_user_id
text_of_ticket
description
department_id
urgency_level
is_remote
```

### Семантика полей

- `actor_admin_id` — сотрудник, выполняющий команду; он записывается в `Ticket.admin_id`.
- `user_id` — пользователь клиента, который инициировал обращение; может быть указан при звонке, email или сообщении.
- `contact_user_id` — пользователь, для которого нужна работа; может совпадать с `user_id`.
- `ticket_user_id` не принимается параметром и создаётся равным `0`.

### Проверки application layer

- actor существует, enabled и имеет permission на создание Ticket;
- Client существует и enabled;
- `user_id`, если задан, принадлежит `client_id`;
- `contact_user_id`, если задан, принадлежит `client_id`;
- Department, если задан, существует и enabled.

### Не делает автоматически

Создание Ticket не должно автоматически:

- принимать Ticket;
- назначать исполнителя;
- создавать план;
- переводить Ticket в `AT_WORK`.

Позднее можно добавить отдельный композиционный сценарий для UI, но базовые workflow-команды должны сохраняться явными.

---

## `update_ticket_details(...)`

Изменяет обычные данные Ticket, не связанные с workflow.

### Можно менять

```text
text_of_ticket
description
urgency_level
is_remote
contact_user_id
```

`contact_user_id` можно изменить, например если выяснилось, что работа нужна не пользователю `11`, а пользователю `12`.

### Не изменяет

```text
client_id
admin_id
user_id
ticket_user_id
department_id
status
executor
```

Причины:

- `admin_id` и `user_id` — исторические данные о регистрации обращения;
- `client_id` определяет владельца Ticket;
- `ticket_user_id` позже будет ссылкой на отдельное внешнее обращение;
- `department_id`, статус и исполнитель имеют отдельную workflow-семантику.

Изменение обычных деталей terminal Ticket лучше запретить, чтобы не переписывать завершённую историю.

---

## `change_ticket_department(...)`

Меняет `department_id` Ticket.

### Проверяет

- actor имеет permission на изменение отдела;
- новый Department существует и enabled;
- Ticket допускает смену отдела в текущем статусе.

### Вызывает

```python
ticket.change_department(department_id=department_id)
```

Сам aggregate запрещает смену отдела в состояниях, где это нарушит смысл назначения, работы или review:

```text
ASSIGNED
READY_TO_WORK
AT_WORK
PAUSED
READY_FOR_REVIEW
REJECTED
EXECUTED
CANCELLED
```

---

## `add_comment(...)`

Добавляет обычный внутренний комментарий к Ticket.

Важно различать:

```text
Ticket.comments
    обычное обсуждение Ticket;

TicketStatusRecord.comment
    причина или пояснение конкретного workflow-перехода.
```

Пока все обычные комментарии считаются внутренними. Публичные комментарии появятся позже вместе с `TicketUser` и клиентской частью системы.

Проверяется право actor-а комментировать Ticket. Комментирование terminal Ticket в первой версии лучше запретить.

---

## `delete_ticket(...)`

Аварийная операция физического удаления Ticket.

Она нужна, когда Ticket необходимо удалить из системы, но не хочется вручную вмешиваться в базу данных: например, при ошибочном импорте, повреждённых тестовых данных или серьёзной ошибке оператора.

### Правила

- Ticket можно удалить в **любом статусе**;
- удаление не проходит через workflow;
- удаляются сам Ticket, его status history и обычные comments;
- операция выполняется в одной транзакции;
- actor должен иметь отдельное сильное permission, например `DELETE_TICKET`;
- в обычном UI операция не должна быть доступна по умолчанию.

Если в будущем Ticket будет связан с `TicketUser`, удаление внутреннего Ticket не должно автоматически удалять родительский `TicketUser`.

Название `hard_delete_ticket(...)` было бы ещё более явным, но `delete_ticket(...)` допустимо, если в проекте зафиксировано, что это физическое удаление.

---

# 5. Управление Ticket

Эти команды используют `TicketManagementService`. Application service проверяет права и внешние связи; допустимость статуса проверяет aggregate через `TicketState`.

## `accept_ticket(...)`

Переход:

```text
CREATED → ACCEPTED
```

Заявка прошла первичную проверку и признана рабочей.

---

## `reject_ticket(...)`

Переход:

```text
CREATED → REJECTED
```

Заявка не прошла первичную проверку и не станет рабочей.

Причина обязательна и записывается в комментарий status record.

После `REJECTED` Ticket terminal.

---

## `defer_ticket(...)`

Переводит Ticket в `DEFERRED`.

Используется, когда работу нельзя или нецелесообразно продолжать:

- ожидаются данные;
- требуется согласование;
- отсутствует доступ;
- нужна внешняя зависимость;
- необходимо решение клиента;
- нужен другой отдел.

Причина обязательна.

Не нужны отдельные команды `force_defer_ticket(...)` и `manager_defer_ticket(...)`: различие должно определяться permission actor-а.

Из `READY_FOR_REVIEW` используется `return_to_deferred(...)`, потому что в этом случае отложение является результатом review.

---

## `schedule_ticket(...)`

Переводит Ticket в `SCHEDULED`.

### Параметры

```text
planned_start_at
planned_finish_at
comment
```

`SCHEDULED` означает, что работа запланирована, но current executor отсутствует.

Повторный переход:

```text
SCHEDULED → SCHEDULED
```

означает перепланирование. Отдельный `reschedule_ticket(...)` не нужен: UI может назвать действие «Перепланировать», но application command остаётся той же.

---

## `assign_executor(...)`

Переводит Ticket в `ASSIGNED`.

### Параметры

```text
executor_id
comment
```

### Проверяет

- actor имеет право назначать исполнителей;
- executor существует;
- executor enabled;
- Ticket имеет Department;
- executor имеет Department;
- `executor.department_id == ticket.department_id`.

`ASSIGNED` означает: исполнитель определён, но план отсутствует.

Повторный переход:

```text
ASSIGNED → ASSIGNED
```

означает переназначение. Отдельный `reassign_executor(...)` не нужен.

---

## `ready_to_work(...)`

Переводит Ticket в `READY_TO_WORK`.

### Параметры

```text
executor_id
planned_start_at
planned_finish_at
comment
```

Смысл статуса:

```text
READY_TO_WORK = назначен исполнитель + есть план выполнения
```

Используется, когда диспетчер уже знает и исполнителя, и план. Проверки исполнителя и department такие же, как в `assign_executor(...)`.

Повторный переход `READY_TO_WORK → READY_TO_WORK` означает обновлённое назначение и/или обновлённый план.

---

## `cancel_ticket(...)`

Переводит Ticket в `CANCELLED`.

Причина обязательна.

Различие терминальных статусов:

```text
REJECTED
    Ticket не прошла первичную проверку;

CANCELLED
    Ticket была рабочей, но затем была снята.
```

Эта команда применяется и для перехода `READY_FOR_REVIEW → CANCELLED`; отдельный `cancel_from_review(...)` не нужен.

---

# 6. Выполнение работы

Эти команды используют `TicketExecutionService`.

## `take_to_work(...)`

Переход:

```text
ASSIGNED / READY_TO_WORK → AT_WORK
```

Actor должен быть current executor Ticket и иметь permission на выполнение работ.

Время начала назначается системой:

```text
actual_started_at = now()
```

Пользователь не передаёт время начала вручную.

---

## `pause_work(...)`

Переход:

```text
AT_WORK → PAUSED
```

Используется, когда начатая работа временно остановлена. Current executor сохраняется.

`PAUSED` не равно `DEFERRED`:

```text
PAUSED
    внутренняя остановка начатой работы;

DEFERRED
    внешняя или управленческая причина,
    по которой Ticket временно не продолжают.
```

---

## `resume_work(...)`

Переход:

```text
PAUSED → AT_WORK
```

Работу продолжает current executor.

Создаётся новая `AT_WORK` record, поэтому время до паузы и после неё учитывается как разные интервалы работы.

---

## `submit_for_review(...)`

Обычный путь завершения работы:

```text
AT_WORK → READY_FOR_REVIEW
```

В новой status record сохраняются:

```text
executor_id
actual_finished_at
comment
```

`actual_started_at` здесь не передаётся: начало работы уже отражено предыдущей `AT_WORK` record.

---

## `record_completed_work_for_review(...)`

Ретроспективно регистрирует уже выполненную работу.

Переход:

```text
SCHEDULED / ASSIGNED / READY_TO_WORK → READY_FOR_REVIEW
```

### Параметры

```text
executor_id
actual_started_at
actual_finished_at
comment
```

Используется, когда работа действительно была выполнена, но не проводилась через `AT_WORK` в момент выполнения:

- не было сети;
- инженер не сменил статус вовремя;
- работа выполнялась вне системы;
- данные внесли после выезда.

### Проверяет

- actor имеет право зарегистрировать факт выполненной работы;
- `actual_started_at <= actual_finished_at`;
- фактические даты не находятся в будущем;
- если в Ticket уже был current executor, переданный `executor_id` совпадает с ним;
- если Ticket находилась только в `SCHEDULED`, исполнитель фиксируется в новой `READY_FOR_REVIEW` record.

Обычно `actor_admin_id == executor_id`. Сотрудник с повышенным permission может зарегистрировать работу другого сотрудника.

---

# 7. Review и закрытие

Команды этой группы используют `TicketReviewService` и работают только из `READY_FOR_REVIEW`.

## `confirm_execution(...)`

Переход:

```text
READY_FOR_REVIEW → EXECUTED
```

Результат принят, Ticket окончательно выполнена и становится terminal.

В первой версии подтверждение выполняет сотрудник с нужным permission. Подтверждение пользователем клиента можно добавить позднее вместе с `TicketUser`.

---

## `return_to_work(...)`

Переход:

```text
READY_FOR_REVIEW → AT_WORK
```

Результат не принят, но тот же исполнитель продолжает работу.

Исполнитель берётся из текущей `READY_FOR_REVIEW` record. Новая `AT_WORK` record начинает новый рабочий интервал.

---

## `return_to_assigned(...)`

Переход:

```text
READY_FOR_REVIEW → ASSIGNED
```

Работа не принята и нужно вернуться к этапу назначения.

### Параметры

```text
executor_id
comment
```

Можно оставить прежнего исполнителя или назначить нового. Проверки исполнителя и department такие же, как в `assign_executor(...)`.

---

## `return_to_scheduled(...)`

Переход:

```text
READY_FOR_REVIEW → SCHEDULED
```

Используется, когда нужен новый план, но исполнитель пока не назначается.

### Параметры

```text
planned_start_at
planned_finish_at
comment
```

---

## `return_to_ready_to_work(...)`

Переход:

```text
READY_FOR_REVIEW → READY_TO_WORK
```

Используется, когда после review уже известны новый исполнитель и новый план.

### Параметры

```text
executor_id
planned_start_at
planned_finish_at
comment
```

---

## `return_to_deferred(...)`

Переход:

```text
READY_FOR_REVIEW → DEFERRED
```

Результат не принят, но продолжить работу сейчас нельзя или не нужно.

Причина обязательна.

---

# 8. Чтение

## `list_tickets(criteria)`

Единый запрос для таблицы оператора и всех сочетаний фильтров.

Фронт не должен вызывать разные endpoints вида:

```text
get_tickets_by_client(...)
get_tickets_by_user(...)
get_tickets_by_status(...)
get_tickets_by_dates(...)
```

Вместо этого оператор выбирает любые фильтры, а фронт всегда вызывает один endpoint, например:

```text
GET /tickets
```

с различными query parameters.

### `TicketSearchCriteria`

```text
client_id
user_id
contact_user_id
created_from
created_to
statuses
page
page_size
sort
```

Все фильтры, кроме pagination, необязательны и объединяются через `AND`.

### Семантика фильтров

```text
client_id
    Ticket конкретного клиента.

user_id
    пользователь, который инициировал обращение.

contact_user_id
    пользователь, в интересах которого выполняется работа.

created_from / created_to
    период создания Ticket.

statuses
    набор текущих статусов Ticket;
    это не поиск по старым status records.
```

### Примеры

```text
Все заявки клиента 15:
    client_id = 15

Все обращения, где пользователь 10 был инициатором:
    user_id = 10

Все работы для пользователя 11:
    contact_user_id = 11

Все Ticket со статусами AT_WORK, PAUSED, READY_FOR_REVIEW:
    statuses = [AT_WORK, PAUSED, READY_FOR_REVIEW]

Все Ticket, созданные в январе:
    created_from = 2026-01-01
    created_to = 2026-02-01

Рабочие Ticket клиента 15, созданные в июне:
    client_id = 15
    statuses = [ACCEPTED, SCHEDULED, ASSIGNED, READY_TO_WORK, AT_WORK, PAUSED, READY_FOR_REVIEW]
    created_from = 2026-06-01
    created_to = 2026-07-01
```

Для первой версии сортировка может быть фиксированной:

```text
date_created DESC
```

Новые Ticket сверху. Позднее `sort` можно открыть для ограниченного набора безопасных значений.

### Результат

Метод возвращает paginated list лёгких DTO, а не полные aggregates.

```text
TicketListItemDTO:
    ticket_id
    client_id
    user_id
    contact_user_id
    text_of_ticket
    current_status
    current_executor_id
    department_id
    urgency_level
    date_created
    is_closed
```

Историю, comments и полное описание для списка не загружаем.

---

## `get_ticket(ticket_id)`

Возвращает одну полную карточку Ticket.

Это отдельный запрос от `list_tickets(criteria)`, потому что таблица нуждается в коротких строках, а карточка — в полной информации.

### Минимальное содержимое DTO

```text
основные поля Ticket
current status
current executor_id
department_id
urgency_level
is_remote
is_closed
date_finished
working_time
status history
обычные comments
```

Отдельный `get_ticket_history(ticket_id)` сейчас не нужен: историю можно вернуть внутри `get_ticket(...)`.

Если позднее история станет большой или потребуется её догрузка по страницам, можно добавить отдельный endpoint:

```text
GET /tickets/{ticket_id}/history
```

---

# 9. Что пока намеренно не входит в API

## TicketUser

Пока не реализуются:

```text
create_ticket_user(...)
create_ticket_from_ticket_user(...)
create_ticket_from_client_request(...)
```

`Ticket.ticket_user_id` остаётся равным `0`.

## Универсальный переход статуса

Не создаётся:

```text
change_status(ticket_id, new_status, payload)
```

Он позволил бы UI обходить предметный смысл отдельных команд.

## Дополнительные фильтры дат

Пока используются только `created_from` и `created_to`.

Позднее могут появиться отдельные, не смешиваемые фильтры:

```text
planned_from / planned_to
finished_from / finished_to
actual_work_from / actual_work_to
```
