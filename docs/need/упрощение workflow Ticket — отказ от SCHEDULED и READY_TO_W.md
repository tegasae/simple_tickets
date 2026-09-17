## Резюме

Мы пришли к выводу, что состояния:

```text
SCHEDULED
READY_TO_WORK
```

не должны быть самостоятельными стадиями жизненного цикла `Ticket`.

Они возникли как комбинации двух независимых признаков:

```text
есть ли executor
есть ли planned_start_at / planned_finish_at
```

Текущая модель фактически кодирует это так:

```text
ACCEPTED
    executor = нет
    plan = нет

SCHEDULED
    executor = нет
    plan = есть

ASSIGNED
    executor = есть
    plan = нет

READY_TO_WORK
    executor = есть
    plan = есть
```

Из-за этого workflow получается сложнее, чем сам бизнес-процесс.

---

### 1. SCHEDULED удаляется из status workflow

Если `SCHEDULED` означает только:

```text
у Ticket задано планируемое время
```

то это не самостоятельный status.

План должен храниться непосредственно в `Ticket`:

```text
planned_start_at
planned_finish_at
```

Изменение плана само по себе не меняет workflow status.

Например:

```text
ACCEPTED
    plan = None

set_plan(...)

ACCEPTED
    planned_start_at = ...
    planned_finish_at = ...
```

Или:

```text
ASSIGNED executor=25

set_plan(...)

ASSIGNED executor=25
planned_start_at = ...
planned_finish_at = ...
```

Таким образом, планирование становится отдельной характеристикой `Ticket`, независимой от workflow.

---

### 2. READY_TO_WORK также удаляется

Принято бизнес-правило:

> Если executor назначен, он уже может взять Ticket в работу.

Поэтому отдельное состояние:

```text
READY_TO_WORK
```

не несёт дополнительного бизнес-смысла.

После:

```text
ACCEPTED → ASSIGNED
```

исполнитель уже имеет право выполнить:

```text
ASSIGNED → AT_WORK
```

Если работу пока выполнять не следует:

```text
ASSIGNED → DEFERRED
```

Отдельное состояние «исполнитель назначен, но ещё не может начать работу» не требуется.

---

### 3. Основной рабочий путь

После удаления `SCHEDULED` и `READY_TO_WORK` основной workflow выглядит значительно проще:

```text
ACCEPTED
    → ASSIGNED
    → AT_WORK
    → READY_FOR_REVIEW
    → EXECUTED
```

Ретроспективная регистрация выполненной работы остаётся:

```text
ASSIGNED
    → READY_FOR_REVIEW
    → EXECUTED
```

без промежуточного `AT_WORK`.

Для такого перехода в `READY_FOR_REVIEW` передаются:

```text
actual_started_at
actual_finished_at
```

Обычный путь остаётся:

```text
ASSIGNED
    → AT_WORK
    → READY_FOR_REVIEW
```

---

### 4. DEFERRED остаётся самостоятельным workflow state

`DEFERRED` имеет собственный бизнес-смысл:

```text
работа по Ticket временно отложена
```

Например:

```text
ACCEPTED → DEFERRED
ASSIGNED → DEFERRED
AT_WORK → DEFERRED
```

Поэтому, в отличие от `SCHEDULED`, это настоящий статус жизненного цикла.

---

### 5. Планирование отделяется от workflow

Текущий план хранится непосредственно в `Ticket`:

```text
planned_start_at
planned_finish_at
```

Планирование не создаёт `TicketStatusRecord` и не меняет текущий status.

Операции могут выглядеть как:

```text
set_plan(...)
change_plan(...)
clear_plan(...)
```

или быть сведены к меньшему API.

Точные методы пока не определены.

Также пока не определено, в каких workflow states разрешено устанавливать, изменять или удалять план.

---

### 6. История перепланирований пока не реализуется

После удаления `SCHEDULED` из status history больше не будет автоматически сохраняться история:

```text
план 10:00
→ план 14:00
→ план на следующий день
```

На текущем этапе это допустимо.

Храним только актуальное состояние:

```text
Ticket.planned_start_at
Ticket.planned_finish_at
```

Если история перепланирований понадобится, её можно добавить позже отдельным механизмом:

```text
PlanningRecord
PlanningHistory
domain events
audit log
```

Это не должно блокировать упрощение workflow сейчас.

