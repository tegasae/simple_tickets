# Технический долг: `SUSPENDED`, восстановление заявок и история происхождения

## Статус

**Требует реализации.**

---

## 1. Проблема текущей модели

`SUSPENDED` используется, когда продолжение работы по заявке невозможно из-за внешнего состояния связанных сущностей, прежде всего при отключении `Client`.

Ранее из `SUSPENDED` были разрешены переходы обратно в рабочие состояния.

Пример:

```text
CREATED
-> ACCEPTED
-> SUSPENDED
-> DEFERRED
-> ACCEPTED
-> SUSPENDED
-> CANCELLED
```

Для проверки корректности такого исторического перехода пришлось бы знать состояние `Client` / `User` / `Contact User` именно в момент перехода.

Текущее состояние связанных сущностей для проверки history недостаточно.

---

## 2. Новая семантика `SUSPENDED`

`SUSPENDED` больше не является обычной паузой внутри того же жизненного цикла.

После перехода в `SUSPENDED` заявка:

- не может вернуться в рабочие статусы;
- может быть окончательно отменена;
- либо после устранения причины блокировки на её основе создаётся новая заявка.

Для внутреннего `Ticket`:

```python
TicketStatus.SUSPENDED: frozenset({
    TicketStatus.CANCELLED,
})
```

Таким образом:

```text
SUSPENDED -> CANCELLED
```

разрешён.

Любые возвраты в рабочие состояния запрещены.

`SUSPENDED` не является terminal-статусом формально, но является конечным рабочим состоянием.

---

## 3. Восстановление — это создание нового `Ticket`

После повторного включения клиента старый `Ticket` не переводится из `SUSPENDED` обратно в работу.

Пример исходной заявки:

```text
Ticket #100

CREATED
-> ACCEPTED
-> ASSIGNED
-> SUSPENDED
```

После включения клиента создаётся новая заявка:

```text
Ticket #137

RESTORED_FROM_SUSPENDED
-> ACCEPTED
-> ...
```

Это два отдельных жизненных цикла.

Перехода:

```text
SUSPENDED -> RESTORED_FROM_SUSPENDED
```

в графе одного `Ticket` нет.

---

## 4. Новый статус `RESTORED_FROM_SUSPENDED`

Добавить:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

Это допустимый начальный статус нового `Ticket`.

Он находится в одной группе с:

```python
TicketStatus.CREATED
TicketStatus.CREATED_FROM_TICKET_USER
TicketStatus.RESTORED_FROM_SUSPENDED
```

Можно явно определить:

```python
INITIAL_TICKET_STATUSES: Final[frozenset[TicketStatus]] = frozenset({
    TicketStatus.CREATED,
    TicketStatus.CREATED_FROM_TICKET_USER,
    TicketStatus.RESTORED_FROM_SUSPENDED,
})
```

Предварительно переходы из него аналогичны `CREATED`:

```python
TicketStatus.RESTORED_FROM_SUSPENDED: frozenset({
    TicketStatus.ACCEPTED,
    TicketStatus.REJECTED,
    TicketStatus.CANCELLED_BY_USER,
    TicketStatus.SUSPENDED,
})
```

Точный набор переходов необходимо подтвердить перед реализацией.

Для `TICKET_STATUS_RULES`:

```python
TicketStatus.RESTORED_FROM_SUSPENDED: TicketStatusRule(
    can_change_data=True,
)
```

---

## 5. Не хранить происхождение внутри `Ticket`

Не добавлять в `Ticket` и таблицу `tickets` поля:

```text
copy_from_ticket_id
restored_from_ticket_id
parent_ticket_id
root_ticket_id
```

Происхождение одной заявки от другой — это отношение между агрегатами, а не внутреннее состояние одного `Ticket`.

---

## 6. Отдельная таблица `ticket_relations`

Добавить:

```text
ticket_relations
```

Предварительная структура:

```text
relation_id
source_ticket_id
target_ticket_id
relation_type
date_created
```

Пример:

```text
relation_id | source_ticket_id | target_ticket_id | relation_type
------------+------------------+------------------+-------------------------
1           | 100              | 137              | RESTORED_FROM_SUSPENDED
2           | 137              | 184              | COPY
3           | 184              | 205              | COPY
```

Тип связи:

```python
class TicketRelationType(Enum):
    COPY = "copy"
    RESTORED_FROM_SUSPENDED = "restored_from_suspended"
```

На первом этапе требуется только `RESTORED_FROM_SUSPENDED`.

`COPY` закладывается для будущего обычного копирования заявок.

---

## 7. Ограничения `ticket_relations`

Обязательные ограничения:

