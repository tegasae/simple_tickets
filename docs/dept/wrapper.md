# Технический долг: создать доменные фасады для основных сущностей

## Контекст

В текущей архитектуре бизнес-операции над сущностями частично выполняются:

- напрямую через методы aggregate;
- через domain services;
- через отдельные domain policies;
- частично через application services, которые вынуждены знать, какой именно набор проверок нужно вызвать перед изменением aggregate.

По мере роста логики это создаёт риск, что правила начнут дублироваться или обходиться.

Пример для `Admin`:

```text
Admin.create(...)
Admin.update(...)
Admin.change_department(...)
Admin.disable(...)

AdminService.change_department(...)
AdminService.update(...)
AdminService.disable(...)

DepartmentPolicy.can_operation(...)
```

Application layer должен помнить:

- когда достаточно вызвать метод `Admin`;
- когда требуется `AdminService`;
- когда дополнительно требуется `DepartmentPolicy`;
- какие внешние факты нужно предварительно получить;
- когда необходимо выполнить `touch()` для optimistic concurrency.

Аналогичная ситуация начинает формироваться для `User`, `Client` и `Department`.

---

## Решение, которое необходимо рассмотреть

Создать доменные фасады для основных сущностей:

```text
AdminFacade
UserFacade
ClientFacade
DepartmentFacade
```

Либо использовать существующие `AdminService`, `UserService`, `ClientService`, `DepartmentService` как такие фасады, если отдельный слой классов не даст дополнительной ценности.

Главная цель — получить единую доменную точку входа для бизнес-операций над конкретной сущностью.

Например:

```text
AdminApplicationService
        |
        v
    AdminFacade
        |
        +--> Admin
        +--> Department
        +--> cross-aggregate rules
```

Application layer при этом отвечает только за:

- RBAC и permissions;
- загрузку aggregates;
- получение внешних фактов из repositories;
- UnitOfWork;
- optimistic concurrency (`save`, `touch`);
- persistence;
- DTO.

Фасад отвечает за:

- выбор необходимых domain rules;
- межагрегатные проверки;
- вызов методов aggregate;
- целостность бизнес-операции.

---

## Пример для Admin

В перспективе фасад должен предоставлять операции уровня:

```python
AdminFacade.create(...)
AdminFacade.update(...)
AdminFacade.change_department(...)
AdminFacade.remove_department(...)
AdminFacade.disable(...)
AdminFacade.ensure_can_delete(...)
```

Application layer не должен самостоятельно знать, что, например:

```text
create Admin
    -> Department должен быть enabled
```

или:

```text
change Department
    -> Admin не должен быть текущим исполнителем Ticket
    -> новый Department должен быть enabled
```

Эти правила должны находиться внутри доменного фасада.

---

## Пример для User

Предполагаемые операции:

```python
UserFacade.create(...)
UserFacade.update(...)
UserFacade.disable(...)
UserFacade.enable(...)
UserFacade.ensure_can_delete(...)
```

Особенно важен `disable()`, поскольку он уже является полноценной межагрегатной операцией:

```text
User
    ↓
Ticket where user_id == User
OR contact_user_id == User
    ↓
SUSPENDED, кроме terminal и AT_WORK
    ↓
linked TicketUser synchronized
```

Application layer должен только загрузить необходимые aggregates и сохранить результат.

---

## Client

Для `Client` фасад особенно полезен из-за каскада:

```text
Client.disable()
    ↓
Users -> disabled
    ↓
Tickets -> SUSPENDED
        except terminal
        except AT_WORK
    ↓
linked TicketUser -> SUSPENDED
```

Сейчас эта логика уже естественно формирует полноценный доменный сервис.

---

## Department

`DepartmentFacade` / `DepartmentService` должен содержать межагрегатные правила операций над Department.

Например:

```text
Department нельзя disable,
если:

- существует enabled Admin этого Department;
- существует open Ticket этого Department.
```

При этом перевод `Admin` между Department остаётся операцией фасада `Admin`, поскольку основной изменяемый aggregate — `Admin`.

---

## Важное ограничение

Фасады не должны превращаться в механические прокси ко всем методам aggregate.

Если операция полностью локальна для одного aggregate и не требует внешнего контекста, допустим прямой вызов:

```python
admin.change_password(...)
admin.add_account(...)
admin.remove_account()

user.change_password(...)
user.add_account(...)
user.remove_account()
```

Фасад нужен прежде всего там,