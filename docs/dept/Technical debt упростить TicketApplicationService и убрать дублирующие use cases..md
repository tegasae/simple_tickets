## Technical debt: упростить TicketApplicationService и убрать дублирующие use cases

### Текущее состояние

`TicketApplicationService` является единым application service для внутренней `Ticket`.

Он отвечает за:

```text
- permission checks;
- UnitOfWork;
- загрузку aggregates;
- cross-aggregate validation;
- вызов domain services;
- синхронизацию Ticket / TicketUser;
- сохранение;
- commit;
- преобразование результата в DTO.
```

Ранее рассматривалось разбиение application layer на несколько сервисов:

```text
TicketCommandApplicationService
TicketManagementApplicationService
TicketExecutionApplicationService
TicketReviewApplicationService
TicketQueryApplicationService
```

От этого решения отказались.

На текущем этапе проекту достаточно одного:

```text
TicketApplicationService
```

Разделение application service на несколько классов сейчас не даёт самостоятельных transaction boundaries, security boundaries или иных преимуществ и только усложняет API и навигацию по коду.

---

## Проблема

В текущем `TicketApplicationService` остались методы, возникшие вследствие разделения workflow на management/review операции.

Например существуют одновременно:

```text
defer()
return_to_deferred()

schedule()
return_to_scheduled()

assign_executor()
return_to_assigned()

ready_to_work()
return_to_ready_to_work()
```

При этом часть этих пар представляет один и тот же application use case.

Например:

```text
defer()
```

и:

```text
return_to_deferred()
```

на application level отличаются только выбором domain service:

```python
TicketManagementService.defer(...)
```

против:

```python
TicketReviewService.return_to_deferred(...)
```

В обоих случаях бизнес-результат один:

```text
current status → DEFERRED
```

Допустимость конкретного перехода уже определяется workflow агрегата `Ticket`.

Таким образом, наличие двух публичных application methods не отражает двух разных application use cases.

---

## Решение

Сохранить один:

```text
TicketApplicationService
```

и не разбивать его сейчас на отдельные management/execution/review application services.

Публичный application API должен соответствовать **бизнес-действиям**, а не исходному статусу Ticket.

То есть если одно действие имеет одинаковую семантику независимо от того, из какого разрешённого состояния оно выполняется, должен существовать один application method.

Например:

```python
defer(...)
schedule(...)
assign_executor(...)
```

должны работать и для `READY_FOR_REVIEW`, если соответствующий переход разрешён domain workflow.

Не требуется отдельное:

```python
return_to_deferred(...)
return_to_scheduled(...)
return_to_assigned(...)
```

только потому, что исходный статус равен `READY_FOR_REVIEW`.

---

## Методы, которые следует удалить

После проверки domain semantics удалить из `TicketApplicationService`:

```text
return_to_deferred()
return_to_scheduled()
return_to_assigned()
```

И использовать соответственно:

```text
defer()
schedule()
assign_executor()
```

для всех разрешённых исходных состояний.

Например:

```text
READY_FOR_REVIEW → DEFERRED
```

выполняется обычным:

```python
ticket_service.defer(...)
```

а:

```text
READY_FOR_REVIEW → ASSIGNED
```

обычным:

```python
ticket_service.assign_executor(...)
```

---

## Методы, которые должны остаться отдельными

Отдельный application method нужен, если отличается **смысл бизнес-действия**, а не только исходный статус.

Например:

```text
at_work()
```

означает:

```text
текущий executor начинает работу
```

а:

```text
return_to_work()
```

означает:

```text
reviewer возвращает результат тому же executor на доработку
```

Хотя оба действия приводят к:

```text
AT_WORK
```

семантика actor-а различна, поэтому это разные use cases.

Аналогично отдельным остаётся:

```text
confirm_execution()
```

поскольку:

```text
READY_FOR_REVIEW → EXECUTED
```

является отдельным действием проверки результата.

---

## `return_to_ready_to_work`

Метод:

```text
return_to_ready_to_work()
```

не удалять автоматически вместе с остальными.

Семантика `READY_TO_WORK` сейчас уточняется отдельно.

В частности уже принято правило:

```text
SCHEDULED → READY_TO_WORK
```

означает назначение executor к уже существующему плану и не должно одновременно выполнять replanning.

Поэтому прежде чем объединять:

```text
ready_to_work()
return_to_ready_to_work()
```

необходимо окончательно определить payload и семантику всех переходов в `READY_TO_WORK`.

---

## Целевой публичный API

Ориентировочно:

```text
Create / edit:
    create_ticket
    update_details
    change_department

Management:
    accept
    reject
    defer
    schedule
    assign_executor
    ready_to_work
    cancel

Execution:
    at_work
    pause_work
    resume_work
    submit_for_review
    record_completed_work_for_review

Review:
    confirm_execution
    return_to_work
    [return_to_ready_to_work — решить отдельно]

Other:
    add_comment
    delete

Queries:
    get_by_id
    get_all
```

Публичный alias:

```python
execute()
```

для `confirm_execution()` можно оставить временно для совместимости, но в дальнейшем желательно использовать одно имя.

---

## Что не делать

Не создавать сейчас:

```text
TicketManagementApplicationService
TicketExecutionApplicationService
TicketReviewApplicationService
TicketCommandApplicationService
TicketQueryApplicationService
```

только ради разделения большого класса.

Такое разбиение имеет смысл позже только при появлении реальной причины, например:

```text
- разные permission boundaries;
- разные transaction boundaries;
- существенно разные dependencies;
- отдельный read model;
- класс стал объективно трудно поддерживать.
```

---

## Требуемые изменения

```text
- оставить один TicketApplicationService;
- удалить дублирующие return_to_deferred();
- удалить дублирующие return_to_scheduled();
- удалить дублирующие return_to_assigned();
- использовать defer()/schedule()/assign_executor()
  также из READY_FOR_REVIEW;
- отдельно решить судьбу return_to_ready_to_work();
- обновить endpoint handlers, если они вызывают удаляемые методы;
- удалить соответствующие дублирующие application tests;
- добавить тесты, что обычные методы работают
  из READY_FOR_REVIEW согласно TicketState;
- обновить документацию API.
```

### Статус

```text
Technical debt.

Архитектурное решение:
на текущем этапе используется один TicketApplicationService.

Разбиение application layer на несколько Ticket-сервисов отложено
и не должно выполняться без практической необходимости.
```
