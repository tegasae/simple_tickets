## Technical debt: пересмотреть границы Ticket domain services и убрать дублирование

### Текущее состояние

Workflow `Ticket` обслуживают три domain service:

```text
TicketManagementService
TicketExecutionService
TicketReviewService
```

Текущее смысловое разделение:

```text
TicketManagementService
    управленческие действия

TicketExecutionService
    действия исполнителя

TicketReviewService
    действия сотрудника, проверяющего результат
```

Само это разделение допустимо и может быть полезным.

Проблема не в количестве классов как таковом, а в том, что часть методов различается только принадлежностью к сервису, но выполняет одно и то же domain action.

---

## Пример дублирования: DEFERRED

`TicketManagementService.defer()` создаёт:

```python
TicketStatusRecord(
    actor_employee_id=actor_employee_id,
    status=TicketStatus.DEFERRED,
    comment=comment,
)
```

и вызывает:

```python
ticket.append_status(record)
```

`TicketReviewService.return_to_deferred()` создаёт фактически такую же record:

```python
TicketStatusRecord(
    actor_employee_id=actor_employee_id,
    status=TicketStatus.DEFERRED,
    comment=comment,
)
```

Единственное дополнительное правило `TicketReviewService`:

```text
current_status == READY_FOR_REVIEW
```

Но допустимость:

```text
READY_FOR_REVIEW → DEFERRED
```

уже является частью `TicketState` и проверяется самим `Ticket.append_status()`.

Следовательно отдельный domain operation:

```text
return_to_deferred()
```

не несёт дополнительной domain semantics.

---

## Аналогичное дублирование

Необходимо пересмотреть пары:

```text
TicketManagementService.defer()
TicketReviewService.return_to_deferred()

TicketManagementService.schedule()
TicketReviewService.return_to_scheduled()

TicketManagementService.assign()
TicketReviewService.return_to_assigned()

TicketManagementService.ready_to_work()
TicketReviewService.return_to_ready_to_work()
```

Для первых трёх на текущий момент отдельная review-операция выглядит избыточной.

---

## Основной принцип

Domain service должен существовать не потому, что операция выполняется **из определённого статуса**, а потому, что она представляет самостоятельное бизнес-действие или требует специфических правил.

То есть:

```text
одинаковый resulting status
+
одинаковый payload
+
одинаковые actor semantics
+
нет дополнительных business invariants
```

→ один domain operation.

Не требуется создавать:

```text
return_to_X()
```

только потому, что исходным состоянием является:

```text
READY_FOR_REVIEW
```

---

## Что действительно является отдельной review operation

Некоторые действия `TicketReviewService` имеют собственную семантику и должны остаться отдельными.

### confirm_execution

```text
READY_FOR_REVIEW → EXECUTED
```

Это не просто переход состояния.

Он означает:

```text
другой сотрудник проверил результат работы
и подтвердил выполнение заявки.
```

Кроме того, reviewer не должен совпадать с executor.

Поэтому:

```python
confirm_execution(...)
```

является самостоятельным domain action.

---

### return_to_work

```text
READY_FOR_REVIEW → AT_WORK
```

также имеет специальную семантику:

```text
reviewer отклонил результат
и вернул заявку тому же executor на доработку.
```

При этом новый `AT_WORK` должен сохранить текущего executor.

Это отличается от обычного:

```text
ASSIGNED / READY_TO_WORK → AT_WORK
```

где действие выполняет сам текущий executor.

Следовательно:

```python
TicketExecutionService.take_to_work(...)
```

и:

```python
TicketReviewService.return_to_work(...)
```

должны оставаться разными domain operations.

---

## DEFERRED

Для:

```text
READY_FOR_REVIEW → DEFERRED
```

специальной review semantics сейчас нет.

Использовать обычный:

```python
TicketManagementService.defer(...)
```

Допустимость перехода определяет:

```text
TicketState
+
Ticket.append_status()
```

Удалить:

```python
TicketReviewService.return_to_deferred()
```

---

## ASSIGNED

Если reviewer решает, что требуется новый или повторно назначенный executor:

```text
READY_FOR_REVIEW → ASSIGNED
```

это с точки зрения состояния является обычным назначением исполнителя.

Если специальных review-specific правил нет, использовать:

```python
TicketManagementService.assign(...)
```

Удалить:

```python
TicketReviewService.return_to_assigned()
```

Если позднее появится специфическое правило именно для возврата с review, тогда отдельную операцию можно вернуть.

---

## SCHEDULED

Аналогично:

```text
READY_FOR_REVIEW → SCHEDULED
```

означает новое планирование.

Если операция использует обычный payload:

```text
planned_start_at
planned_finish_at
```

и специальных правил review нет, использовать:

```python
TicketManagementService.schedule(...)
```

Удалить:

```python
TicketReviewService.return_to_scheduled()
```

---

## READY_TO_WORK

Пару:

```text
TicketManagementService.ready_to_work()
TicketReviewService.return_to_ready_to_work()
```

не объединять автоматически.

Семантика `READY_TO_WORK` требует отдельного пересмотра.

Уже принято правило:

```text
SCHEDULED → READY_TO_WORK
```

означает:

```text
назначить executor к существующему plan
```

и не должно одновременно менять:

```text
planned_start_at
planned_finish_at
```

В других переходах в `READY_TO_WORK` семантика может отличаться.

Поэтому окончательная форма domain operation для `READY_TO_WORK` должна быть определена отдельно.

---

## Предлагаемая структура

Ориентировочно:

```text
TicketManagementService
    accept
    reject
    defer
    schedule
    assign
    ready_to_work
    cancel
    handle_client_disabled

TicketExecutionService
    take_to_work
    pause_work
    resume_work
    submit_for_review
    record_completed_work_for_review

TicketReviewService
    confirm_execution
    return_to_work
    [операции только при наличии действительно
     специфической review semantics]
```

---

## Ответственность Ticket

`Ticket` остаётся окончательным защитником локального workflow.

Именно aggregate должен проверять:

```text
- terminal state;
- допустимость current_status → new_status;
- payload status record;
- transition-specific invariants;
- историю при rehydrate.
```

Domain service не должен дублировать весь `TicketState`.

Он должен описывать конкретное бизнес-действие и сформировать корректную `TicketStatusRecord`.

---

## Требуемые изменения

```text
- удалить TicketReviewService.return_to_deferred();
- использовать TicketManagementService.defer();

- удалить TicketReviewService.return_to_assigned();
- использовать TicketManagementService.assign();

- удалить TicketReviewService.return_to_scheduled();
- использовать TicketManagementService.schedule();

- отдельно пересмотреть ready_to_work /
  return_to_ready_to_work;

- оставить TicketReviewService.confirm_execution();

- оставить TicketReviewService.return_to_work();

- проверить reviewer != current executor
  для подтверждения результата;

- обновить domain tests;

- проверить rehydrate validation после изменений;

- обновить workflow documentation.
```

### Дополнительное связанное изменение

Отдельно уже зафиксировано:

```text
record_completed_work_for_review
```

должен допускать только:

```text
ASSIGNED
READY_TO_WORK
```

а:

```text
SCHEDULED → READY_FOR_REVIEW
```

должен быть запрещён.

Для ретроспективного завершения executor берётся из текущего состояния Ticket и не должен повторно передаваться вызывающим кодом.

---

### Статус

```text
Technical debt.

Сохранять три domain service можно,
но границы должны определяться бизнес-смыслом операций,
а не механическим делением workflow по стадиям.

Дублирующие операции необходимо удалить.
```


