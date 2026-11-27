# Кэширование справочных данных во frontend Simple Tickets

## 1. Общий подход

Для справочных сущностей имеет смысл использовать простой глобальный frontend-кэш.

Цели:

- не перечитывать одни и те же справочники при каждом переходе между разделами;
- не делать несколько одинаковых запросов из разных компонентов;
- быстро разрешать `client_id`, `user_id`, `admin_id`, `department_id` в человекочитаемые имена;
- сохранять архитектуру простой;
- не вводить сложный client-side cache без реальной необходимости.

Объёмы данных позволяют использовать такой подход:

- Clients — до примерно 1000 записей;
- Users — до примерно 4000 записей;
- Admin — десятки;
- Departments — десятки.

---

# 2. Глобальное хранение

Справочные данные должны храниться глобально и переиспользоваться всеми разделами frontend.

Пример структуры:

```javascript
referenceData = {
  clients: new Map(),
  admins: new Map(),
  departments: new Map(),

  users: new Map(),          // user_id -> User
  usersByClient: new Map(),  // client_id -> [user_id, ...]
}
```

Компоненты не должны каждый хранить собственную независимую копию одних и тех же справочников.

Например, `TicketsPage`, `TicketCard` и `ClientsPage` должны использовать общий список Clients.

---

# 3. Lazy loading

Не требуется загружать все справочники сразу после login.

Данные загружаются по мере необходимости.

Пример:

```text
компонент запросил Clients
        ↓
Clients ещё не загружены
        ↓
GET /admin/clients/
        ↓
данные сохраняются в глобальный cache
```

При следующем обращении:

```text
Clients уже загружены
        ↓
используем cache
```

То есть основной принцип:

```text
не загружено -> загрузить
уже загружено -> использовать
```

В реализации используется отдельный признак `loaded`, а не проверка `array.length === 0`, потому что пустой справочник является корректным результатом и не должен вызывать повторный запрос при каждом обращении.

---

# 4. Поведение при входе в раздел

При открытии раздела не следует безусловно перечитывать весь справочник.

Например переходы:

```text
Заявки
→ Клиенты
→ Заявки
→ Клиенты
```

не должны каждый раз приводить к:

```text
GET /admin/clients/
```

Вместо этого раздел вызывает условную операцию типа:

```javascript
ensureClientsLoaded()
```

которая:

- загружает список, если он ещё не был загружен;
- использует cache, если список уже есть.

При необходимости в разделе можно предусмотреть явное действие:

```text
[Обновить]
```

для принудительного reread.

---

# 5. Cache miss по конкретному ID

Если frontend получил ID сущности, которой нет в глобальном cache, не нужно сразу перечитывать весь список.

Пример:

```json
{
  "client_id": 100
}
```

и:

```javascript
clients.get(100) === undefined
```

Тогда используется запрос конкретной сущности:

```text
GET /admin/clients/100
```

После ответа запись добавляется в cache.

Аналогично:

```text
GET /admin/users/{employee_id}
GET /admin/admins/{employee_id}
GET /admin/departments/{department_id}
```

Общий алгоритм:

```text
ID найден в cache
    -> использовать

ID не найден
    -> GET by ID
    -> добавить результат в cache
    -> использовать
```

Это предпочтительнее, чем перечитывать полный справочник.

---

# 6. Обновление cache после mutations

После create/update/delete не следует автоматически перечитывать весь список.

Backend обычно возвращает актуальное состояние изменённой сущности.

После создания:

```javascript
clients.set(created.client_id, created);
```

После изменения:

```javascript
clients.set(updated.client_id, updated);
```

После удаления:

```javascript
clients.delete(clientId);
```

То же правило применяется к:

- Admin;
- User;
- Department.

Основной принцип:

```text
mutation
    ↓
response backend
    ↓
обновление локального cache
```

вместо:

```text
mutation
    ↓
GET all
```

---

# 7. Clients

Clients можно хранить полностью в глобальном cache.

Рекомендуемая схема:

```text
первое обращение
    -> GET /admin/clients/

последующие обращения
    -> cache

неизвестный client_id
    -> GET /admin/clients/{client_id}

create/update
    -> обновить cache

delete
    -> удалить из cache
```

