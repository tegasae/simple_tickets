# Технический долг: терминальный `SUSPENDED` и восстановление заявки новым жизненным циклом

## Статус

**Требует реализации.**

## Контекст

Сейчас статус `SUSPENDED` используется при отключении связанных сущностей:

- `Client`;
- основного `User`;
- контактного пользователя.

Проблема текущей модели состоит в том, что из `SUSPENDED` разрешены обычные переходы в другие состояния.

Пример истории:

```text
CREATED
-> ACCEPTED
-> SUSPENDED
-> DEFERRED
-> ACCEPTED
-> SUSPENDED
-> CANCELLED
```

Чтобы проверить, был ли конкретный переход из `SUSPENDED` допустим в момент его выполнения, пришлось бы знать историческое состояние связанных `Client` / `User` / `Contact User`.

Текущее состояние связанных сущностей для этого недостаточно.

## Принятое решение

`SUSPENDED` становится **терминальным статусом**.

После перехода в `SUSPENDED` жизненный цикл конкретного `Ticket` считается завершённым.

Из `SUSPENDED` запрещены любые дальнейшие переходы:

```python
TicketStatus.SUSPENDED: frozenset()
```

Если причина приостановки устранена, старый `Ticket` не изменяется.

Вместо этого создаётся **новый `Ticket` с новым жизненным циклом**.

Новый Ticket:

- получает новый `ticket_id`;
- содержит ссылку на исходный Ticket;
- не копирует историю статусов исходного Ticket;
- начинается со специального статуса:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

## Новое поле `Ticket`

Добавить в `Ticket`:

```python
copy_from_ticket_id: int = 0
```

Семантика:

```text
copy_from_ticket_id == 0
    Ticket создан самостоятельно

copy_from_ticket_id > 0
    Ticket создан на основе другого Ticket
```

Поле делается общим, а не специфичным только для восстановления из `SUSPENDED`.

Это позволит в будущем использовать тот же механизм для обычного копирования заявок.

### Инварианты

```python
if self.copy_from_ticket_id < 0:
    raise ItemValidationError(
        "Copy-from ticket ID cannot be negative"
    )
```

Для `RESTORED_FROM_SUSPENDED` ссылка на исходный Ticket обязательна:

```python
if (
    initial_status is TicketStatus.RESTORED_FROM_SUSPENDED
    and self.copy_from_ticket_id <= 0
):
    raise ItemValidationError(
        "Restored ticket must reference source ticket"
    )
```

При этом в будущем допустимо:

```text
CREATED + copy_from_ticket_id > 0
```

для обычного копирования заявки.

## Новый статус

Добавить:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

Статус является **начальным статусом нового Ticket**, а не переходом старого Ticket.

По смыслу он находится рядом с:

```python
TicketStatus.CREATED
TicketStatus.CREATED_FROM_TICKET_USER
TicketStatus.RESTORED_FROM_SUSPENDED
```

Рекомендуется явно зафиксировать допустимые начальные статусы:

```python
INITIAL_TICKET_STATUSES: Final[frozenset[TicketStatus]] = frozenset({
    TicketStatus.CREATED,
    TicketStatus.CREATED_FROM_TICKET_USER,
    TicketStatus.RESTORED_FROM_SUSPENDED,
})
```

## Граф переходов

### `SUSPENDED`

Изменить текущий граф на:

```python
TicketStatus.SUSPENDED: frozenset()
```

### `RESTORED_FROM_SUSPENDED`

Так как это новый жизненный цикл, статус должен вести себя примерно как `CREATED`.

Предварительный вариант:

```python
TicketStatus.RESTORED_FROM_SUSPENDED: frozenset({
    TicketStatus.ACCEPTED,
    TicketStatus.REJECTED,
    TicketStatus.CANCELLED_BY_USER,
    TicketStatus.SUSPENDED,
})
```

Точный набор переходов необходимо подтвердить перед реализацией.

## `TicketStatusRule`

