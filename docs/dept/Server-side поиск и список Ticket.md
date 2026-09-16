## Server-side поиск и список Ticket

### Текущее состояние

`GET /admin/tickets/` временно использует `TicketApplicationService.get_all()`.

Все Ticket загружаются как полные aggregates, включая status history и comments. Фильтрация списка может выполняться вне persistence/backend search.

Такое решение принято временно, пока объём данных небольшой.

### Проблема

`get_all()` не подходит как окончательная read-модель для таблицы Ticket:

* загружаются все Ticket;
* для списка загружается лишняя aggregate-информация;
* statuses и comments загружаются для каждой Ticket;
* отсутствует полноценная server-side pagination;
* отсутствует единый server-side механизм комбинирования фильтров;
* решение плохо масштабируется при росте количества заявок.

Ранее существовавшую реализацию `TicketSearchService/search()` не следует восстанавливать без пересмотра: она была создана для более ранней версии модели Ticket и содержала устаревшую семантику некоторых полей, включая current executor и derived state.

### Целевое решение

Реализовать отдельную read/query-модель списка Ticket.

Публичный API должен использовать один endpoint:

```text
GET /admin/tickets/
```

с набором необязательных criteria, комбинируемых через `AND`.

Ориентировочный набор критериев:

```text
client_id
user_id
contact_user_id
admin_id
executor_id
department_id
status / statuses
is_closed
created_from
created_to
text
pagination
sort
```

Точный состав критериев необходимо сверить с актуальными требованиями frontend-а перед реализацией.

Не создавать отдельные API/use cases вида:

```text
get_by_client
get_by_user
get_by_status
get_by_date
...
```

### Read model

Список должен возвращать лёгкий DTO, например:

```text
TicketListItemDTO

ticket_id
client_id
user_id
contact_user_id
admin_id
text_of_ticket
current_status
current_executor_id
department_id
urgency_level
date_created
is_closed
```

Историю статусов, comments и другие тяжёлые данные aggregate для списка не загружать.

Полная Ticket загружается отдельно:

```text
GET /admin/tickets/{ticket_id}
```

### Persistence

Поиск является query/read concern и не обязан восстанавливать полный `Ticket` aggregate.

SQL/query implementation должна непосредственно получать:

* текущий статус;
* текущего исполнителя;
* необходимые поля списка;
* количество записей для pagination, если оно требуется UI.

Реализация не должна зависеть от SQLite-специфики и должна быть переносима на будущий persistence adapter.

### Статус

```text
Technical debt.
Server-side Ticket search намеренно отложен.
Текущий get_all() является временным решением.
```
