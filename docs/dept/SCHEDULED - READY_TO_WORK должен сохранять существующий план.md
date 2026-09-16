## SCHEDULED → READY_TO_WORK должен сохранять существующий план

### Проблема

Сейчас переход:

```text
SCHEDULED → READY_TO_WORK
```

может трактоваться как операция, в которой одновременно:

* назначается исполнитель;
* задаётся или изменяется `planned_start_at`;
* задаётся или изменяется `planned_finish_at`.

Это смешивает два разных бизнес-события:

```text
перепланирование заявки
```

и:

```text
назначение исполнителя к уже существующему плану
```

Из-за этого история Ticket становится менее однозначной.

### Принятое решение

Переход:

```text
SCHEDULED → READY_TO_WORK
```

должен означать только:

> к уже существующему плану назначен исполнитель.

План при этом не изменяется.

Пример:

```text
SCHEDULED
    executor_id = 0
    planned_start_at  = 2026-09-20 10:00
    planned_finish_at = 2026-09-20 12:00

        ↓ назначен executor_id = 15

READY_TO_WORK
    executor_id = 15
    planned_start_at  = 2026-09-20 10:00
    planned_finish_at = 2026-09-20 12:00
```

### Изменение плана

Если необходимо изменить план, это должно быть отдельным business event:

```text
SCHEDULED → SCHEDULED
```

После перепланирования исполнитель назначается отдельным переходом:

```text
SCHEDULED → READY_TO_WORK
```

Таким образом:

```text
SCHEDULED → SCHEDULED
    = перепланирование

SCHEDULED → READY_TO_WORK
    = назначение исполнителя к существующему плану
```

### Изменения в domain service

Операция перехода из `SCHEDULED` в `READY_TO_WORK` не должна принимать новые:

```text
planned_start_at
planned_finish_at
```

Она должна принимать только данные назначения, например:

```python
executor_id
actor_employee_id
comment
```

План необходимо брать из текущей `SCHEDULED` status record:

```python
current = ticket.current_status_record()

record = TicketStatusRecord(
    actor_employee_id=actor_employee_id,
    status=TicketStatus.READY_TO_WORK,
    executor_id=executor_id,
    planned_start_at=current.planned_start_at,
    planned_finish_at=current.planned_finish_at,
    comment=comment,
)
```

### Инвариант aggregate

Ограничение необходимо защищать не только в application/domain service, но и внутри `Ticket`.

Для перехода:

```text
SCHEDULED → READY_TO_WORK
```

должно выполняться:

```python
new_record.planned_start_at == current_record.planned_start_at

new_record.planned_finish_at == current_record.planned_finish_at
```

При нарушении:

```python
raise DomainOperationError(...)
```

Это предотвращает изменение плана через другой use case или будущий domain service.

### Разделение ответственности

`TicketStatusRecord` проверяет корректность собственного payload:

```text
READY_TO_WORK требует executor_id
READY_TO_WORK требует planned_start_at
```

`Ticket` проверяет transition invariant:

```text
при SCHEDULED → READY_TO_WORK
существующий план должен быть сохранён
```

`TicketManagementService` реализует бизнес-операцию:

```text
назначить исполнителя к уже существующему плану
```

### Rehydrate

Историческая проверка при `Ticket.rehydrate()` также должна обнаруживать persisted history, нарушающую это правило.

Например, следующая история должна считаться некорректной:

```text
SCHEDULED
    planned_start_at = 10:00

READY_TO_WORK
    planned_start_at = 14:00
```

Такое изменение должно было быть представлено как:

```text
SCHEDULED(10:00)
    ↓
SCHEDULED(14:00)
    ↓
READY_TO_WORK(14:00)
```

### Требуемые тесты

Добавить domain tests как минимум для сценариев:

```text
SCHEDULED → READY_TO_WORK
    сохраняет planned_start_at / planned_finish_at

SCHEDULED → READY_TO_WORK
    с изменённым plan запрещён

SCHEDULED → SCHEDULED
    позволяет изменить plan

SCHEDULED(new plan) → READY_TO_WORK
    сохраняет новый plan

rehydrate()
    отвергает историю, где
    SCHEDULED → READY_TO_WORK изменяет plan
```

### Статус

```text
Technical debt.
Семантика перехода согласована.
Требуется изменить domain service, aggregate validation и tests.
```
