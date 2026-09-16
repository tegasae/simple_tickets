## Два допустимых пути перехода в READY_FOR_REVIEW

### Проблема

Текущая модель должна явно различать два способа завершения работы исполнителем:

1. обычный workflow, когда начало работы было своевременно зарегистрировано через `AT_WORK`;
2. ретроспективную регистрацию уже выполненной работы, когда этап `AT_WORK` не был зарегистрирован.

Оба сценария должны приводить в:

```text
READY_FOR_REVIEW
```

поскольку результат работы обязательно проверяется другим сотрудником до перехода в:

```text
EXECUTED
```

### Допустимые потоки

Обычный workflow:

```text
ASSIGNED
    → AT_WORK
    → READY_FOR_REVIEW

READY_TO_WORK
    → AT_WORK
    → READY_FOR_REVIEW
```

Ретроспективная регистрация:

```text
ASSIGNED
    → READY_FOR_REVIEW

READY_TO_WORK
    → READY_FOR_REVIEW
```

Таким образом, допустимые непосредственные входы в `READY_FOR_REVIEW`:

```text
AT_WORK
ASSIGNED
READY_TO_WORK
```

### SCHEDULED

Переход:

```text
SCHEDULED → READY_FOR_REVIEW
```

должен быть запрещён.

`SCHEDULED` означает, что заявка имеет план, но исполнитель ещё не определён.

Если работа была фактически выполнена при сохранённом состоянии `SCHEDULED`, это считается нарушением бизнес-процесса и не должно исправляться созданием искусственной истории задним числом.

Запрещено также восстанавливать такую историю через фиктивную последовательность:

```text
SCHEDULED
    → ASSIGNED
    → READY_FOR_REVIEW
```

если назначение исполнителя фактически не было произведено до выполнения работы.

### Обычный переход AT_WORK → READY_FOR_REVIEW

При:

```text
AT_WORK → READY_FOR_REVIEW
```

начало работы уже зафиксировано предыдущей `AT_WORK` status record.

Поэтому новый `READY_FOR_REVIEW` record не должен повторно принимать:

```text
actual_started_at
```

Фактический интервал работы определяется существующей workflow history.

### Ретроспективный переход

Для:

```text
ASSIGNED → READY_FOR_REVIEW
READY_TO_WORK → READY_FOR_REVIEW
```

этап `AT_WORK` отсутствует.

Поэтому при регистрации выполненной работы необходимо обязательно указать:

```text
actual_started_at
actual_finished_at
```

Эти значения фиксируют реальный период выполнения работы.

### Executor

Для ретроспективного перехода `executor_id` не должен повторно передаваться вызывающим кодом.

Он уже определён текущим состоянием:

```text
ASSIGNED.executor_id
READY_TO_WORK.executor_id
```

Новая `READY_FOR_REVIEW` status record должна автоматически наследовать текущего исполнителя:

```text
current.executor_id
    →
READY_FOR_REVIEW.executor_id
```

Это исключает дублирование информации и возможность передать исполнителя, отличающегося от фактически назначенного.

### Domain invariant

`Ticket` должен проверять семантику перехода в зависимости от предыдущего состояния.

Концептуально:

```python
if new_status == READY_FOR_REVIEW:

    if previous_status == AT_WORK:
        actual_started_at must be None

    elif previous_status in {
        ASSIGNED,
        READY_TO_WORK,
    }:
        actual_started_at is required
        actual_finished_at is required
        executor_id must equal previous_record.executor_id

    else:
        transition is forbidden
```

### Domain service

Следует разделять обычное завершение работы и ретроспективную регистрацию по смыслу операции.

Обычный сценарий:

```python
submit_for_review(...)
```

для:

```text
AT_WORK → READY_FOR_REVIEW
```

Ретроспективный сценарий:

```python
record_completed_work_for_review(...)
```

для:

```text
ASSIGNED → READY_FOR_REVIEW
READY_TO_WORK → READY_FOR_REVIEW
```

`record_completed_work_for_review()` не должен принимать `executor_id`.

Ориентировочная сигнатура:

```python
record_completed_work_for_review(
    *,
    ticket: Ticket,
    actor_employee_id: int,
    actual_started_at: datetime,
    actual_finished_at: datetime,
    comment: str = "",
)
```

Executor определяется из текущей status record.

### Review

После любого из двух потоков дальнейший workflow одинаков:

```text
READY_FOR_REVIEW → EXECUTED
```

`EXECUTED` означает, что результат работы проверен и принят.

Исполнитель Ticket не должен иметь возможности самостоятельно подтвердить собственную работу.

Проверку выполняет другой сотрудник с соответствующим permission.

### Требуемые изменения

Необходимо:

```text
- удалить SCHEDULED → READY_FOR_REVIEW из графа переходов;
- оставить AT_WORK → READY_FOR_REVIEW;
- оставить ASSIGNED → READY_FOR_REVIEW;
- оставить READY_TO_WORK → READY_FOR_REVIEW;
- изменить validation payload для READY_FOR_REVIEW;
- перестать передавать executor_id в retrospective completion для ASSIGNED/READY_TO_WORK;
- наследовать executor_id из текущей status record;
- проверить, что reviewer не совпадает с executor;
- обновить rehydrate validation;
- обновить domain/application tests;
- обновить таблицу состояний и документацию workflow.
```

### Требуемые тесты

Как минимум:

```text
ASSIGNED → AT_WORK → READY_FOR_REVIEW
    разрешён

READY_TO_WORK → AT_WORK → READY_FOR_REVIEW
    разрешён

ASSIGNED → READY_FOR_REVIEW
    разрешён только с actual_started_at/actual_finished_at

READY_TO_WORK → READY_FOR_REVIEW
    разрешён только с actual_started_at/actual_finished_at

SCHEDULED → READY_FOR_REVIEW
    запрещён

AT_WORK → READY_FOR_REVIEW
    запрещает переданный actual_started_at

ретроспективный READY_FOR_REVIEW
    наследует executor_id из текущего состояния

READY_FOR_REVIEW → EXECUTED
    запрещён для текущего executor
```

### Статус

```text
Technical debt.

Семантика двух потоков согласована.
Текущую domain validation, service API, transition graph и tests необходимо привести к этой модели.
```
