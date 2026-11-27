## Роли
#### Роли администраторов
#### Базовая роль
```
    CLIENT_VIEW = "client.view"                                     # просмотр клиентов
    ADMIN_VIEW="admin.view"                                         # просмотр admin-ов
    DEPARTMENT_VIEW="department.view"                               # просмотр отделов
    TICKET_CREATED="ticket.created"                                 # может создавать заявки
    TICKET_VIEW = "ticket.view"                                     # просмотр заявок
```

```json
{
  "role_id": 80,
  "name": "Обычный пользователь",
  "permissions": [
    "ticket.view",
    "department.view",
    "admin.view",
    "client.view",
    "ticket.created"
  ],
  "description": "Базовая роль, все остальные основаны на ней",
  "is_system_role": false,
  "date_created": "2026-11-19T13:14:10.653809Z"
}
```





#### Роль обычного инженера
1) Может создавать заявки
2) Выполнять работы
```
    TICKET_CREATED="ticket.created"                                 # может создавать заявки
    TICKET_VIEW = "ticket.view"                                     # просмотр заявок
    TICKET_AT_WORK = "ticket.at_work"                               # имеет право выполнять заявки
    TICKET_AT_WORK_RETROSPECTIVE = "ticket.at_work_retrospective"   # имеет право вносить данные по работе ретроспективно
```
```json
{
  "role_id": 81,
  "name": "Обычный инженер",
  "permissions": [
    "ticket.created",
    "ticket.at_work",
    "ticket.view",
    "ticket.at_work_retrospective"
  ],
  "description": "Обычный инженер, может выполнять заявки, основывается на базовой роли",
  "is_system_role": false,
  "date_created": "2026-11-19T13:18:04.438066Z"
}


```

#### Роль опытного инженера
1) Может создавать заявки
2) Подтверждать заявки
3) Выполнять работы
4) Подтверждать работы
```
    TICKET_ACCEPTED = "ticket.accepted"                             # имеет право подтверждать заявки
    TICKET_EXECUTED = "ticket.executed"                             # имеет право переводить в executed
```
```json
{
  "role_id": 82,
  "name": "Опытный инженер",
  "permissions": [
    "ticket.accepted",
    "ticket.executed"
  ],
  "description": "Опытный инженер, может подтверждать заявки и подтверждать выполнение, основывается на роли обычного инженера",
  "is_system_role": false,
  "date_created": "2026-11-19T13:21:06.478717Z"
}

```


#### Роль удаленщика
1) Может выполнять работы удаленно
```
    TICKET_AT_WORK_REMOTE = "ticket.at_work_remote"                 # имеет право выполнять заявки, который рекомендованы как удаленные
```

```json
{
  "role_id": 83,
  "name": "Удаленщик",
  "permissions": [
    "ticket.at_work_remote"
  ],
  "description": "Работа на горячей линии, добавляется к ролям инженеров",
  "is_system_role": false,
  "date_created": "2026-11-19T13:38:31.616620Z"
}
```

#### Роль менеджера
1) Может принимать заявки
2) Отказывать пользовательским заявкам
3) Может подтверждать заявки
4) Рекомендовать заявку на горячую линию
5) Назначать исполнителя
6) Подтверждать работы
7) Снимать заявки
8) Заводить клиентов
9) Заводить пользователей клиента
10) Отключать клиентов
11) Отключать пользователей клиента
```
    CLIENT_OPERATION = "client.operation"                           # операции с клиентами
    CLIENT_DECISION = "client.decision"                             # решения по клиенту
    CLIENT_CREATE = "client.create"                                 # создание клиента
    USER_OPERATION="user.operation"                                 # операции с пользователями
    TICKET_OPERATION="ticket.operation"                             # общие операции с заявками
    TICKET_ACCEPTED = "ticket.accepted"                             # имеет право подтверждать заявки
    TICKET_CANCELLED="ticket.canceled"                              # имеет право снимать заявки cancel или reject
    TICKET_EXECUTED = "ticket.executed"                             # имеет право переводить в executed

```
```json
{
  "role_id": 84,
  "name": "Менеджер",
  "permissions": [
    "ticket.canceled",
    "ticket.accepted",
    "client.operation",
    "ticket.operation",
    "user.operation",
    "client.create",
    "client.decision",
    "ticket.executed"
  ],
  "description": "Роль менеджера, базируется на роли обычного пользователя",
  "is_system_role": false,
  "date_created": "2026-11-19T13:44:04.617319Z"
}
```