Добавить правило:

```python
TicketStatus.RESTORED_FROM_SUSPENDED: TicketStatusRule(
    can_change_data=True,
)
```

Статус:

- не является `user_action`;
- не требует исполнителя;
- не требует комментария;
- не содержит work data;
- разрешает изменение данных аналогично `CREATED`.

`TICKET_STATUS_RULES` продолжает описывать только внутренние свойства статуса.

## История статусов

История исходного `Ticket` **не копируется**.

Пример:

```text
Ticket #100

CREATED
-> ACCEPTED
-> ASSIGNED
-> SUSPENDED
```

После устранения причины блокировки создаётся:

```text
Ticket #137
copy_from_ticket_id = 100

RESTORED_FROM_SUSPENDED
-> ACCEPTED
-> ASSIGNED
-> ...
```

История `Ticket #100` остаётся неизменной.

История `Ticket #137` начинается с новой даты и нового статусного события.

Это исключает дублирование:

- `status_id`;
- `actor_employee_id`;
- `date_created`;
- комментариев;
- work data;
- других исторических записей.

## Цепочка происхождения

Возможна последовательная цепочка:

```text
Ticket #100
    |
    | restored
    v
Ticket #137
    |
    | suspended
    | restored
    v
Ticket #184
```

При этом:

```text
#137.copy_from_ticket_id = 100
#184.copy_from_ticket_id = 137
```

Отдельное поле `root_ticket_id` пока не требуется.

При необходимости корневая заявка может быть найдена проходом по `copy_from_ticket_id`.

## Операция восстановления

Восстановление не является методом старого Ticket вида:

```python
old_ticket.restore()
```

Потому что старый Ticket не изменяется.

Операция должна находиться в доменном `TicketService`, например:

```python
new_ticket = TicketService.restore_from_suspended(
    source_ticket=source_ticket,
    ...
)
```

Минимальная проверка:

```python
source_ticket.current_status is TicketStatus.SUSPENDED
```

Также перед созданием нового Ticket необходимо проверить, что причина приостановки устранена:

```text
Client enabled
User enabled, если user_id > 0
Contact User enabled, если contact_user_id > 0
```

После успешной проверки создаётся новый агрегат:

```python
Ticket.create_restored(
    copy_from_ticket_id=source_ticket.ticket_id,
    ...
)
```

с первым статусом:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

## Какие данные переносятся

В новый Ticket должны переноситься актуальные бизнес-данные исходной заявки, если это соответствует бизнес-правилам.

Предварительно:

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

Не переносятся как история:

```text
statuses
date_finished
накопленное work time
исторические назначения исполнителей
```

Отдельно требуется решить:

- переносится ли `planned_at`;
- переносится ли `department_id`;
- переносится ли рекомендация удалённой работы;
- переносится ли последний исполнитель;
- копируются ли обычные комментарии или остаются только в исходном Ticket.

## Изменение семантики `SUSPENDED`

После реализации:

```text
DEFERRED / PAUSED
    временная остановка текущего жизненного цикла

SUSPENDED
    окончание текущего жизненного цикла
    из-за внешнего состояния связанной сущности

RESTORED_FROM_SUSPENDED
    начало нового жизненного цикла после устранения причины
```

Таким образом, `SUSPENDED` больше не является временной паузой внутри того же Ticket.

## Проверка истории при rehydrate

После изменения графа история:

```text
... -> SUSPENDED -> любой другой статус
```

всегда является невалидной.

Для её обнаружения достаточно обычной проверки:

```python
next_status in TICKET_TRANSITIONS[current_status]
```

Историческое состояние `Client` / `User` / `Contact User` для проверки истории больше не требуется.

## `TicketTransitionContext`

После введения терминального `SUSPENDED` необходимость использовать `TicketTransitionContext` для обычных переходов существенно уменьшается.

Он может понадобиться для операций, зависящих от состояния связанных агрегатов, в частности:

```text
restore_from_suspended()
```

