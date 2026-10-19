#src/domain/rbac/permissions.py

from enum import StrEnum
# ---------------------------
# Permissions (separate forever)
# ---------------------------


class PermissionBase(StrEnum):
    """Stable string identifiers (DB-friendly)."""
    pass


class AdminPermission(PermissionBase):
    CLIENT_OPERATION = "client.operation"                           # операции с клиентами
    CLIENT_VIEW = "client.view"                                     # просмотр клиентов
    CLIENT_DECISION = "client.decision"                             # решения по клиенту
    CLIENT_CREATE = "client.create"                                 # создание клиента
    ADMIN_OPERATION="admin.operation"                               # операции с admin-ами
    ADMIN_VIEW="admin.view"                                         # просмотр admin-ов
    DEPARTMENT_OPERATION="department.operation"                     # операции с отделами
    DEPARTMENT_VIEW="department.view"                               # просмотр отделов
    USER_OPERATION="user.operation"                                 # операции с пользователями
    USER_VIEW="user.view"                                           # просмотр пользователей
    TICKET_OPERATION="ticket.operation"                             # общие операции с заявками
    TICKET_CREATED="ticket.created"                                 # может создавать заявки
    TICKET_VIEW = "ticket.view"                                     # просмотр заявок
    TICKET_ACCEPTED = "ticket.accepted"                             # имеет право подтверждать заявки
    TICKET_AT_WORK = "ticket.at_work"                               # имеет право выполнять заявки
    TICKET_AT_WORK_REMOTE = "ticket.at_work_remote"                 # имеет право выполнять заявки, который рекомендованы как удаленные
    TICKET_AT_WORK_RETROSPECTIVE = "ticket.at_work_retrospective"   # имеет право вносить данные по работе ретроспективно
    TICKET_CANCELLED="ticket.canceled"                              # имеет право снимать заявки cancel или reject
    TICKET_EXECUTED = "ticket.executed"                             # имеет право переводить в executed
    ROLE_ASSIGN="role.assign"                                       # имеет право работать с ролями Admin-ов
    ROLE_USER_ASSIGN = "role_user.assign"                           # имеет право работать с ролями User-ов






class UserPermission(PermissionBase):
    TICKET_OPERATION = "ticket.operation"                           # имеет право работать со своим заявками
    TICKET_OPERATION_ALL="ticket.operation.all"                     # имеет право работать со всеми заявками организации
    TICKET_VIEW = "ticket.view"                                     # имеет право смотреть свои заявки
    TICKET_VIEW_ALL = "ticket.view.all"                             # имеет право смотреть заявки организации