```text
source_ticket_id != target_ticket_id
```

и:

```text
UNIQUE(source_ticket_id, target_ticket_id, relation_type)
```

Следует также рассмотреть:

```text
UNIQUE(target_ticket_id)
```

если принимается правило:

> каждый новый Ticket имеет не более одного непосредственного предка.

Для обычного `COPY` один source Ticket может иметь несколько потомков:

```text
#100 -> #140
#100 -> #155
#100 -> #170
```

Для восстановления правило строже:

> один `SUSPENDED Ticket` может породить не более одного `RESTORED_FROM_SUSPENDED` Ticket.

Это ограничение желательно защитить и на уровне БД.

---

## 8. Исторический путь заявки

Таблица связей позволяет хранить полный путь происхождения.

Пример:

```text
Ticket #100
    |
    | COPY
    v
Ticket #140
    |
    | COPY
    v
Ticket #201
    |
    | RESTORED_FROM_SUSPENDED
    v
Ticket #260
```

В БД:

```text
100 -> 140  COPY
140 -> 201  COPY
201 -> 260  RESTORED_FROM_SUSPENDED
```

Для `Ticket #260` можно восстановить:

```text
100 -> 140 -> 201 -> 260
```

Отдельный `root_ticket_id` не требуется.

В будущем repository может предоставлять:

```python
get_parent(ticket_id)
get_children(ticket_id)
get_ancestry(ticket_id)
get_descendants(ticket_id)
```

---

## 9. Зачем нужны и статус, и relation

У восстановленной заявки одновременно существуют:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

и relation:

```text
source #100 -> target #137
RESTORED_FROM_SUSPENDED
```

Они отвечают на разные вопросы.

Статус:

> почему начался жизненный цикл этого Ticket?

Relation:

> из какого именно Ticket он был создан?

---

## 10. Отключение клиента

При отключении `Client` соответствующие незакрытые заявки переводятся в:

```python
TicketStatus.SUSPENDED
```

После этого каждая такая заявка может:

1. оставаться в `SUSPENDED`;
2. быть переведена в `CANCELLED`.

Возврат в рабочие состояния запрещён.

---

## 11. Повторное включение клиента

Когда `Client` снова становится enabled, необходимо найти его заявки:

- текущий статус которых `SUSPENDED`;
- которые не были переведены в `CANCELLED`;
- для которых ещё не существует восстановленной заявки.

Для каждой такой заявки создаётся новый `Ticket`.

Пример:

```text
Client disabled
      |
      v
Ticket #100 -> SUSPENDED


Client enabled
      |
      v
Ticket #100 остаётся SUSPENDED

создаётся:

Ticket #137
RESTORED_FROM_SUSPENDED

relation:

#100 -> #137
RESTORED_FROM_SUSPENDED
```

Старый `Ticket` не изменяется.

---

## 12. Как определить уже восстановленные заявки

Не добавлять в `Ticket` флаг:

```text
is_restored
```

Наличие восстановленной заявки определяется через `ticket_relations`.

Концептуально:

```sql
SELECT source.*
FROM tickets AS source
WHERE source.client_id = :client_id
  AND source.current_status = 'SUSPENDED'
  AND NOT EXISTS (
      SELECT 1
      FROM ticket_relations AS relation
      WHERE relation.source_ticket_id = source.ticket_id
        AND relation.relation_type = 'restored_from_suspended'
  )
```

Точная реализация зависит от текущей схемы хранения status history.

---

## 13. Операция восстановления

Восстановление не является методом:

```python
source_ticket.restore()
```

потому что исходный aggregate не изменяется.

Операция должна находиться в `TicketService`:

```python
new_ticket = TicketService.restore_from_suspended(
    source_ticket=source_ticket,
    ...
)
```

Минимальные проверки:

```text
source Ticket находится в SUSPENDED
Client снова enabled
для source Ticket ещё не существует restoration relation
```

После этого создаётся новый aggregate с первым статусом:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

---

## 14. Транзакция восстановления

Создание нового `Ticket` и relation должно быть атомарным.

Application layer:

```text
load source Ticket
load Client
load необходимые связанные aggregates

проверить permissions

TicketService создаёт новый Ticket

save(new_ticket)

insert TicketRelation(
    source_ticket_id=source_ticket.ticket_id,
    target_ticket_id=new_ticket.ticket_id,
    relation_type=RESTORED_FROM_SUSPENDED
)

touch(source_ticket)
touch(Client)
touch других aggregates, участвовавших в решении)

commit
```

Если relation не сохранилась, новый Ticket также не должен остаться сохранённым.

---

## 15. Optimistic locking