---

### 7. Возврат из DEFERRED с предыдущим исполнителем

Отдельно обсуждалась операция:

```text
ASSIGNED executor=25
→ DEFERRED
→ «Вернуть»
```

Принято, что это отдельное бизнес-действие, а не специальное значение:

```text
executor_id=0
```

`0` продолжает означать отсутствие исполнителя.

`Ticket` должен по своей истории уметь определить наличие предыдущего executor и кандидата на восстановление.

При этом актуальная доступность Admin:

```text
enabled
department
другие cross-aggregate ограничения
```

проверяется вне `Ticket`.

Для оператора кнопка **«Вернуть»** недоступна как минимум в двух случаях:

```text
предыдущего executor нет

или

предыдущий executor есть,
но сейчас не может быть назначен
```

Точная семантика поиска предыдущего executor ещё требует определения.

---

### 8. Главный принцип

Workflow status отвечает на вопрос:

> На каком этапе жизненного цикла находится Ticket?

Он не должен использоваться только для кодирования наличия дополнительных данных.

Поэтому:

```text
ACCEPTED
ASSIGNED
AT_WORK
DEFERRED
READY_FOR_REVIEW
EXECUTED
CANCELLED
```

имеют самостоятельный workflow-смысл.

А:

```text
SCHEDULED
READY_TO_WORK
```

в существующей модели фактически кодируют:

```text
plan
executor + plan
```

и поэтому удаляются.

---

### Новый граф

Общее направление уже понятно:

```text
CREATED / CREATED_FROM_TICKET_USER
    → ACCEPTED / REJECTED

ACCEPTED
    → ASSIGNED
    ↔ DEFERRED
    → CANCELLED

ASSIGNED
    → AT_WORK
    → READY_FOR_REVIEW
    ↔ DEFERRED
    → CANCELLED

AT_WORK
    → PAUSED
    → READY_FOR_REVIEW
    → DEFERRED
    → CANCELLED

READY_FOR_REVIEW
    → EXECUTED
    → AT_WORK / ASSIGNED / DEFERRED / CANCELLED
```

Но это пока не окончательный transition graph.

После удаления `SCHEDULED` и `READY_TO_WORK` его необходимо пройти отдельно переход за переходом и проверить бизнес-смысл каждого ребра.

---

### Что потребуется изменить

```text
- удалить TicketStatus.SCHEDULED;
- удалить TicketStatus.READY_TO_WORK;

- перенести planned_start_at / planned_finish_at
  в состояние самого Ticket;

- убрать planned_* из семантики workflow status;

- переписать TicketState transition graph;

- убрать schedule как status transition;

- удалить ready_to_work как status transition;

- упростить TicketManagementService;

- изменить обычный запуск работы:
    ASSIGNED → AT_WORK;

- изменить ретроспективное завершение:
    ASSIGNED → READY_FOR_REVIEW;

- пересмотреть возврат из DEFERRED
  с предыдущим executor;

- обновить persistence / mapper / repository;

- обновить DTO / assembler;

- обновить domain tests;

- обновить application tests;

- обновить workflow documentation.
```

## Статус решений

### Согласовано

```text
SCHEDULED удаляется из workflow.

READY_TO_WORK удаляется из workflow.

planned_start_at / planned_finish_at
становятся свойствами Ticket
и не определяют его workflow status.

Назначенный executor уже может начать работу:

ASSIGNED → AT_WORK.

Если работу выполнять пока не следует,
используется DEFERRED.

Ретроспективное выполнение:

ASSIGNED → READY_FOR_REVIEW.

Историю перепланирований
на текущем этапе не реализуем.
```

### Согласовано концептуально, но требует уточнения

```text
Операция «Вернуть» из DEFERRED
с предыдущим executor.
```

Нужно определить:

```text
какого executor считать предыдущим;

насколько далеко разрешено искать его в истории;

точную семантику возврата;

взаимодействие возврата с планированием.
```

### Открытые вопросы

```text
точный transition graph после удаления
SCHEDULED и READY_TO_WORK;

в каких status разрешено менять plan;

поведение plan при DEFERRED;

поведение plan при возврате из DEFERRED;

точный API управления plan;

окончательная семантика
planned_start_at / planned_finish_at;

нужна ли в будущем отдельная
история перепланирований.
```