и при переводе активных заявок в `SUSPENDED` при отключении:

```text
Client
User
Contact User
```

Не требуется использовать исторический `TicketTransitionContext` для проверки уже сохранённой status history.

## Application layer и optimistic locking

При восстановлении application layer должен:

```text
load source Ticket
load Client
load User, если есть
load Contact User, если есть

проверить permissions

вызвать TicketService.restore_from_suspended(...)

save(new_ticket)

touch(source_ticket)
touch(Client)
touch(User)
touch(Contact User)

commit
```

`touch()` требуется для агрегатов, состояние которых участвовало в решении о создании восстановленной заявки.

Если один и тот же `User` одновременно является основным и контактным, его следует `touch()` только один раз.

## Старый Ticket

Операция восстановления:

- не удаляет старый Ticket;
- не изменяет его статус;
- не изменяет его историю;
- не удаляет комментарии;
- не изменяет дату завершения;
- не добавляет в его status history запись о восстановлении.

Связь существует только со стороны нового Ticket:

```text
new_ticket.copy_from_ticket_id = old_ticket.ticket_id
```

Обратную ссылку в старом Ticket пока не хранить.

## Отображение в UI

Для восстановленного Ticket желательно показывать:

```text
Восстановлена из заявки №100
```

с возможностью перейти к исходной заявке.

Для исходной `SUSPENDED` заявки в будущем можно вычислять список созданных на её основе заявок отдельным запросом:

```text
WHERE copy_from_ticket_id = source_ticket_id
```

Хранить список дочерних Ticket внутри агрегата не требуется.

## Открытые вопросы

### `TicketUser`

Для заявок, связанных с `TicketUser`, необходимо отдельно определить полный сценарий завершения и восстановления жизненного цикла.

Сейчас действует инвариант:

```text
Ticket.user_ticket_id == TicketUser.ticket_user_id
Ticket.client_id == TicketUser.client_id
Ticket.user_id == TicketUser.user_id
Ticket.contact_user_id == TicketUser.contact_user_id
```

Кроме того, при создании `TicketUser` внутренний `Ticket` создаётся сразу в той же транзакции.

Переход к терминальному `SUSPENDED` требует решить следующие вопросы.

#### 1. Должен ли `TicketUser.SUSPENDED` также стать терминальным

Если внутренний `Ticket.SUSPENDED` становится терминальным, необходимо решить, должен ли пользовательский агрегат вести себя симметрично:

```text
Ticket        -> SUSPENDED -> terminal
TicketUser    -> SUSPENDED -> terminal ?
```

Если `TicketUser` сможет выходить из `SUSPENDED`, а внутренний `Ticket` — нет, жизненные циклы связанных агрегатов начнут расходиться.

Нужно определить:

- становится ли `TicketUserStatus.SUSPENDED` терминальным;
- считается ли такой `TicketUser` закрытым;
- устанавливается ли `date_closed`;
- должен ли `is_closed` быть `True` для `SUSPENDED`.

#### 2. Что создавать при восстановлении связанной заявки

Если исходный `Ticket` имеет:

```text
user_ticket_id > 0
```

необходимо определить, создаётся ли при восстановлении новая пара:

```text
old Ticket      -> terminal SUSPENDED
old TicketUser  -> terminal SUSPENDED

            restore

new Ticket
new TicketUser
```

Предварительно наиболее согласованная модель — создавать **оба новых агрегата в одной транзакции**, аналогично первоначальному созданию `TicketUser`.

Но это решение требуется зафиксировать отдельно.

#### 3. Начальный статус нового `TicketUser`

Для нового `Ticket` вводится:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

Необходимо решить, какой статус получает новый `TicketUser`.

Варианты:

```text
TicketUserStatus.CREATED
```

или отдельный:

```text
TicketUserStatus.RESTORED_FROM_SUSPENDED
```

Если вводится новый пользовательский статус, потребуется:

