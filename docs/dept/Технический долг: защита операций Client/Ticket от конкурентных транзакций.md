# Технический долг: защита операций Client/Ticket от конкурентных транзакций

## Проблема

Существует race condition между операциями, состояние которых зависит от `Client.enabled`.

Пример:

```text
T1: начинается создание Ticket для Client
T1: Client прочитан как enabled=True

T2: начинается отключение Client
T2: Client переводится в enabled=False
T2: связанные Ticket переводятся в соответствующее состояние
T2: COMMIT

T1: создаёт Ticket
T1: COMMIT
```

В результате после завершения обеих транзакций потенциально может существовать новая активная Ticket для уже отключённого Client.

Аналогичная проблема возможна не только при создании Ticket, но и для других операций, которые принимают решение на основании того, что Client остаётся активным.

## Бизнес-инвариант

Операция, разрешённая только для активного Client, не должна успешно завершаться, если Client был изменён другой транзакцией после проверки его состояния.

Например:

```text
Client.enabled == False

=> новая активная Ticket не должна появиться.
```

При отключении Client уже существующие Ticket обрабатываются согласно текущей workflow-policy.

## Требование к решению

Решение не должно зависеть от особенностей конкретной СУБД.

Нежелательно делать application/domain layer зависимым от механизмов вроде:

```text
SELECT ... FOR UPDATE
BEGIN IMMEDIATE
PostgreSQL advisory locks
SQLite locking semantics
конкретного transaction isolation level
```

В дальнейшем SQLite рассматривается преимущественно как development DB. Persistence может быть заменён, например, на PostgreSQL через SQLAlchemy или прямой SQL.

## Предлагаемое решение

Использовать существующий механизм optimistic locking через `Client.version`.

`Client` в данном случае выступает не только как aggregate, но и как concurrency guard для операций, результат которых зависит от его состояния.

При начале операции:

```python
client = uow.clients.get(client_id)

TicketPolicy.ensure_client_enabled(client)
```

операция запоминает текущую версию Client:

```text
enabled = True
version = N
```

Перед успешным завершением транзакции необходимо атомарно подтвердить, что Client с момента проверки не изменился.

Концептуально:

```sql
UPDATE clients
SET version = version + 1
WHERE client_id = :client_id
  AND version = :expected_version
```

Если изменена одна строка:

```text
Client не изменялся конкурентной транзакцией.
Операция может быть закоммичена.
```

Если изменено `0 rows`:

```text
Client уже был изменён другой транзакцией.
```

Должен возникнуть:

```python
OptimisticLockError
```

и вся Unit of Work должна быть откатана.

## Пример: Client отключился первым

Исходное состояние:

```text
Client
enabled = True
version = 10
```

Обе транзакции читают:

```text
enabled=True
version=10
```

Транзакция отключения Client:

```text
T2:

client.disable()

enabled = False
version 10 -> 11

COMMIT
```

Транзакция создания Ticket пытается подтвердить прочитанную версию:

```text
T1:

INSERT Ticket

UPDATE Client
WHERE version = 10
```

Но текущая версия уже:

```text
version = 11
```

Поэтому:

```text
0 rows updated
-> OptimisticLockError
-> ROLLBACK
```

Созданная Ticket также откатывается.

Итог:

```text
Client disabled
новая Ticket отсутствует
```

## Обратный порядок

Если первой завершается транзакция создания Ticket:

```text
T1:

Client version = 10
создание Ticket

Client version 10 -> 11

COMMIT
```

Транзакция отключения Client, которая ранее прочитала `version=10`, получает optimistic conflict:

```text
T2:

UPDATE Client
WHERE version = 10

0 rows updated
-> OptimisticLockError
-> ROLLBACK
```

После повторного выполнения `disable(Client)` она читает уже:

```text
Client version = 11
+
новую Ticket
```

и новая Ticket попадает в обычную обработку отключения Client.

Таким образом обе допустимые последовательности приводят к корректному состоянию системы.

## Возможный repository contract

Не следует вводить методы с названиями:

```python
get_for_update()
lock()
```

поскольку они описывают конкретный способ реализации concurrency.

Возможный общий repository-метод:

```python
clients.touch(client)
```

Смысл:

> подтвердить, что текущая версия Client всё ещё актуальна, и изменить его concurrency version.

`touch()` не является бизнес-изменением Client.

Другой вариант — скрыть эту операцию внутри более общего механизма Unit of Work/repository concurrency control.

Окончательное имя API следует определить при реализации.

## Где потребуется такой контроль

Как минимум:

```text
- создание внутренней Ticket;
- создание TicketUser и связанной внутренней Ticket;
- отключение Client.
```

Дополнительно необходимо проверить операции, которые могут перевести Ticket в состояние, недопустимое для отключённого Client.

Если операция принимает решение на основании:

```text
Client.enabled == True
```

она должна участвовать в том же optimistic concurrency protocol.

## Что уже есть

В проекте уже используется optimistic locking для агрегатов через `version`.

Поэтому желательно не вводить второй независимый механизм concurrency control, а расширить существующий подход на cross-aggregate invariants.

## Требуемые тесты

Необходимо добавить integration/concurrency test с двумя независимыми Unit of Work / DB connections.

Основной сценарий:

```text
T1 — создание Ticket
T2 — disable Client
```

Проверять оба возможных порядка завершения транзакций.

После разрешения конфликта должен выполняться инвариант:

```text
у disabled Client не появляется новая Ticket
в состоянии, которое policy отключения должна была изменить.
```

Отдельно проверить создание TicketUser пользователем.

## Статус

```text
Technical debt
Не реализовано.
```

Текущие проверки `Client.enabled` корректны для последовательного выполнения операций, но сами по себе не гарантируют сохранение cross-aggregate инварианта при конкурентных транзакциях.