`source_ticket` участвует в решении о восстановлении, поэтому его следует `touch()`.

`Client` также участвует в решении:

```text
client.enabled == True
```

поэтому его следует `touch()`.

Если состояние `User` / `Contact User` будет участвовать в восстановлении, их также следует `touch()`.

---

## 16. Какие данные копируются

Новая заявка начинает новый жизненный цикл, но создаётся на основе исходной.

Предварительно могут переноситься:

```text
client_id
user_id
contact_user_id
department_id
text_of_ticket
description
urgency_level
planned_at
remote_work_recommended
```

Не копируются как history:

```text
statuses
status_id
date_finished
накопленное work time
исторические назначения исполнителей
```

Отдельно требуется решить:

- переносится ли `planned_at`;
- переносится ли `department_id`;
- переносится ли `remote_work_recommended`;
- переносится ли последний исполнитель;
- копируются ли обычные comments.

---

## 17. Проверка history при rehydrate

После изменения графа:

```text
... -> SUSPENDED -> ACCEPTED
```

всегда невалидно.

Допустима только:

```text
SUSPENDED -> CANCELLED
```

Поэтому для проверки history достаточно:

```python
next_status in TICKET_TRANSITIONS[current_status]
```

Историческое состояние `Client` больше не требуется для проверки выхода из `SUSPENDED`.

Восстановление вообще не присутствует в status history старого Ticket.

---

## 18. Будущее обычное копирование

Таблица `ticket_relations` должна использоваться и для будущего обычного копирования.

Пример:

```text
Ticket #100
    |
    | COPY
    v
Ticket #140
```

Если затем копируется копия:

```text
Ticket #140
    |
    | COPY
    v
Ticket #201
```

полный исторический путь остаётся доступен:

```text
#100 -> #140 -> #201
```

Это одна из основных причин не хранить `copy_from_ticket_id` внутри `Ticket`.

---

## 19. `TicketUser`: открытые вопросы

Для связанных пользовательских заявок необходимо отдельно определить поведение `TicketUser`.

Текущие cross-aggregate invariants должны сохраняться:

```text
Ticket.user_ticket_id == TicketUser.ticket_user_id
Ticket.client_id == TicketUser.client_id
Ticket.user_id == TicketUser.user_id
Ticket.contact_user_id == TicketUser.contact_user_id
```

### 19.1. Переход из `TicketUserStatus.SUSPENDED`

Необходимо решить, должен ли пользовательский aggregate иметь:

```text
SUSPENDED -> CANCELLED_BY_ADMIN
```

и должны ли быть запрещены все остальные выходы.

Предпочтительная симметрия:

```text
Ticket:
SUSPENDED -> CANCELLED

TicketUser:
SUSPENDED -> CANCELLED_BY_ADMIN
```

### 19.2. Что создавать при восстановлении

Если исходный `Ticket` связан с `TicketUser`, необходимо определить, создаётся ли новая пара:

```text
old TicketUser <-> old Ticket

           restore

new TicketUser <-> new Ticket
```

Предварительно наиболее согласованный вариант — создавать новую пару в одной транзакции.

### 19.3. Нужна ли отдельная relation для `TicketUser`

Предпочтительный вариант — не создавать отдельную таблицу происхождения `TicketUser`.

Relation хранится только между внутренними `Ticket`:

```text
old Ticket -> new Ticket
```

Старый `TicketUser` определяется через:

```text
old_ticket.user_ticket_id
```

Новый:

```text
new_ticket.user_ticket_id
```

Таким образом одна relation фактически связывает две пары:

```text
TicketUser #50 <-> Ticket #100
                       |
                       | RESTORED_FROM_SUSPENDED
                       v
TicketUser #81 <-> Ticket #137
```

Это решение требуется окончательно подтвердить.

### 19.4. Начальный статус нового `TicketUser`

Необходимо определить:

```text
CREATED
```

или новый:

```text
RESTORED_FROM_SUSPENDED
```

Если вводится новый статус `TicketUser`, потребуется обновить:

- enum;
- status rules;
- transitions;
- history validation;
- mapping `Ticket -> TicketUser`.

### 19.5. Mapping

Необходимо явно определить:

```text
Ticket.RESTORED_FROM_SUSPENDED
    ->
TicketUser.<status>
```

### 19.6. Исходные состояния

Для связанной заявки необходимо решить, достаточно ли:

```text
Ticket == SUSPENDED
```

или обязательно также:

```text
TicketUser == SUSPENDED
```

Предпочтительно считать рассогласование нарушением данных и не выполнять восстановление.

### 19.7. Копируемые данные `TicketUser`

