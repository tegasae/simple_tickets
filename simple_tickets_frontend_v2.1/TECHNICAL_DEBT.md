# Технический долг Simple Tickets

Этот файл содержит только изменения, которые ещё остаются отложенными.

Актуальный backend-контракт уже содержит:

```text
current_executor_id
last_executor_id
```

Оба поля могут быть равны `0`.

Поле `version` в актуальном `TicketResponse` отсутствует и frontend его не использует.

---

## 1. Добавить `current_status` в `TicketResponse`

### Сейчас

В `TicketResponse` есть история:

```text
statuses
```

но отдельного `current_status` пока нет.

Frontend получает текущий статус из последней записи `statuses`.

### Позже

Добавить в backend:

```python
current_status: TicketStatus
```

После этого frontend будет использовать `ticket.current_status` напрямую.

---

## 2. Окончательно зафиксировать контракт `time_spent`

API сейчас возвращает:

```text
time_spent: integer
```

Контракт следует считать количеством секунд и сохранить именно таким.

Frontend отображает значение человекочитаемо:

```text
0 мин
25 мин
1 ч 15 мин
2 д 3 ч
```

---

## 3. Серверная комбинированная фильтрация и поиск заявок

Сейчас комбинированные фильтры и поиск выполняются на frontend.

Backend уже предоставляет отдельные endpoint-ы:

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

При существенном росте числа заявок можно добавить серверную комбинированную фильтрацию и поиск.

До появления реальной необходимости API не усложняем.

---

## 4. Серверная фильтрация `remote_work_recommended`

Сейчас представление **«Рекомендовано удалённо»** формируется frontend-ом:

```text
remote_work_recommended == true
```

Позже этот критерий может стать частью общей серверной фильтрации.

Отдельный endpoint сейчас не требуется.

---

# Приоритет

## Ближайшее

1. `TicketResponse.current_status`.
2. Проверить и окончательно зафиксировать `time_spent` как integer seconds.

## По необходимости

3. Серверная комбинированная фильтрация и поиск.
4. Серверная фильтрация по `remote_work_recommended`.