- добавить его в `TicketUserStatus`;
- добавить его правила;
- разрешить его как начальный статус;
- определить переходы;
- обновить mapping `Ticket -> TicketUser`.

#### 4. Mapping нового статуса

Если внутренний Ticket начинается с:

```python
TicketStatus.RESTORED_FROM_SUSPENDED
```

необходимо определить его соответствие пользовательскому статусу.

Например:

```text
RESTORED_FROM_SUSPENDED -> CREATED
```

либо:

```text
RESTORED_FROM_SUSPENDED -> RESTORED_FROM_SUSPENDED
```

Это решение должно быть явным, а не возникать как побочный эффект существующего mapping.

#### 5. Нужен ли `copy_from_ticket_user_id`

Для `Ticket` вводится:

```python
copy_from_ticket_id
```

Нужно решить, хранить ли аналогичную связь непосредственно в `TicketUser`:

```python
copy_from_ticket_user_id: int = 0
```

Варианты:

1. Хранить lineage только в `Ticket`, а исходный `TicketUser` получать через исходный `Ticket.user_ticket_id`.
2. Хранить lineage независимо в обоих агрегатах.

Второй вариант делает историю происхождения `TicketUser` самодостаточной, но добавляет ещё один cross-aggregate invariant.

#### 6. Инварианты новой пары

Если при восстановлении создаются новый `Ticket` и новый `TicketUser`, необходимо обеспечить:

```text
new_ticket.user_ticket_id == new_ticket_user.ticket_user_id

new_ticket.client_id == new_ticket_user.client_id
new_ticket.user_id == new_ticket_user.user_id
new_ticket.contact_user_id == new_ticket_user.contact_user_id
```

Если вводится `copy_from_ticket_user_id`, дополнительно необходимо решить связь происхождения:

```text
new_ticket.copy_from_ticket_id == old_ticket.ticket_id
new_ticket_user.copy_from_ticket_user_id == old_ticket_user.ticket_user_id
```

#### 7. Состояние обоих исходных агрегатов перед восстановлением

Необходимо решить, достаточно ли проверки:

```text
source Ticket == SUSPENDED
```

или для связанной заявки обязательно также:

```text
source TicketUser == SUSPENDED
```

Предпочтительно не восстанавливать пару, если состояния двух агрегатов расходятся, а считать такое состояние нарушением согласованности данных.

#### 8. Какие данные копируются в новый `TicketUser`

`TicketUser` имеет собственные данные, в том числе независимое поле `description`.

Необходимо отдельно определить перенос:

```text
client_id
user_id
contact_user_id
text_of_ticket
description
urgency_level
```

Особенно важно помнить:

```text
Ticket.description
```

и:

```text
TicketUser.description
```

независимы и не должны синхронизироваться между собой автоматически.

#### 9. Что делать с комментариями `TicketUser`

Историю статусов решено не копировать.

Необходимо отдельно определить судьбу обычных комментариев:

- остаются только в старом `TicketUser`;
- копируются в новый;
- в новом создаётся только служебная ссылка на предыдущую заявку.

По умолчанию предпочтительнее не копировать исторические комментарии, но решение пока не принято.

#### 10. Новый номер пользовательской заявки

Если создаётся новый `TicketUser`, он получает новый:

```text
ticket_user_id
```

Нужно подтвердить, что пользователь действительно видит это как **новую заявку / новый жизненный цикл**, а не как продолжение под старым номером.

В интерфейсе можно показывать связь:

```text
Восстановлена из заявки №...
```

#### 11. Кто имеет право инициировать восстановление

Нужно определить, кто может создать новый жизненный цикл:

- только Admin;
- User;
- оба при соответствующих permissions.

Это особенно важно для пользовательской заявки, поскольку старый `TicketUser` уже терминальный и не должен изменяться.

#### 12. Повторное отключение после восстановления

Необходимо проверить полный цикл:

```text
Ticket #100 / TicketUser #500
        -> SUSPENDED

restore

Ticket #137 / TicketUser #620
        -> RESTORED_FROM_SUSPENDED / <новый user-status>
        -> работа
        -> SUSPENDED

restore again

Ticket #184 / TicketUser #711
        -> новый жизненный цикл
```

Каждая пара должна оставаться отдельной исторической сущностью.

#### 13. Можно ли восстановить одну `SUSPENDED` заявку несколько раз

Нужно решить, допустимо ли:

```text
Ticket #100 SUSPENDED
    -> Ticket #137
    -> Ticket #138
```

то есть несколько независимых потомков одного source Ticket.

Если это запрещено, потребуется правило:

```text
у SUSPENDED Ticket может быть только одна восстановленная заявка
```

и соответствующая проверка на уровне сервиса/repository.

То же решение должно быть согласовано для `TicketUser`.

#### 14. Несвязанные Ticket

Для:

```text
ticket.user_ticket_id == 0
```

восстановление может создавать только новый внутренний `Ticket`.

Необходимо зафиксировать, что `TicketUser` в таком случае автоматически не создаётся.

### Обычное копирование

Поле:

```python
copy_from_ticket_id
```

сразу проектируется как общее.

Позднее необходимо отдельно определить операцию:

```python
copy_ticket(...)
```

для обычных Ticket, не связанных с `SUSPENDED`.

## Необходимые тесты

### Граф переходов

Проверить:

```text
SUSPENDED -> ACCEPTED      запрещено
SUSPENDED -> DEFERRED      запрещено
SUSPENDED -> CANCELLED     запрещено
SUSPENDED -> любой статус  запрещено
```

### История

`rehydrate()` должен отвергать:

```text
CREATED
-> ACCEPTED
-> SUSPENDED
-> DEFERRED
```

и:

```text
CREATED
-> ACCEPTED
-> SUSPENDED
-> CANCELLED
```

### Восстановление

Проверить, что `RESTORED_FROM_SUSPENDED` может быть первым статусом нового Ticket.

Проверить обязательность:

```text
copy_from_ticket_id > 0
```

для такого Ticket.

### Источник восстановления

Запрещено восстанавливать Ticket, если его текущий статус не:

```python
TicketStatus.SUSPENDED
```

### Связанные сущности

Запрещено восстановление, если:

```text
Client disabled
User disabled
Contact User disabled
```

если соответствующая сущность существует.

### История исходного Ticket

После восстановления исходный Ticket должен остаться полностью неизменным.

### Новый Ticket

Новый Ticket должен:

- получить новый `ticket_id`;
- получить `copy_from_ticket_id == source.ticket_id`;
- иметь первую status record `RESTORED_FROM_SUSPENDED`;
- не содержать status history исходного Ticket.

### `TicketUser`

После принятия решений по пользовательской части добавить тесты как минимум на:

- терминальность `TicketUserStatus.SUSPENDED`, если она будет принята;
- создание новой пары `Ticket + TicketUser` в одной транзакции;
- новые `ticket_id` и `ticket_user_id`;
- сохранение cross-aggregate invariants новой пары;
- отсутствие копирования старой status history;
- корректный начальный статус нового `TicketUser`;
- корректный mapping `RESTORED_FROM_SUSPENDED`;
- запрет восстановления при рассогласованных статусах исходных `Ticket` и `TicketUser`;
- поведение `copy_from_ticket_user_id`, если поле будет введено;
- повторное восстановление после нового `SUSPENDED`;
- запрет нескольких потомков одного source Ticket, если такое ограничение будет принято.

## Результат

После реализации модель должна обеспечивать:

```text
SUSPENDED = terminal
```

и:

```text
устранение причины SUSPENDED
        |
        v
создание нового Ticket
        |
        v
RESTORED_FROM_SUSPENDED
        |
        v
новый независимый жизненный цикл
```

Связь между жизненными циклами хранится через:

```python
copy_from_ticket_id
```

При этом старый Ticket остаётся неизменяемой исторической записью своего завершённого жизненного цикла.
