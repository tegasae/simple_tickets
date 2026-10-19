# Concurrency control для операций Client / Ticket

## 1. Контекст

В системе существуют операции над `Ticket` и `TicketUser`, допустимость которых зависит от текущего состояния `Client`.

В частности, некоторые операции разрешены только при:

```python
client.enabled is True
```

Примеры:

- создание внутренней `Ticket`;
- создание `TicketUser` пользователем и связанной внутренней `Ticket`;
- возможные workflow-операции, которые недопустимы для отключённого `Client`;
- отключение самого `Client`, при котором необходимо обработать связанные заявки.

При последовательном выполнении обычной проверки:

```python
client = uow.clients.get(client_id)

TicketPolicy.ensure_client_enabled(client)
```

достаточно.

Однако при конкурентных транзакциях между моментом чтения `Client` и `COMMIT` его состояние может измениться.

---

# 2. Исходная проблема

Рассмотрим две транзакции.

## T1 — создание Ticket

```text
T1:
    прочитать Client

    Client.enabled == True

    создать Ticket
```

## T2 — отключение Client

```text
T2:
    прочитать Client

    отключить Client

    обработать существующие Ticket

    COMMIT
```

Возможна последовательность:

```text
T1: Client прочитан как enabled=True

T2: Client отключён
T2: существующие Ticket обработаны
T2: COMMIT

T1: INSERT Ticket
T1: COMMIT
```

После этого появляется новая `Ticket`, которая не существовала во время обработки заявок при отключении `Client`.

Получается состояние:

```text
Client.enabled == False

+

новая Ticket,
которая избежала workflow-обработки,
выполняемой при отключении Client
```

Это нарушение cross-aggregate invariant.

---

# 3. Бизнес-инвариант

Если операция допустима только для активного `Client`, она не должна успешно завершиться на основании устаревшего состояния `Client`.

То есть если операция проверила:

```text
Client.enabled == True
```

а до её завершения другая транзакция изменила `Client`, первая транзакция должна либо:

1. завершиться раньше изменения `Client`;

либо:

2. обнаружить concurrency conflict и откатиться.

В результате не должно возникать состояния:

```text
Client отключён,
но новая Ticket появилась уже после обработки
существовавших заявок при disable(Client).
```

---

# 4. Требование к concurrency mechanism

Желательно, чтобы основной механизм не зависел от конкретной СУБД.

В частности, application/domain layer не должен непосредственно зависеть от:

```text
SELECT ... FOR UPDATE
BEGIN IMMEDIATE
PostgreSQL advisory locks
SQLite locking semantics
конкретного transaction isolation level
```

SQLite пока используется преимущественно как development database.

В дальнейшем persistence может быть заменён, например, на:

```text
PostgreSQL
SQLAlchemy
прямой SQL
```

Поэтому предпочтительно иметь concurrency protocol, который можно одинаково реализовать поверх разных persistence technologies.

---

# 5. Вариант 1. Optimistic locking через Client.version

Это текущий предпочтительный вариант.

В проекте уже существует optimistic locking агрегатов через поле:

```python
version
```

Поэтому `Client` можно использовать не только как aggregate, но и как concurrency guard для операций, результат которых зависит от его состояния.

---

## 5.1. Начало операции

Application service загружает `Client`:

```python
client = uow.clients.get(client_id)
```

Например:

```text
enabled = True
version = 10
```

После этого проверяется бизнес-условие:

```python
TicketPolicy.ensure_client_enabled(client)
```

И выполняется операция:

```python
ticket = Ticket.create(...)
uow.tickets.save(ticket)
```

Но перед `COMMIT` необходимо подтвердить, что `Client` с момента чтения не изменился.

---

## 5.2. touch(Client)

Для этого repository может иметь:

```python
clients.touch(client)
```

Смысл метода:

> атомарно подтвердить, что версия `Client`, прочитанная в начале операции, всё ещё актуальна, и продвинуть concurrency version.

Концептуально:

```sql
UPDATE clients
SET version = version + 1
WHERE client_id = :client_id
  AND version = :expected_version
```

Если:

```text
rowcount == 1
```

значит версия всё ещё была актуальна.

Если:

```text
rowcount == 0
```

значит `Client` уже был изменён другой транзакцией.

Возникает:

```python
OptimisticLockError
```

и вся Unit of Work откатывается.

---

# 6. Пример: disable(Client) завершился первым

Начальное состояние:

```text
Client
enabled = True
version = 10
```

Обе транзакции прочитали:

```text
enabled = True
version = 10
```

## T2 отключает Client

```text
T2:

client.disable()

save(client)

version:
10 -> 11

COMMIT
```

После этого T1 уже успела создать `Ticket` внутри своей ещё незавершённой транзакции:

```text
T1:

INSERT Ticket
```