#### Роль управления адмнистраторами
1) Может заводить администраторов
2) Может отключать администраторов
3) Может управлять ролями администраторов
4) Может управлять ролями пользователей клиентов
5) Может работат с отделами
```
    ADMIN_OPERATION="admin.operation"                               # операции с admin-ами
    DEPARTMENT_OPERATION="department.operation"                     # операции с отделами
    DEPARTMENT_VIEW="department.view"                               # просмотр отделов
    ROLE_ASSIGN="role.assign"                                       # имеет право работать с ролями Admin-ов
    ROLE_USER_ASSIGN = "role_user.assign"                           # имеет право работать с ролями User-ов
```
```json
{
  "role_id": 85,
  "name": "Управление админстраторами",
  "permissions": [
    "department.operation",
    "role.assign",
    "department.view",
    "admin.operation",
    "role_user.assign"
  ],
  "description": "Роль управления админстраторами, базируется на роли обычного пользователя",
  "is_system_role": false,
  "date_created": "2026-11-19T13:46:58.249169Z"
}
```


### Роли пользователей клиентов
#### Роль обычного пользователя
1) Может создавать заявки
2) Может просматривать свои заявки
3) Может снимать свои заявки
```
    TICKET_OPERATION = "ticket.operation"                           # имеет право работать со своим заявками
    TICKET_VIEW = "ticket.view"                                     # имеет право смотреть свои заявки
```
```json
 {
    "role_id": 87,
    "name": "Обычный пользователь",
    "permissions": [
      "ticket.view",
      "ticket.operation"
    ],
    "description": "Обычный пользователь клиент",
    "is_system_role": false
  }
```


#### Роль главного пользователя
1) Может создавать заявки 
2) Может просматривать все заявки
3) Может снимать все заявки
```
    TICKET_OPERATION_ALL="ticket.operation.all"                     # имеет право работать со всеми заявками организации
    TICKET_VIEW_ALL = "ticket.view.all"                             # имеет право смотреть заявки организации
```
```json
{
  "role_id": 88,
  "name": "Главный пользователь",
  "permissions": [
    "ticket.operation.all",
    "ticket.view.all"
  ],
  "description": "Роль главного пользователя клиента, добавляется к роли обычного пользователя",
  "is_system_role": false
}

```





## Администраторы
### Обычный сотрудник
**Роль:** Базовая роль
```json
{
  "employee_id": 220,
  "first_name": "Обычный пользователь",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "standard_user",
  "enabled_login": true,
  "date_created": "2026-11-20 19:14:51.730199+00:00",
  "roles": [
    80
  ],
  "job_title": "",
  "department_id": 0
}
```

### Обычный инженер
**Роль:** Базовая роль, Роль обычного инженера
```json
{
  "employee_id": 221,
  "first_name": "Обычный инженер",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "standard_engineer",
  "enabled_login": true,
  "date_created": "2026-11-20 19:37:57.089254+00:00",
  "roles": [
    80,
    81
  ],
  "job_title": "",
  "department_id": 2
}
```
### Опытный инженер
**Роль:** Базовая роль, Роль обычного инженера, Роль опытного инженера
```json
{
  "employee_id": 222,
  "first_name": "Опытный инженер",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "chief_engineer",
  "enabled_login": true,
  "date_created": "2026-11-20 19:40:21.912237+00:00",
  "roles": [
    80,
    81,
    82
  ],
  "job_title": "",
  "department_id": 2
}
```
### Удаленщик
Роль: Роль удаленщика
```json
{
  "employee_id": 223,
  "first_name": "Обычный инженер с работой на удаленке",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "remote_engineer",
  "enabled_login": true,
  "date_created": "2026-11-20 19:43:49.300517",
  "roles": [
    80,
    81,
    83
  ],
  "job_title": "",
  "department_id": 2
}

```
### Менеджер
**Роль:**  Базовая роль, Роль менеджера
```json
{
  "employee_id": 224,
  "first_name": "Менеджер",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "manager",
  "enabled_login": true,
  "date_created": "2026-11-20 19:45:17.195260+00:00",
  "roles": [
    80,
    84
  ],
  "job_title": "",
  "department_id": 0
}
```
### Руководитель отдела
**Роль:** Базовая роль, Роль менеджера, Роль управления адмнистраторами
```json
{
  "employee_id": 225,
  "first_name": "Руководитель отдела",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "chief_department",
  "enabled_login": true,
  "date_created": "2026-11-20 19:47:26.660021",
  "roles": [
    80,
    84,
    85
  ],
  "job_title": "",
  "department_id": 0
}
```

