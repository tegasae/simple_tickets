# Технический долг Simple Tickets

Этот файл содержит только те изменения, которые мы уже обсуждали и сознательно отложили.  
Текущий OpenAPI остаётся источником истины для действующего API.

---

## 1. Добавить `current_status` в `TicketResponse`

### Сейчас

В `TicketResponse` есть полная история:

```text
statuses
```

но отдельного поля текущего статуса нет.

Frontend при необходимости должен брать последнюю запись `statuses`.

### Нужно добавить

В backend:

```python
current_status: TicketStatus
```

или эквивалентное строковое представление enum в web-response.

Изменения потребуются в:

- `TicketResponseDTO`;
- `TicketAssembler`;
- web-модели `TicketResponse`;
- OpenAPI.

### Зачем

Текущий статус является текущим вычисляемым состоянием Ticket и должен приходить от backend напрямую.

Frontend не должен самостоятельно вычислять его из истории.

После добавления список заявок сможет использовать:

```text
ticket.current_status
```

для:

- отображения статуса;
- фильтрации;
- определения UI-действий.

---

## 2. Добавить `current_executor_id` в `TicketResponse`

### Сейчас

В `TicketResponse` нет отдельного ID текущего активного исполнителя.

Для представления **«Назначенные мне»** пока используется:

```text
GET /admin/tickets/by-executor/{executor_id}
```

### Нужно добавить

В backend:

```python
current_executor_id: int
```

Семантика должна соответствовать:

```python
Ticket.current_executor_id()
```

Если активного исполнителя нет:

```text
0
```

Изменения потребуются в:

- `TicketResponseDTO`;
- `TicketAssembler`;
- web-модели `TicketResponse`;
- OpenAPI.

### Зачем

Frontend не должен восстанавливать текущего исполнителя из `statuses`.

Поле потребуется для:

- основной таблицы заявок;
- фильтра по исполнителю;
- отображения исполнителя;
- локального представления «Назначенные мне».

Endpoint:

```text
/admin/tickets/by-executor/{executor_id}
```

при этом можно сохранить — он остаётся полезным специализированным запросом.

---

## 3. Зафиксировать контракт `time_spent`

### Сейчас

OpenAPI возвращает:

```text
time_spent: integer
```

При этом доменный расчёт рабочего времени естественно работает с `timedelta`.

### Нужно проверить и окончательно зафиксировать

В API:

```text
time_spent = integer seconds
```

Если доменный метод возвращает `timedelta`, assembler должен преобразовывать его:

```python
time_spent = int(ticket.working_time().total_seconds())
```

Frontend преобразует секунды в человекочитаемый вид:

```text
0 мин
25 мин
1 ч 15 мин
4 ч 32 мин
2 д 3 ч
```

### Зачем

Не должно быть неоднозначности между:

- `timedelta`;
- ISO 8601 duration;
- количеством секунд.

Для API используем один простой контракт — integer seconds.

---

## 4. Серверная комбинированная фильтрация заявок

### Сейчас

На первом этапе поиск и комбинированная фильтрация выполняются на frontend.

Backend уже имеет отдельные endpoint-ы:

```text
GET /admin/tickets/
GET /admin/tickets/open
GET /admin/tickets/closed
GET /admin/tickets/by-client/{client_id}
GET /admin/tickets/by-user/{user_id}
GET /admin/tickets/by-contact-user/{contact_user_id}
GET /admin/tickets/by-department/{department_id}
GET /admin/tickets/by-executor/{executor_id}
```

### Позже

Если количество заявок станет достаточно большим, можно перенести комбинированные фильтры и поиск на backend.

Потенциальные критерии:

- Client;
- User;
- Contact User;
- Department;
- executor;
- status;
- urgency;
- open/closed;
- `remote_work_recommended`;
- поиск по номеру и тексту.

### Важно

Конкретный новый endpoint или набор query parameters пока **не зафиксирован**.

До появления реальной необходимости не усложняем API.

---

## 5. Серверный фильтр «Рекомендовано удалённо»

### Сейчас

Представление:

```text
Рекомендовано удалённо
```

формируется frontend-ом:

```text
remote_work_recommended == true
```

### Позже

Если локальная фильтрация станет неудобной из-за объёма данных, можно добавить backend-фильтр по:

```text
remote_work_recommended
```

Это может быть частью общей серверной фильтрации заявок.

Отдельный endpoint сейчас не требуется.

---

# Приоритет

## Ближайшие изменения

1. `TicketResponse.current_status`
2. `TicketResponse.current_executor_id`
3. Проверить и окончательно зафиксировать `time_spent` как integer seconds

## Отложено до необходимости

4. Серверная комбинированная фильтрация и поиск
5. Серверная фильтрация по `remote_work_recommended`

---

# Что сейчас не является техническим долгом

## «Назначенные мне»

Новый endpoint сейчас не нужен.

Используем существующий:

```text
GET /admin/tickets/by-executor/{executor_id}
```

## Поиск и фильтры frontend

На первом этапе это сознательное решение, а не ошибка архитектуры.

Перенос на backend потребуется только при росте объёма данных.

## Предыдущий React frontend

Предыдущая версия frontend используется только как UI-reference.

Несоответствие её старых Ticket endpoint-ов текущему API не считается долгом новой версии, поскольку старый код не является актуальной кодовой базой.