Но затем делает:

```text
touch(Client)

expected version = 10
```

В БД уже:

```text
version = 11
```

Поэтому:

```text
UPDATE ...
WHERE version = 10

0 rows
```

Следствие:

```text
OptimisticLockError
ROLLBACK
```

Откатывается не только `touch`, но и ранее выполненный:

```text
INSERT Ticket
```

Итог:

```text
Client.enabled == False

новая Ticket отсутствует
```

---

# 7. Обратный порядок: создание Ticket завершилось первым

Исходно:

```text
Client.version = 10
```

T1:

```text
прочитала Client version=10

создала Ticket

touch(Client)

10 -> 11

COMMIT
```

T2 ранее также прочитала:

```text
Client.version = 10
```

Теперь T2 пытается сохранить отключение:

```sql
UPDATE clients
...
WHERE client_id = ...
  AND version = 10
```

Но актуальная версия уже:

```text
11
```

Получаем:

```text
0 rows
OptimisticLockError
ROLLBACK
```

При повторном выполнении операции отключения:

```text
Client.version = 11
```

и новая `Ticket` уже существует.

Поэтому она попадёт в обычную обработку:

```text
disable Client
+
обработка всех связанных Ticket
```

И снова получается корректное состояние.

---

# 8. Важное различие: save(Client) и touch(Client)

`touch()` нужен не всегда.

Если операция действительно меняет `Client`, обычный:

```python
uow.clients.save(client)
```

уже выполняет optimistic locking.

Поэтому:

```text
Client изменяется
    -> save(client)

Client не изменяется,
но результат операции зависит от Client
    -> touch(client)
```

Например, при:

```python
client.disable()
```

не нужно делать:

```python
uow.clients.save(client)
uow.clients.touch(client)
```

Это было бы двойным concurrency update.

Достаточно:

```python
uow.clients.save(client)
```

---

# 9. Пример create Ticket

Пример application workflow:

```python
client = uow.clients.get(client_id)

TicketPolicy.ensure_client_enabled(client)

ticket = Ticket.create(
    client_id=client_id,
    ...
)

uow.tickets.save(ticket)

uow.clients.touch(client)

uow.commit()
```

Логика:

```text
READ Client

check Client.enabled

create Ticket

save Ticket

optimistic validation of Client

COMMIT
```

Если optimistic validation не проходит:

```text
ROLLBACK всей транзакции
```

---

# 10. Создание TicketUser + Ticket

При создании заявки пользователем схема аналогична.

```text
1. загрузить Client
2. проверить Client.enabled
3. создать TicketUser
4. сохранить TicketUser
5. получить TicketUser.ticket_id
6. создать связанную Ticket
7. сохранить Ticket
8. touch(Client)
9. COMMIT
```

Критически важно:

```text
TicketUser
Ticket
Client.touch
```

должны выполняться внутри **одной Unit of Work / одной DB transaction**.

Иначе optimistic guard не защищает всю операцию атомарно.

---

# 11. Недостаток Client.version как общего guard

Есть важное следствие.

Рассмотрим две совершенно допустимые операции:

```text
T1: создать Ticket A для Client #15
T2: создать Ticket B для Client #15
```

Обе читают:

```text
Client.version = 10
```

T1 делает:

```text
touch:
10 -> 11
```

T2 затем пытается:

```text
touch:
expected=10
```

и получает:

```text
OptimisticLockError
```

Хотя между Ticket A и Ticket B бизнес-конфликта как такового нет.

Таким образом `Client` превращается в **точку сериализации операций**, зависящих от его состояния.

При текущем предполагаемом объёме нагрузки это приемлемо.

Одна из транзакций просто должна быть повторена.

---

# 12. Вариант 2. Pessimistic locking Client

Альтернативой является блокировка `Client` на всё время операции.

Например, в PostgreSQL:

```sql
SELECT *
FROM clients
WHERE client_id = :client_id
FOR UPDATE
```

После этого конкурирующая транзакция, пытающаяся получить такой же lock, будет ждать.

---

## 12.1. Создание Ticket завершается первым

```text
T1:
    lock Client
    enabled=True

    create Ticket

    COMMIT
    lock released
```

T2 ждёт.

После завершения T1:

```text
T2:
    получает lock

    disable Client

    теперь уже видит созданную Ticket

    обрабатывает её

    COMMIT
```

---

## 12.2. Disable Client завершается первым

```text
T2:
    lock Client

    disable

    process Tickets

    COMMIT
```

T1 ждёт.

После освобождения lock:

```text
T1:
    читает Client

    enabled=False

    создание Ticket запрещается
```

Оба порядка дают корректное состояние.

---

# 13. Преимущества pessimistic locking

Пессимистичная блокировка очень естественно выражает этот invariant:

> пока операция принимает решение на основании состояния