## Клиенты
### Клиент
```json
{
  "client_id": 40,
  "name": "Клиент для заявок",
  "email": "",
  "address": "",
  "phone": "",
  "description": "",
  "enabled": true,
  "date_created": "2026-11-20 16:49:57.811433+00:00",
  "created_by_admin": 181
}
```


### Пользователи клиента
#### Обычный пользователь
**Роль:**  Обычный пользователь
```json
{
  "employee_id": 226,
  "first_name": "Обычный пользователь клиента",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "standard_client_user",
  "enabled_login": true,
  "date_created": "2026-11-20 19:53:56.816347",
  "roles": [
    87
  ],
  "client_id": 40
}

```
#### Главный пользователь
**Роль:**  Обычный пользователь, Главный пользователь
```json
{
  "employee_id": 227,
  "first_name": "Главный пользователь клиента",
  "last_name": "",
  "enabled": true,
  "email": "",
  "phone": "",
  "login": "chief_client_user",
  "enabled_login": true,
  "date_created": "2026-11-20 19:54:58.990940",
  "roles": [
    88,
    87
  ],
  "client_id": 40
}
```
## Заявки
### Заявки без участия пользователей

#### Заявка сделанная опытным инженером
##### заявка выполненная
1) Заявка создается
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 0,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-21T08:11:19.309000Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 0,
  "is_closed": false,
  "time_spent": 0,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "Комментарий"
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}

```

2) Менеджер указывае запланированное время
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 0,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 0,
  "is_closed": false,
  "time_spent": 0,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}
```
3) Менеджер назначает исполнителя
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 0,
  "is_closed": false,
  "time_spent": 0,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}
```

```json
    {
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 221,
  "last_executor_id": 221,
  "is_closed": false,
  "time_spent": 0,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    },
    {
      "id": 209,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:46:54.896572Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}
```

4) Исполнитель берет в работу
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 221,
  "last_executor_id": 221,
  "is_closed": false,
  "time_spent": 0,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    },
    {
      "id": 209,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:46:54.896572Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 210,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:49:19.630391Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}
```

5) Исполнитель завершает работу
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 221,
  "last_executor_id": 221,
  "is_closed": false,
  "time_spent": 61,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    },
    {
      "id": 209,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:46:54.896572Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 210,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:49:19.630391Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 211,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:50:20.684026Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "Не успел доделать"
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}
```

6) Менеджер переводит в принято
7) Менеджер назначает нового исполнителя
8) Менеджер назначает нового исполнителя
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 223,
  "last_executor_id": 223,
  "is_closed": false,
  "time_spent": 73,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    },
    {
      "id": 209,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:46:54.896572Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 210,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:49:19.630391Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 211,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:50:20.684026Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 212,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:53:53.365609Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 213,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-21T09:58:19.082913Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 214,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:00:32.689797Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 215,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:01:30.688610Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 216,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:01:38.530648Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 217,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:05:08.986762Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 218,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:06:32.641874Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 219,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:08:13.764857Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 220,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:08:19.221327Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 221,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-21T10:35:23.713850Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "не хватило времени"
      }
    },
    {
      "id": 222,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-21T10:37:09.410523Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "теперь попробуем инженера с ролью удаленщика"
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}

```
9) Исполнитель закрывает работу задним числом
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": null,
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 223,
  "last_executor_id": 223,
  "is_closed": false,
  "time_spent": 653,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    },
    {
      "id": 209,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:46:54.896572Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 210,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:49:19.630391Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 211,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:50:20.684026Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 212,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:53:53.365609Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 213,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-21T09:58:19.082913Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 214,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:00:32.689797Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 215,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:01:30.688610Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 216,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:01:38.530648Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 217,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:05:08.986762Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 218,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:06:32.641874Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 219,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:08:13.764857Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 220,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:08:19.221327Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 221,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-21T10:35:23.713850Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "не хватило времени"
      }
    },
    {
      "id": 222,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-21T10:37:09.410523Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "теперь попробуем инженера с ролью удаленщика"
      }
    },
    {
      "id": 223,
      "status": "at_work",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:02:12.532173Z",
      "actual_started_at": "2026-11-21T09:50:27.175000Z",
      "actual_finished_at": "2026-11-21T09:58:27.175000Z",
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 224,
      "status": "ready_for_review",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:02:12.532173Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 225,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-21T11:03:50.586964Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 226,
      "status": "at_work",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:06:15.687489Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT1M40S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 227,
      "status": "ready_for_review",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:06:15.687489Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}