При максимальном количестве около 1000 записей это приемлемо.

---

# 8. Сотрудники (Admin в backend)

Сотрудников (`Admin` в backend API) можно хранить полностью в глобальном cache.

Количество записей небольшое.

Схема:

```text
первое обращение
    -> GET /admin/admins/

последующие обращения
    -> cache

неизвестный employee_id
    -> GET /admin/admins/{employee_id}

mutation
    -> обновить cache
```

---

# 9. Departments

Departments хранятся полностью в глобальном cache.

Количество записей небольшое.

Схема:

```text
первое обращение
    -> GET /admin/departments/

последующие обращения
    -> cache

неизвестный department_id
    -> GET /admin/departments/{department_id}

mutation
    -> обновить cache
```

---

# 10. Users

Users лучше кэшировать немного иначе, поскольку User принадлежит Client.

Не рекомендуется всегда загружать все ~4000 Users заранее.

Оптимальный вариант:

```javascript
usersById = new Map()
usersByClient = new Map()
```

где:

```javascript
usersById
    51 -> User
    52 -> User
    53 -> User

usersByClient
    10 -> [51, 52]
    11 -> [53]
```

---

## 10.1. Загрузка Users по Client

При выборе Client:

```text
client_id = 23
        ↓
проверяем usersByClient[23]
        ↓
если данных нет
        ↓
GET /admin/users/?client_id=23
        ↓
сохраняем Users
```

Это особенно удобно:

- при создании Ticket;
- при выборе Contact User;
- при просмотре карточки Client;
- при фильтрации Users по Client.

---

## 10.2. Неизвестный User

Если встретился `user_id`, которого нет в `usersById`:

```text
GET /admin/users/{employee_id}
```

После ответа:

- добавить User в `usersById`;
- при необходимости добавить его ID в соответствующий `usersByClient`.

---

# 11. Использование в Ticket UI

Ticket содержит ID связанных сущностей:

```text
client_id
user_id
contact_user_id
department_id
```

Frontend должен получать отображаемые значения через общий reference cache.

Например:

```javascript
const client = referenceData.clients.get(ticket.client_id);
```

Если сущность не найдена:

```text
cache miss
    ↓
GET by ID
    ↓
обновление cache
    ↓
rerender
```

Карточка Ticket не должна каждый раз перечитывать весь список Clients, Users, Admin или Departments.

---

# 12. Stale data

Если другой Admin изменил справочную сущность, текущий frontend не узнает об этом мгновенно.

На первом этапе это считается допустимым.

Достаточная стратегия:

- lazy initial loading;
- обновление cache после собственных mutations;
- fetch by ID при cache miss;
- явное обновление списка при необходимости.

Сложные механизмы пока не нужны:

- polling;
- WebSocket invalidation;
- постоянный background refresh;
- сложный TTL cache.

---

# 13. Возможный TTL в будущем

Если stale data станет реальной проблемой, можно добавить простой TTL.

Например:

```text
5 минут
```

Тогда `ensureClientsLoaded()` сможет проверять:

```text
данные есть и свежие
    -> использовать cache

данные устарели
    -> GET all
```

На текущем этапе TTL не требуется.

---

# 14. Итоговая стратегия

## Clients

```text
глобальный cache
первое обращение -> GET all
cache miss по ID -> GET by ID
mutation -> обновить cache
```

## Сотрудники

```text
глобальный cache
первое обращение -> GET all
cache miss по ID -> GET by ID
mutation -> обновить cache
```

## Departments

```text
глобальный cache
первое обращение -> GET all
cache miss по ID -> GET by ID
mutation -> обновить cache
```

## Users

```text
глобальный index by ID
списки кэшируются по client_id
первый запрос для Client -> GET ?client_id=X
cache miss по ID -> GET by ID
mutation -> обновить cache
```

---

# 15. Главный принцип

Frontend не должен постоянно перечитывать одни и те же справочники.

Но также не следует заранее загружать всё без необходимости.

Используем простой подход:

```text
lazy loading
+
global cache
+
fetch by ID on cache miss
+
cache update after mutations
```

Без сложного client-side caching до тех пор, пока реальная нагрузка не потребует этого.