Необходимо отдельно определить перенос:

```text
client_id
user_id
contact_user_id
text_of_ticket
description
urgency_level
```

Важно сохранить независимость:

```text
Ticket.description
```

и:

```text
TicketUser.description
```

### 19.8. Comments `TicketUser`

История статусов старого `TicketUser` не копируется.

Судьбу обычных comments необходимо определить отдельно.

### 19.9. Новый номер пользовательской заявки

Если создаётся новый `TicketUser`, он получает новый:

```text
ticket_user_id
```

Пользователь должен видеть это как новый жизненный цикл, связанный с предыдущей заявкой.

---

## 20. Повторные отключения

Должна поддерживаться цепочка:

```text
Ticket #100
CREATED
-> ...
-> SUSPENDED

restore

Ticket #137
RESTORED_FROM_SUSPENDED
-> ...
-> SUSPENDED

restore

Ticket #184
RESTORED_FROM_SUSPENDED
-> ...
```

Relations:

```text
100 -> 137  RESTORED_FROM_SUSPENDED
137 -> 184  RESTORED_FROM_SUSPENDED
```

Для restoration не должно возникать:

```text
100 -> 137
100 -> 184
```

---

## 21. UI

Для восстановленной заявки желательно показывать:

```text
Восстановлена из заявки №100
```

Для цепочки:

```text
№100
  -> №137
      -> №184
```

Для обычных копий:

```text
Копия заявки №100
```

Источник этой информации — `ticket_relations`, а не поля `Ticket`.

---

## 22. Необходимые тесты

### `SUSPENDED`

Проверить:

```text
SUSPENDED -> CANCELLED         разрешено

SUSPENDED -> ACCEPTED          запрещено
SUSPENDED -> DEFERRED          запрещено
SUSPENDED -> ASSIGNED          запрещено
SUSPENDED -> AT_WORK           запрещено
SUSPENDED -> PAUSED            запрещено
SUSPENDED -> READY_FOR_REVIEW  запрещено
```

### History validation

`rehydrate()` должен принимать:

```text
CREATED
-> ACCEPTED
-> SUSPENDED
-> CANCELLED
```

и отвергать:

```text
CREATED
-> ACCEPTED
-> SUSPENDED
-> DEFERRED
```

### Создание восстановленной заявки

Проверить:

- source Ticket находится в `SUSPENDED`;
- Client снова enabled;
- создаётся новый `ticket_id`;
- первая status record нового Ticket — `RESTORED_FROM_SUSPENDED`;
- history source Ticket не копируется;
- source Ticket не изменяется.

### Relation

Проверить создание relation в той же транзакции.

Проверить:

```text
source_ticket_id != target_ticket_id
```

Проверить запрет повторного восстановления одного source Ticket.

### Историческая цепочка

Проверить:

```text
100 -> 137 -> 184
```

и получение ancestry в правильном порядке.

### Повторное отключение

Проверить:

```text
#100 SUSPENDED
-> #137 RESTORED_FROM_SUSPENDED
-> #137 SUSPENDED
-> #184 RESTORED_FROM_SUSPENDED
```

без повторного создания потомка из `#100`.

### `TicketUser`

После принятия решений добавить тесты на:

- допустимые переходы из `TicketUserStatus.SUSPENDED`;
- создание новой пары `Ticket + TicketUser`;
- новые ID обоих aggregates;
- сохранение cross-aggregate invariants;
- отсутствие копирования старой history;
- mapping нового начального статуса;
- relation через внутренние Ticket;
- повторное восстановление пользовательской заявки.

---

## 23. Итоговая модель

```text
Ticket
    отвечает только за собственный жизненный цикл

TicketUser
    отвечает за пользовательский жизненный цикл

TicketRelation
    отвечает за происхождение одного Ticket от другого

TicketService
    определяет, когда создание нового жизненного цикла допустимо
```

Основной сценарий:

```text
Client disabled
        |
        v
Ticket #100
... -> SUSPENDED
        |
        +----> CANCELLED

Client enabled
        |
        v
если #100 остаётся SUSPENDED
и ещё не имеет восстановленного потомка:
        |
        v
создаётся Ticket #137

RESTORED_FROM_SUSPENDED
        |
        v
новый жизненный цикл

ticket_relations:
#100 -> #137
RESTORED_FROM_SUSPENDED
```

История происхождения хранится отдельно от aggregates и может образовывать цепочки:

```text
#100 -> #137 -> #184 -> ...
```

Тот же механизм в дальнейшем используется для обычного копирования заявок без добавления полей происхождения в `Ticket` или таблицу `tickets`.