```
10) Опытный инженер подтверждает работу
```json
{
  "ticket_id": 41,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная опытным инженером, без участи пользователей клиента. Например, для наших задач",
  "description": "Описание заявки",
  "date_created": "2026-11-21T08:13:03.516555Z",
  "date_finished": "2026-11-21T11:08:19.755078Z",
  "planned_at": "2026-11-22T08:13:03.516555Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 223,
  "is_closed": true,
  "time_spent": 653,
  "statuses": [
    {
      "id": 207,
      "status": "created",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516555Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 208,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T08:13:03.516772Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Комментарий"
      }
    },
    {
      "id": 209,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:46:54.896572Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 210,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:49:19.630391Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 211,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T09:50:20.684026Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 212,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T09:53:53.365609Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 213,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-21T09:58:19.082913Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 214,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:00:32.689797Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 215,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:01:30.688610Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 216,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:01:38.530648Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 217,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:05:08.986762Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 218,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 221,
      "date_created": "2026-11-21T10:06:32.641874Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 219,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:08:13.764857Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 220,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-21T10:08:19.221327Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Не успел доделать"
      }
    },
    {
      "id": 221,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-21T10:35:23.713850Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "не хватило времени"
      }
    },
    {
      "id": 222,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-21T10:37:09.410523Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "теперь попробуем инженера с ролью удаленщика"
      }
    },
    {
      "id": 223,
      "status": "at_work",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:02:12.532173Z",
      "actual_started_at": "2026-11-21T09:50:27.175000Z",
      "actual_finished_at": "2026-11-21T09:58:27.175000Z",
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 224,
      "status": "ready_for_review",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:02:12.532173Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 225,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-21T11:03:50.586964Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 226,
      "status": "at_work",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:06:15.687489Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT1M40S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 227,
      "status": "ready_for_review",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-21T11:06:15.687489Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 228,
      "status": "executed",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-21T11:08:19.755078Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "Сделали заявку"
      }
    }
  ],
  "comments": [
    {
      "id": 15,
      "actor_id": 222,
      "comment": {
        "value": "Комментарий"
      },
      "date_created": "2026-11-21T08:13:03.516555Z"
    }
  ]
}
```
##### Заявка снятая
1) Заявка создается
2) Менеджер назначает исполнителя
3) Менеджер снимает заявку
```json
{
  "ticket_id": 42,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка которую надо будет снять",
  "description": "",
  "date_created": "2026-11-22T10:57:21.313425Z",
  "date_finished": "2026-11-22T11:02:21.531313Z",
  "planned_at": "2026-11-22T10:56:19.404000Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 223,
  "is_closed": true,
  "time_spent": 0,
  "statuses": [
    {
      "id": 229,
      "status": "created",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T10:57:21.313425Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 230,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T10:57:26.721422Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 231,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-22T10:59:58.878514Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 232,
      "status": "deferred",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T11:00:43.031517Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Пока отложим"
      }
    },
    {
      "id": 233,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-22T11:00:53.611424Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 234,
      "status": "cancelled",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T11:02:21.531313Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "Заявку снимаем"
      }
    }
  ],
  "comments": []
}
```

#### Заявка сделанная обычным инженером
1) Заявка создается
2) Менеджер подтверждает
3) Исполнитель берет в работу
4) Исполнитель завершает работу
5) Менеджер переводит в принято
6) Менеджер назначает нового исполнителя
7) Менеджер назначает нового исполнителя
8) Исполнитель начинает работу
9) Исполнитель ставит на паузу
10) Исполнитель продолжает
11) Исполнитель завершает работу
12) Менеджер подтверждает работу
```json
{
  "ticket_id": 43,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная инженером",
  "description": "",
  "date_created": "2026-11-22T11:24:51.293828Z",
  "date_finished": "2026-11-22T11:36:24.640813Z",
  "planned_at": "2026-11-22T10:56:19.404000Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 223,
  "is_closed": true,
  "time_spent": 3500,
  "statuses": [
    {
      "id": 235,
      "status": "created",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-22T11:24:51.293828Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 236,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T11:30:53.367165Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 237,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-22T11:31:20.671847Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 238,
      "status": "at_work",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-22T11:33:02.891017Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT58M20S",
      "work_is_remote": true,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 239,
      "status": "ready_for_review",
      "actor_id": 221,
      "executor_id": 0,
      "date_created": "2026-11-22T11:33:02.891017Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 240,
      "status": "executed",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T11:36:24.640813Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": []
} 
```


#### Заявка сделанная менеджером
1) Заявка создается 
2) Указывается отдел
3) Менеджер назначает исполнителя
4) Исполнитель завершает работу
5) Опытный инженер подтверждает
```json
{
  "ticket_id": 44,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка созданная менеджером",
  "description": "",
  "date_created": "2026-11-22T12:00:26.135715Z",
  "date_finished": "2026-11-22T12:06:10.358214Z",
  "planned_at": "2026-11-22T10:56:19.404000Z",
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 222,
  "is_closed": true,
  "time_spent": 46,
  "statuses": [
    {
      "id": 241,
      "status": "created",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:00:26.135715Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 242,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:00:29.019513Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 243,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 222,
      "date_created": "2026-11-22T12:02:40.155294Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Будет выполнять опытный инженер"
      }
    },
    {
      "id": 244,
      "status": "at_work",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:03:33.191280Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 245,
      "status": "paused",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:04:07.042305Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "на паузу"
      }
    },
    {
      "id": 246,
      "status": "at_work",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:04:46.814998Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Возвращаем в работу"
      }
    },
    {
      "id": 247,
      "status": "ready_for_review",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:05:00.121206Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 248,
      "status": "executed",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:06:10.358214Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "Сам подтвердил свою работу"
      }
    }
  ],
  "comments": []
}
```


#### Заявка сделанная менеджером с рекомендацией удаленной работы
1) Заявка создается
2) Менеджер подтверждает
3) Исполнитель берет в работу горячей линии
4) Исполнитель завершает работу
5) Опытный инженер подтверждает
```json
{
  "ticket_id": 45,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 2,
  "text_of_ticket": "Заявка для горячей линии",
  "description": "",
  "date_created": "2026-11-22T12:08:30.666317Z",
  "date_finished": "2026-11-22T12:13:59.148023Z",
  "planned_at": "2026-11-22T10:56:19.404000Z",
  "remote_work_recommended": true,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 223,
  "is_closed": true,
  "time_spent": 112,
  "statuses": [
    {
      "id": 249,
      "status": "created",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:08:30.666317Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 250,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:08:34.795039Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 251,
      "status": "assigned",
      "actor_id": 223,
      "executor_id": 223,
      "date_created": "2026-11-22T12:10:35.151404Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 252,
      "status": "at_work",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-22T12:10:35.151404Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": true,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 253,
      "status": "ready_for_review",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-22T12:12:27.265240Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Завершаем заявку на горячей линии"
      }
    },
    {
      "id": 254,
      "status": "executed",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:13:59.148023Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "Подтверждение заявки на горячей линнии"
      }
    }
  ],
  "comments": []
}
```
#### Заявка сделанная обычным сотрудником
1) Заявка создается без отдела
2) Менеджер подтверждает
3) Менеджер указывает отдела
4) Исполнитель берет в горячей линии
5) Исполнитель завершает работу
6) Менеджер переводит в принято
7) Менеджер меняет отдел
8) Исполнитель берет в работу
9) Исполнитель завершает
10) Опытный инженер подтверждает
```json
{
  "ticket_id": 46,
  "client_id": 40,
  "user_id": 0,
  "contact_user_id": 0,
  "user_ticket_id": 0,
  "department_id": 5,
  "text_of_ticket": "Заявка созданная обычным пользователем",
  "description": "Я не знаю, позвонили, я внес",
  "date_created": "2026-11-22T12:17:00.532461Z",
  "date_finished": "2026-11-22T12:42:24.977757Z",
  "planned_at": "2026-11-22T10:56:19.404000Z",
  "remote_work_recommended": true,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 228,
  "is_closed": true,
  "time_spent": 3611,
  "statuses": [
    {
      "id": 255,
      "status": "created",
      "actor_id": 220,
      "executor_id": 0,
      "date_created": "2026-11-22T12:17:00.532461Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 256,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:18:08.811201Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 257,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 222,
      "date_created": "2026-11-22T12:31:16.825126Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": "Будет выполнять опытный инженер"
      }
    },
    {
      "id": 258,
      "status": "at_work",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:36:52.227833Z",
      "actual_started_at": "2026-11-22T11:36:32.780000Z",
      "actual_finished_at": "2026-11-22T12:36:32.780000Z",
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 259,
      "status": "ready_for_review",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:36:52.227833Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 260,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:39:14.077503Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 261,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 228,
      "date_created": "2026-11-22T12:40:02.520113Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 262,
      "status": "at_work",
      "actor_id": 228,
      "executor_id": 0,
      "date_created": "2026-11-22T12:41:17.367461Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 263,
      "status": "ready_for_review",
      "actor_id": 228,
      "executor_id": 0,
      "date_created": "2026-11-22T12:41:29.220774Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 264,
      "status": "executed",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T12:42:24.977757Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": []
}
```
### Заявка сделанная по запросу пользователя


#### Заявка записанная опытным инженером
1) Опытный инженер принимает заявку
2) Менеджер назначает исполнителя
3) Исполнитель берет заявку в работу
4) Исполнитель завершает
5) Менеджер назначает исполнителя
6) Исполнитель берет заявку в работу
7) Исполнитель завершает
8) Менеджер подтверждает
```json
{
  "ticket_user_id": 19,
  "client_id": 40,
  "user_id": 226,
  "contact_user_id": 226,
  "text_of_ticket": "Нам позвонил пользователь клиента",
  "description": "",
  "current_status": "confirmed_by_admin",
  "date_created": "2026-11-22T12:46:09.703393Z",
  "date_finished": "2026-11-22T17:47:10.082114Z",
  "is_closed": true,
  "statuses": [
    {
      "id": 95,
      "status": "created",
      "actor_id": 226,
      "comment": "",
      "date_created": "2026-11-22T12:46:09.703393Z"
    },
    {
      "id": 96,
      "status": "in_work",
      "actor_id": 222,
      "comment": "",
      "date_created": "2026-11-22T12:46:14.070439Z"
    },
    {
      "id": 103,
      "status": "waiting_for_confirmation",
      "actor_id": 223,
      "comment": "",
      "date_created": "2026-11-22T17:45:59.932497Z"
    },
    {
      "id": 104,
      "status": "confirmed_by_admin",
      "actor_id": 224,
      "comment": "",
      "date_created": "2026-11-22T17:47:10.082114Z"
    }
  ],
  "comments": []
}

```

```json
{
  "ticket_id": 47,
  "client_id": 40,
  "user_id": 226,
  "contact_user_id": 226,
  "user_ticket_id": 19,
  "department_id": 2,
  "text_of_ticket": "Нам позвонил пользователь клиента",
  "description": "",
  "date_created": "2026-11-22T12:46:09.704317Z",
  "date_finished": "2026-11-22T17:47:10.081904Z",
  "planned_at": "2026-11-22T12:44:11.813000Z",
  "remote_work_recommended": true,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 223,
  "is_closed": true,
  "time_spent": 10,
  "statuses": [
    {
      "id": 265,
      "status": "created_from_request_user",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:46:09.704317Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 266,
      "status": "accepted",
      "actor_id": 222,
      "executor_id": 0,
      "date_created": "2026-11-22T12:46:14.070085Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 279,
      "status": "assigned",
      "actor_id": 223,
      "executor_id": 223,
      "date_created": "2026-11-22T17:45:49.184380Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 280,
      "status": "at_work",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-22T17:45:49.184380Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": true,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 281,
      "status": "ready_for_review",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-22T17:45:59.932344Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 282,
      "status": "executed",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T17:47:10.081904Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": []
}

```


#### Заявка записанная обычным инженером
1) Инженер принимает заявку
2) Менеджер отказывает
#### Заявка записанная менеджером
1) Менеджер принимает заявку с указанием отдела
2) Менеджер назначает испонителя
3) Исполнитель берет заявку в работу
4) Исполнитель завершает работу
5) Пользователь подтверждает
#### Заявка записанная менеджером с рекомендацией удаленной работы
1) Менеджер принимает заявку с указанием отдела
2) Менеджер назначает заявку на горячую линию
3) Исполнитель берет заявку в работу
4) Исполнитель завершает работу
5) Менеджер подтверждает

### Заявки сделанные пользователем
#### Заявка сделанная главным пользователем
##### Заявка снятая пользователем
1) Пользователь делает заявку
2) Пользователь ее снимает
```json
{
  "ticket_user_id": 22,
  "client_id": 40,
  "user_id": 227,
  "contact_user_id": 227,
  "text_of_ticket": "Эту заявку нужно снять",
  "description": "",
  "current_status": "cancelled_by_admin",
  "date_created": "2026-11-22T17:50:53.731051Z",
  "date_finished": "2026-11-22T17:53:34.628188Z",
  "is_closed": true,
  "statuses": [
    {
      "id": 105,
      "status": "created",
      "actor_id": 227,
      "comment": "",
      "date_created": "2026-11-22T17:50:53.731051Z"
    },
    {
      "id": 107,
      "status": "cancelled_by_admin",
      "actor_id": 224,
      "comment": "Отказали",
      "date_created": "2026-11-22T17:53:34.628188Z"
    }
  ],
  "comments": []
}
```

```json
{
  "ticket_id": 50,
  "client_id": 40,
  "user_id": 227,
  "contact_user_id": 227,
  "user_ticket_id": 22,
  "department_id": 0,
  "text_of_ticket": "Эту заявку нужно снять",
  "description": "",
  "date_created": "2026-11-22T17:50:53.731378Z",
  "date_finished": "2026-11-22T17:53:34.628046Z",
  "planned_at": null,
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 0,
  "is_closed": true,
  "time_spent": 0,
  "statuses": [
    {
      "id": 283,
      "status": "created_from_ticket_user",
      "actor_id": 0,
      "executor_id": 0,
      "date_created": "2026-11-22T17:50:53.731378Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 285,
      "status": "rejected",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T17:53:34.628046Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": null,
      "comment": {
        "value": "Отказали"
      }
    }
  ],
  "comments": []
}
```
##### Заявка сделанная пользователем взятая в работу
1) Пользователь делает заявку
2) Менеджер ее подтверждает
3) Менеджер снимает ее

#### Заявка сделанная обычным пользователем
##### Заявка снятая главным пользователем
1) Пользователь делает заявку
2) Главный пользователь снимает ее
```json
{
  "ticket_user_id": 20,
  "client_id": 40,
  "user_id": 226,
  "contact_user_id": 226,
  "text_of_ticket": "Пользователь клиента делает заявку",
  "description": "",
  "current_status": "cancelled_by_user",
  "date_created": "2026-11-22T17:06:02.665139Z",
  "date_finished": "2026-11-22T17:37:33.927695Z",
  "is_closed": true,
  "statuses": [
    {
      "id": 97,
      "status": "created",
      "actor_id": 226,
      "comment": "",
      "date_created": "2026-11-22T17:06:02.665139Z"
    },
    {
      "id": 102,
      "status": "cancelled_by_user",
      "actor_id": 227,
      "comment": "",
      "date_created": "2026-11-22T17:37:33.927695Z"
    }
  ],
  "comments": []
}


```
```json
{
  "ticket_id": 48,
  "client_id": 40,
  "user_id": 226,
  "contact_user_id": 226,
  "user_ticket_id": 20,
  "department_id": 0,
  "text_of_ticket": "Пользователь клиента делает заявку",
  "description": "",
  "date_created": "2026-11-22T17:06:02.665451Z",
  "date_finished": "2026-11-22T17:37:33.927763Z",
  "planned_at": null,
  "remote_work_recommended": false,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 0,
  "is_closed": true,
  "time_spent": 0,
  "statuses": [
    {
      "id": 271,
      "status": "created_from_ticket_user",
      "actor_id": 0,
      "executor_id": 0,
      "date_created": "2026-11-22T17:06:02.665451Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 278,
      "status": "cancelled_by_user",
      "actor_id": 0,
      "executor_id": 0,
      "date_created": "2026-11-22T17:37:33.927763Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": []
}

```

##### Заявка подтвержденная пользователем
1) Пользователь делает заявку
2) Менеджер подтверждает
3) Менеджер назначает на горячую линию
4) Исполнитель берет в работу
5) Исполнитель завершает
6) Пользователь подтверждает
```json
{
  "ticket_user_id": 21,
  "client_id": 40,
  "user_id": 226,
  "contact_user_id": 226,
  "text_of_ticket": "Пользователь клиента делает заявку еще раз",
  "description": "",
  "current_status": "confirmed_by_user",
  "date_created": "2026-11-22T17:09:18.210078Z",
  "date_finished": "2026-11-22T17:26:21.326405Z",
  "is_closed": true,
  "statuses": [
    {
      "id": 98,
      "status": "created",
      "actor_id": 226,
      "comment": "",
      "date_created": "2026-11-22T17:09:18.210078Z"
    },
    {
      "id": 99,
      "status": "in_work",
      "actor_id": 224,
      "comment": "",
      "date_created": "2026-11-22T17:14:58.826561Z"
    },
    {
      "id": 100,
      "status": "waiting_for_confirmation",
      "actor_id": 223,
      "comment": "",
      "date_created": "2026-11-22T17:21:40.275445Z"
    },
    {
      "id": 101,
      "status": "confirmed_by_user",
      "actor_id": 226,
      "comment": "",
      "date_created": "2026-11-22T17:26:21.326405Z"
    }
  ],
  "comments": []
}
```

```json
{
  "ticket_id": 49,
  "client_id": 40,
  "user_id": 226,
  "contact_user_id": 226,
  "user_ticket_id": 21,
  "department_id": 2,
  "text_of_ticket": "Пользователь клиента делает заявку еще раз",
  "description": "",
  "date_created": "2026-11-22T17:09:18.211010Z",
  "date_finished": "2026-11-22T17:26:22.203609Z",
  "planned_at": null,
  "remote_work_recommended": true,
  "urgency": "normal",
  "current_executor_id": 0,
  "last_executor_id": 223,
  "is_closed": true,
  "time_spent": 85,
  "statuses": [
    {
      "id": 272,
      "status": "created_from_ticket_user",
      "actor_id": 0,
      "executor_id": 0,
      "date_created": "2026-11-22T17:09:18.211010Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 273,
      "status": "accepted",
      "actor_id": 224,
      "executor_id": 0,
      "date_created": "2026-11-22T17:14:58.826220Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 274,
      "status": "assigned",
      "actor_id": 224,
      "executor_id": 223,
      "date_created": "2026-11-22T17:17:21.572011Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 275,
      "status": "at_work",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-22T17:20:15.126673Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": true,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 276,
      "status": "ready_for_review",
      "actor_id": 223,
      "executor_id": 0,
      "date_created": "2026-11-22T17:21:40.275342Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    },
    {
      "id": 277,
      "status": "confirmed_by_user",
      "actor_id": 0,
      "executor_id": 0,
      "date_created": "2026-11-22T17:26:22.203609Z",
      "actual_started_at": null,
      "actual_finished_at": null,
      "duration": "PT0S",
      "work_is_remote": false,
      "comment": {
        "value": ""
      }
    }
  ],
  "comments": []
}
```


##### Заявка подтвержденная менеджером
1) Пользователь делает заявку
2) Менеджер подтверждает
3) Менеджер назначает на горячую линию
4) Исполнитель берет в работу
5) Исполнитель завершает
6) Менеджер подтверждает







