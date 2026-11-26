# Контракт HTTP API

Статический реестр на `88e8bfb573541774ca51eead8ca4d11b5475cd38`. Код API идентичен в `5e2a8e6`. Схемы и права сверены по обработчикам, моделям и сервисам. Контрактные тесты предусмотрены отдельным этапом. Контур User приведён для полноты реестра (DEC-001, DEC-002).

## Реестр (107 операций)

P — path, Q — query, H — header, F — form, B — JSON body. Символ `?` у заголовка означает необязательный параметр. Для любого `/admin/*` требуется действующий Bearer Admin, для `/user/tickets/*` — действующий Bearer User. ID актёра извлекается сервером. Пустой столбец обозначен «—». URL указан с точным завершающим слешем. Регистрация роутеров и стандартные маршруты OpenAPI и документации заданы в [create_app](../../src/web/main.py#L37). Маршруты документации FastAPI учитываются отдельно.

### /health (1)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `GET /health` | — | 200 `{status: string}` | Публичный | [health_check](../../src/web/main.py#L95) |

### /admin/admins (18)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /admin/admins/` | H `Idempotency-Key?`, B `AdminCreateRequest` | 201 `AdminResponse` | admin.operation, с roles также role.assign | [create_admin](../../src/web/routers/admin/admins.py#L70) |
| `GET /admin/admins/` | — | 200 `list[AdminResponse]` | admin.view | [get_all_admins](../../src/web/routers/admin/admins.py#L99) |
| `GET /admin/admins/permissions` | — | 200 `PermissionsResponse` | Действующий Admin | [get_permissions](../../src/web/routers/admin/admins.py#L117) |
| `GET /admin/admins/by-login/{login}` | P `login str` | 200 `AdminResponse` | admin.view | [find_admin_by_login](../../src/web/routers/admin/admins.py#L140) |
| `GET /admin/admins/{employee_id}` | P `employee_id int` | 200 `AdminResponse` | admin.view | [get_admin](../../src/web/routers/admin/admins.py#L162) |
| `PUT /admin/admins/{employee_id}` | P `employee_id int`, B `AdminUpdateRequest` | 200 `AdminResponse` | admin.operation | [update_admin](../../src/web/routers/admin/admins.py#L184) |
| `POST /admin/admins/{employee_id}/account` | P `employee_id int`, B `AdminAttachAccountRequest` | 200 `AdminResponse` | admin.operation | [attach_account](../../src/web/routers/admin/admins.py#L208) |
| `DELETE /admin/admins/{employee_id}/account` | P `employee_id int` | 200 `AdminResponse` | admin.operation | [detach_account](../../src/web/routers/admin/admins.py#L232) |
| `PATCH /admin/admins/{employee_id}/account/enable` | P `employee_id int` | 200 `AdminResponse` | admin.operation | [enable_account](../../src/web/routers/admin/admins.py#L253) |
| `PATCH /admin/admins/{employee_id}/account/disable` | P `employee_id int` | 200 `AdminResponse` | admin.operation | [disable_account](../../src/web/routers/admin/admins.py#L275) |
| `PATCH /admin/admins/{employee_id}/password` | P `employee_id int`, B `AdminChangePasswordRequest` | 200 `AdminResponse` | admin.operation | [change_password](../../src/web/routers/admin/admins.py#L303) |
| `POST /admin/admins/{employee_id}/roles` | P `employee_id int`, B `AdminRolesRequest` | 200 `AdminResponse` | role.assign | [grant_roles](../../src/web/routers/admin/admins.py#L327) |
| `DELETE /admin/admins/{employee_id}/roles` | P `employee_id int`, B `AdminRolesRequest` | 200 `AdminResponse` | role.assign | [revoke_roles](../../src/web/routers/admin/admins.py#L351) |
| `PATCH /admin/admins/{employee_id}/disable` | P `employee_id int` | 200 `AdminResponse` | admin.operation | [disable_admin](../../src/web/routers/admin/admins.py#L371) |
| `PATCH /admin/admins/{employee_id}/enable` | P `employee_id int` | 200 `AdminResponse` | admin.operation | [enable_admin](../../src/web/routers/admin/admins.py#L393) |
| `DELETE /admin/admins/{employee_id}` | P `employee_id int` | 204 — | admin.operation | [delete_admin](../../src/web/routers/admin/admins.py#L415) |
| `PATCH /admin/admins/{employee_id}/department` | P `employee_id int`, B `AdminChangeDepartmentRequest` | 200 `AdminResponse` | admin.operation | [change_admin_department](../../src/web/routers/admin/admins.py#L435) |
| `DELETE /admin/admins/{employee_id}/department` | P `employee_id int` | 200 `AdminResponse` | admin.operation | [remove_admin_department](../../src/web/routers/admin/admins.py#L457) |

### /admin/clients (7)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /admin/clients/` | H `Idempotency-Key?`, B `ClientCreateRequest` | 201 `ClientResponse` | client.create / client.operation / client.decision | [create_client](../../src/web/routers/admin/clients.py#L84) |
| `GET /admin/clients/` | — | 200 `list[ClientResponse]` | client.view | [get_all_clients](../../src/web/routers/admin/clients.py#L113) |
| `GET /admin/clients/{client_id}` | P `client_id int` | 200 `ClientResponse` | client.view | [get_client](../../src/web/routers/admin/clients.py#L132) |
| `PUT /admin/clients/{client_id}/contact` | P `client_id int`, B `ClientUpdateContactRequest` | 200 `ClientResponse` | client.operation | [update_contact](../../src/web/routers/admin/clients.py#L154) |
| `PATCH /admin/clients/{client_id}/disable` | P `client_id int` | 200 `ClientResponse` | client.decision | [disable_client](../../src/web/routers/admin/clients.py#L178) |
| `PATCH /admin/clients/{client_id}/enable` | P `client_id int` | 200 `ClientResponse` | client.decision | [enable_client](../../src/web/routers/admin/clients.py#L200) |
| `DELETE /admin/clients/{client_id}` | P `client_id int` | 204 — | client.operation | [delete_client](../../src/web/routers/admin/clients.py#L222) |

### /admin/departments (7)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /admin/departments/` | H `Idempotency-Key?`, B `DepartmentCreateRequest` | 201 `DepartmentResponse` | department.operation | [create_department](../../src/web/routers/admin/departments.py#L65) |
| `GET /admin/departments/` | — | 200 `list[DepartmentResponse]` | department.view | [get_all_departments](../../src/web/routers/admin/departments.py#L92) |
| `GET /admin/departments/{department_id}` | P `department_id Annotated[int, Path(gt=0)]` | 200 `DepartmentResponse` | department.view | [get_department](../../src/web/routers/admin/departments.py#L112) |
| `PUT /admin/departments/{department_id}` | P `department_id Annotated[int, Path(gt=0)]`, B `DepartmentUpdateRequest` | 200 `DepartmentResponse` | department.operation | [update_department](../../src/web/routers/admin/departments.py#L133) |
| `PATCH /admin/departments/{department_id}/enable` | P `department_id Annotated[int, Path(gt=0)]` | 200 `DepartmentResponse` | department.operation | [enable_department](../../src/web/routers/admin/departments.py#L158) |
| `PATCH /admin/departments/{department_id}/disable` | P `department_id Annotated[int, Path(gt=0)]` | 200 `DepartmentResponse` | department.operation | [disable_department](../../src/web/routers/admin/departments.py#L179) |
| `DELETE /admin/departments/{department_id}` | P `department_id Annotated[int, Path(gt=0)]` | 204 — | department.operation | [delete_department](../../src/web/routers/admin/departments.py#L201) |

### /admin/roles (10)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `GET /admin/roles/admin/permissions` | — | 200 `list[AdminPermission]` | Действующий Admin | [get_admin_permissions](../../src/web/routers/admin/roles.py#L64) |
| `GET /admin/roles/user/permissions` | — | 200 `list[UserPermission]` | Действующий Admin | [get_user_permissions](../../src/web/routers/admin/roles.py#L74) |
| `POST /admin/roles/admin` | H `Idempotency-Key?`, B `AdminRoleCreateRequest` | 201 `AdminRoleResponse` | role.assign | [create_admin_role](../../src/web/routers/admin/roles.py#L104) |
| `GET /admin/roles/admin` | — | 200 `list[AdminRoleResponse]` | role.assign | [get_all_admin_roles](../../src/web/routers/admin/roles.py#L132) |
| `GET /admin/roles/admin/{role_id}` | P `role_id int` | 200 `AdminRoleResponse` | role.assign | [get_admin_role](../../src/web/routers/admin/roles.py#L153) |
| `DELETE /admin/roles/admin/{role_id}` | P `role_id int` | 204 — | role.assign | [delete_admin_role](../../src/web/routers/admin/roles.py#L174) |
| `POST /admin/roles/user` | H `Idempotency-Key?`, B `UserRoleCreateRequest` | 201 `UserRoleResponse` | role_user.assign | [create_user_role](../../src/web/routers/admin/roles.py#L212) |
| `GET /admin/roles/user` | — | 200 `list[UserRoleResponse]` | role_user.assign | [get_all_user_roles](../../src/web/routers/admin/roles.py#L240) |
| `GET /admin/roles/user/{role_id}` | P `role_id int` | 200 `UserRoleResponse` | role_user.assign | [get_user_role](../../src/web/routers/admin/roles.py#L260) |
| `DELETE /admin/roles/user/{role_id}` | P `role_id int` | 204 — | role_user.assign | [delete_user_role](../../src/web/routers/admin/roles.py#L281) |

### /admin/tickets (31)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /admin/tickets/` | H `Idempotency-Key?`, B `TicketCreateRequest` | 201 `TicketResponse` | ticket.created / ticket.operation¹ | [create_ticket](../../src/web/routers/admin/tickets.py#L85) |
| `GET /admin/tickets/` | — | 200 `list[TicketResponse]` | ticket.view | [get_all_tickets](../../src/web/routers/admin/tickets.py#L123) |
| `GET /admin/tickets/open` | — | 200 `list[TicketResponse]` | ticket.view | [get_open_tickets](../../src/web/routers/admin/tickets.py#L151) |
| `GET /admin/tickets/closed` | — | 200 `list[TicketResponse]` | ticket.view | [get_closed_tickets](../../src/web/routers/admin/tickets.py#L179) |
| `GET /admin/tickets/by-client/{client_id}` | P `client_id int` | 200 `list[TicketResponse]` | ticket.view | [get_tickets_by_client](../../src/web/routers/admin/tickets.py#L207) |
| `GET /admin/tickets/by-user/{user_id}` | P `user_id int` | 200 `list[TicketResponse]` | ticket.view | [get_tickets_by_user](../../src/web/routers/admin/tickets.py#L237) |
| `GET /admin/tickets/by-contact-user/{contact_user_id}` | P `contact_user_id int` | 200 `list[TicketResponse]` | ticket.view | [get_tickets_by_contact_user](../../src/web/routers/admin/tickets.py#L267) |
| `GET /admin/tickets/by-department/{department_id}` | P `department_id int` | 200 `list[TicketResponse]` | ticket.view | [get_tickets_by_department](../../src/web/routers/admin/tickets.py#L297) |
| `GET /admin/tickets/by-executor/{executor_id}` | P `executor_id int` | 200 `list[TicketResponse]` | ticket.view | [get_tickets_by_current_executor](../../src/web/routers/admin/tickets.py#L327) |
| `GET /admin/tickets/{ticket_id}` | P `ticket_id int` | 200 `TicketResponse` | ticket.view | [get_ticket](../../src/web/routers/admin/tickets.py#L356) |
| `POST /admin/tickets/{ticket_id}/comments` | H `Idempotency-Key?`, P `ticket_id int`, B `TicketRequiredCommentRequest` | 200 `TicketResponse` | ticket.operation | [add_comment](../../src/web/routers/admin/tickets.py#L407) |
| `PATCH /admin/tickets/{ticket_id}/description` | P `ticket_id int`, B `TicketDescriptionRequest` | 200 `TicketResponse` | ticket.operation | [update_description](../../src/web/routers/admin/tickets.py#L442) |
| `PATCH /admin/tickets/{ticket_id}/contact-user` | P `ticket_id int`, B `TicketContactUserRequest` | 200 `TicketResponse` | ticket.operation | [change_contact_user](../../src/web/routers/admin/tickets.py#L476) |
| `PATCH /admin/tickets/{ticket_id}/department` | P `ticket_id int`, B `TicketChangeDepartmentRequest` | 200 `TicketResponse` | ticket.operation | [change_department](../../src/web/routers/admin/tickets.py#L511) |
| `PATCH /admin/tickets/{ticket_id}/remote-work-recommended` | P `ticket_id int`, B `TicketRemoteWorkRecommendationRequest` | 200 `TicketResponse` | ticket.set_remote_recommendation | [set_remote_work_recommended](../../src/web/routers/admin/tickets.py#L544) |
| `PATCH /admin/tickets/{ticket_id}/urgency` | P `ticket_id int`, B `TicketUrgencyRequest` | 200 `TicketResponse` | ticket.operation | [change_urgency](../../src/web/routers/admin/tickets.py#L578) |
| `PATCH /admin/tickets/{ticket_id}/schedule` | P `ticket_id int`, B `TicketScheduleRequest` | 200 `TicketResponse` | ticket.operation | [schedule_ticket](../../src/web/routers/admin/tickets.py#L617) |
| `DELETE /admin/tickets/{ticket_id}/schedule` | P `ticket_id int` | 200 `TicketResponse` | ticket.operation | [clear_ticket_schedule](../../src/web/routers/admin/tickets.py#L649) |
| `PATCH /admin/tickets/{ticket_id}/accept` | P `ticket_id int`, B `TicketAcceptRequest` | 200 `TicketResponse` | ticket.accepted | [accept_ticket](../../src/web/routers/admin/tickets.py#L686) |
| `PATCH /admin/tickets/{ticket_id}/reject` | P `ticket_id int`, B `TicketRejectRequest` | 200 `TicketResponse` | ticket.canceled | [reject_ticket](../../src/web/routers/admin/tickets.py#L719) |
| `PATCH /admin/tickets/{ticket_id}/defer` | P `ticket_id int`, B `TicketDeferRequest` | 200 `TicketResponse` | ticket.operation | [defer_ticket](../../src/web/routers/admin/tickets.py#L752) |
| `PATCH /admin/tickets/{ticket_id}/executor` | P `ticket_id int`, B `TicketAssignRequest` | 200 `TicketResponse` | ticket.assign_executor для другого Admin / ticket.at_work_remote для себя¹ | [assign_ticket](../../src/web/routers/admin/tickets.py#L783) |
| `PATCH /admin/tickets/{ticket_id}/start-work` | P `ticket_id int`, B `TicketStartWorkRequest` | 200 `TicketResponse` | ticket.at_work | [start_work](../../src/web/routers/admin/tickets.py#L820) |
| `PATCH /admin/tickets/{ticket_id}/start-remote-work` | P `ticket_id int`, B `TicketStartRemoteWorkRequest` | 200 `TicketResponse` | ticket.at_work_remote | [start_remote_work](../../src/web/routers/admin/tickets.py#L852) |
| `PATCH /admin/tickets/{ticket_id}/pause-work` | P `ticket_id int`, B `TicketPauseWorkRequest` | 200 `TicketResponse` | ticket.at_work / ticket.at_work_remote¹ | [pause_work](../../src/web/routers/admin/tickets.py#L884) |
| `PATCH /admin/tickets/{ticket_id}/resume-work` | P `ticket_id int`, B `TicketResumeWorkRequest` | 200 `TicketResponse` | ticket.at_work / ticket.at_work_remote¹ | [resume_work](../../src/web/routers/admin/tickets.py#L917) |
| `PATCH /admin/tickets/{ticket_id}/finish-work` | P `ticket_id int`, B `TicketFinishWorkRequest` | 200 `TicketResponse` | ticket.at_work / ticket.at_work_remote¹ | [finish_work](../../src/web/routers/admin/tickets.py#L950) |
| `PATCH /admin/tickets/{ticket_id}/complete-work-retroactively` | P `ticket_id int`, B `TicketCompleteWorkRetroactivelyRequest` | 200 `TicketResponse` | ticket.at_work_retrospective | [complete_work_retroactively](../../src/web/routers/admin/tickets.py#L982) |
| `PATCH /admin/tickets/{ticket_id}/execute` | P `ticket_id int`, B `TicketExecuteRequest` | 200 `TicketResponse` | ticket.executed | [execute_ticket](../../src/web/routers/admin/tickets.py#L1020) |
| `PATCH /admin/tickets/{ticket_id}/cancel` | P `ticket_id int`, B `TicketCancelRequest` | 200 `TicketResponse` | ticket.canceled | [cancel_ticket](../../src/web/routers/admin/tickets.py#L1052) |
| `DELETE /admin/tickets/{ticket_id}` | P `ticket_id int` | 204 — | ticket.delete | [delete_ticket](../../src/web/routers/admin/tickets.py#L1084) |

### /admin/users (16)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /admin/users/` | H `Idempotency-Key?`, B `UserCreateRequest` | 201 `UserResponse` | user.operation, с roles также role_user.assign | [create_user](../../src/web/routers/admin/users.py#L91) |
| `GET /admin/users/` | Q `client_id int = 0` | 200 `list[UserResponse]` | user.view | [get_all_users](../../src/web/routers/admin/users.py#L120) |
| `GET /admin/users/by-login/{login}` | P `login str` | 200 `UserResponse` | user.view | [find_user_by_login](../../src/web/routers/admin/users.py#L143) |
| `GET /admin/users/{employee_id}` | P `employee_id int` | 200 `UserResponse` | user.view | [get_user](../../src/web/routers/admin/users.py#L168) |
| `GET /admin/users/client/{client_id}` | P `client_id int` | 200 `list[UserResponse]` | user.view | [get_by_client](../../src/web/routers/admin/users.py#L188) |
| `PUT /admin/users/{employee_id}` | P `employee_id int`, B `UserUpdateRequest` | 200 `UserResponse` | user.operation | [update_user](../../src/web/routers/admin/users.py#L210) |
| `POST /admin/users/{employee_id}/account` | P `employee_id int`, B `UserAttachAccountRequest` | 200 `UserResponse` | user.operation | [attach_account](../../src/web/routers/admin/users.py#L231) |
| `DELETE /admin/users/{employee_id}/account` | P `employee_id int` | 200 `UserResponse` | user.operation | [detach_account](../../src/web/routers/admin/users.py#L252) |
| `PATCH /admin/users/{employee_id}/account/enable` | P `employee_id int` | 200 `UserResponse` | user.operation | [enable_account](../../src/web/routers/admin/users.py#L271) |
| `PATCH /admin/users/{employee_id}/account/disable` | P `employee_id int` | 200 `UserResponse` | user.operation | [disable_account](../../src/web/routers/admin/users.py#L293) |
| `PATCH /admin/users/{employee_id}/password` | P `employee_id int`, B `UserChangePasswordRequest` | 200 `UserResponse` | user.operation | [change_password](../../src/web/routers/admin/users.py#L318) |
| `POST /admin/users/{employee_id}/roles` | P `employee_id int`, B `UserRolesRequest` | 200 `UserResponse` | role_user.assign | [grant_roles](../../src/web/routers/admin/users.py#L338) |
| `DELETE /admin/users/{employee_id}/roles` | P `employee_id int`, B `UserRolesRequest` | 200 `UserResponse` | role_user.assign | [revoke_roles](../../src/web/routers/admin/users.py#L360) |
| `PATCH /admin/users/{employee_id}/disable` | P `employee_id int` | 200 `UserResponse` | user.operation | [disable_user](../../src/web/routers/admin/users.py#L380) |
| `PATCH /admin/users/{employee_id}/enable` | P `employee_id int` | 200 `UserResponse` | user.operation | [enable_user](../../src/web/routers/admin/users.py#L401) |
| `DELETE /admin/users/{employee_id}` | P `employee_id int` | 204 — | user.operation | [delete_user](../../src/web/routers/admin/users.py#L421) |

### /auth/admin (3)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /auth/admin/login` | F `OAuth2PasswordRequestForm` | 200 `TokenResponse` | Учётные данные | [login](../../src/web/routers/auth.py#L72) |
| `POST /auth/admin/refresh` | B `RefreshRequest` | 200 `TokenResponse` | Refresh текущего контура | [refresh](../../src/web/routers/auth.py#L83) |
| `POST /auth/admin/logout` | B `LogoutRequest`, H `Authorization?` | 200 `{message: string}` | Refresh или Bearer и username² | [logout](../../src/web/routers/auth.py#L93) |

### /auth/user (3)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /auth/user/login` | F `OAuth2PasswordRequestForm` | 200 `TokenResponse` | Учётные данные | [login_user](../../src/web/routers/auth.py#L107) |
| `POST /auth/user/refresh` | B `RefreshRequest` | 200 `TokenResponse` | Refresh текущего контура | [refresh_user](../../src/web/routers/auth.py#L118) |
| `POST /auth/user/logout` | B `LogoutRequest`, H `Authorization?` | 200 `{message: string}` | Refresh или Bearer и username² | [logout_user](../../src/web/routers/auth.py#L127) |

### /user/tickets (11)

| HTTP | Параметры | Успех | Допуск | Обработчик |
|---|---|---|---|---|
| `POST /user/tickets/` | H `Idempotency-Key?`, B `UserTicketCreateRequest` | 201 `TicketUserResponse` | User ticket.operation | [create_ticket](../../src/web/routers/user/tickets.py#L132) |
| `GET /user/tickets/` | — | 200 `list[TicketUserResponse]` | User ticket.view / ticket.view.all³ | [get_my_tickets](../../src/web/routers/user/tickets.py#L170) |
| `GET /user/tickets/all` | — | 200 `list[TicketUserResponse]` | User ticket.view.all | [get_all_tickets](../../src/web/routers/user/tickets.py#L199) |
| `GET /user/tickets/open` | — | 200 `list[TicketUserResponse]` | User ticket.view / ticket.view.all³ | [get_open_tickets](../../src/web/routers/user/tickets.py#L229) |
| `GET /user/tickets/closed` | — | 200 `list[TicketUserResponse]` | User ticket.view / ticket.view.all³ | [get_closed_tickets](../../src/web/routers/user/tickets.py#L258) |
| `GET /user/tickets/{ticket_user_id}` | P `ticket_user_id int` | 200 `TicketUserResponse` | User ticket.view / ticket.view.all³ | [get_ticket](../../src/web/routers/user/tickets.py#L287) |
| `POST /user/tickets/{ticket_user_id}/comments` | H `Idempotency-Key?`, P `ticket_user_id int`, B `UserTicketCommentRequest` | 200 `TicketUserResponse` | User ticket.operation / ticket.operation.all³ | [add_comment](../../src/web/routers/user/tickets.py#L337) |
| `PATCH /user/tickets/{ticket_user_id}/description` | P `ticket_user_id int`, B `UserTicketDescriptionRequest` | 200 `TicketUserResponse` | User ticket.operation / ticket.operation.all³ | [update_description](../../src/web/routers/user/tickets.py#L374) |
| `PATCH /user/tickets/{ticket_user_id}/contact-user` | P `ticket_user_id int`, B `UserTicketContactUserRequest` | 200 `TicketUserResponse` | User ticket.operation / ticket.operation.all³ | [change_contact_user](../../src/web/routers/user/tickets.py#L409) |
| `PATCH /user/tickets/{ticket_user_id}/cancel` | P `ticket_user_id int`, B `UserTicketActionRequest` | 200 `TicketUserResponse` | User ticket.operation / ticket.operation.all³ | [cancel_ticket](../../src/web/routers/user/tickets.py#L448) |
| `PATCH /user/tickets/{ticket_user_id}/confirm` | P `ticket_user_id int`, B `UserTicketActionRequest` | 200 `TicketUserResponse` | User ticket.operation / ticket.operation.all³ | [confirm_ticket](../../src/web/routers/user/tickets.py#L482) |

¹ Условные права и состояния перечислены в [PERMISSIONS_MATRIX.md](PERMISSIONS_MATRIX.md#действия-с-заявкой). При создании `remote_work_recommended=true` требуется `ticket.set_remote_recommendation`.

² `/logout` принимает JSON `LogoutRequest`. Основной сценарий v3 отправляет актуальный refresh текущей сессии. Режим отзыва всех сессий использует совпадающий `username` и валидный Bearer соответствующего субъекта. [AUTHENTICATION.md](AUTHENTICATION.md) · [SharedSessionAuthManager](../../src/web/auth/services/shared_sessions.py#L70).

³ User видит собственную заявку с `ticket.view` или `ticket.view.all`, чужую в своём клиенте — с `ticket.view.all`. GET `/user/tickets/` возвращает только собственные даже при `ticket.view.all`. `/all` ограничен текущим клиентом, `/open` и `/closed` выбирают scope по правам. Для изменения собственной действуют `ticket.operation` или `ticket.operation.all`, для чужой в своём клиенте — `ticket.operation.all`. Комментарии требуют нетерминального состояния, описание — `created`, контакт — `created` или `in_work` и проверку связанной заявки. Отмена начинается из `created`, подтверждение требует `waiting_for_confirmation` и связанной `ready_for_review`. [Сервис TicketUser](../../src/application/services/ticket_user_service.py#L210).

## Схемы запросов и ответов

JSON использует имена полей в таблице. `*` отмечает объявленное обязательное поле модели, без учёта дополнительных доменных правил. `set` и `tuple` сериализуются JSON-массивами. `datetime` — ISO 8601, `timedelta` — длительность в поддерживаемом Pydantic формате (клиент отправляет ISO 8601 duration). `null` соответствует типу `None`. В моделях команд Ticket с `extra=forbid` лишнее поле даёт 422. Маршруты с моделью тела требуют JSON-объект даже при всех полях с defaults. Для пустой команды передать `{}`. `Idempotency-Key` используется только там, где он отмечен в реестре.

| Схема | Поля и defaults |
|---|---|
| [RefreshRequest](../../src/web/auth/models.py#L4) | `refresh_token str` * |
| [LogoutRequest](../../src/web/auth/models.py#L8) | `refresh_token str = ''`, `username str = ''` |
| [TokenResponse](../../src/web/auth/models.py#L13) | `access_token str` *, `token_type str = 'bearer'`, `expires_in int` *, `refresh_token str` *, `scope str = ''` |
| [AdminCreateRequest](../../src/web/models/admins.py#L8) | `first_name str` *, `last_name str = ''`, `email str = ''`, `phone str = ''`, `job_title str = ''`, `login str = ''`, `password str = ''`, `enable_account bool = True`, `department_id int = 0`, `roles set[int] = Field(default_factory=set, examples=[[]])` |
| [AdminUpdateRequest](../../src/web/models/admins.py#L31) | `first_name str = ''`, `last_name str = ''`, `email str = ''`, `phone str = ''`, `job_title str = ''`, `department_id int = 0` |
| [AdminAttachAccountRequest](../../src/web/models/admins.py#L45) | `login str` *, `password str` *, `enable_account bool = True` |
| [AdminChangePasswordRequest](../../src/web/models/admins.py#L57) | `password str` * |
| [AdminRolesRequest](../../src/web/models/admins.py#L67) | `roles set[int] = Field(default_factory=set)` |
| [AdminChangeDepartmentRequest](../../src/web/models/admins.py#L77) | `department_id int = 0` |
| [AdminResponse](../../src/web/models/admins.py#L82) | `employee_id int` *, `first_name str = ''`, `last_name str = ''`, `enabled bool = True`, `email str = ''`, `phone str = ''`, `login str = ''`, `enabled_login bool = False`, `date_created str = ''`, `roles set[int] = Field(default_factory=set)`, `job_title str = ''`, `department_id int = 0` |
| [PermissionsResponse](../../src/web/models/admins.py#L133) | `permissions tuple[str, ...] = Field(default_factory=tuple)` |
| [ClientCreateRequest](../../src/web/models/clients.py#L8) | `name str` *, `email str = ''`, `address str = ''`, `phone str = ''`, `description str = ''` |
| [ClientUpdateContactRequest](../../src/web/models/clients.py#L27) | `name str = ''`, `email str = ''`, `address str = ''`, `phone str = ''`, `description str = ''` |
| [ClientResponse](../../src/web/models/clients.py#L35) | `client_id int` *, `name str` *, `email str = ''`, `address str = ''`, `phone str = ''`, `description str = ''`, `enabled bool` *, `date_created str` *, `created_by_admin int` * |
| [DepartmentCreateRequest](../../src/web/models/department.py#L10) | `name str` *, `enabled bool = True` |
| [DepartmentUpdateRequest](../../src/web/models/department.py#L24) | `name str` * |
| [DepartmentResponse](../../src/web/models/department.py#L34) | `department_id int` *, `name str` *, `enabled bool` *, `date_created datetime` * |
| [AdminRoleCreateRequest](../../src/web/models/roles.py#L15) | `name str` *, `permissions list[AdminPermission]` *, `description str = ''`, `is_system_role bool = False` |
| [AdminRoleResponse](../../src/web/models/roles.py#L50) | `role_id int` *, `name str` *, `permissions list[str]` *, `description str = ''`, `is_system_role bool` *, `date_created datetime` * |
| [UserRoleCreateRequest](../../src/web/models/roles.py#L70) | `name str` *, `permissions list[UserPermission]` *, `description str = ''`, `is_system_role bool = False` |
| [UserRoleResponse](../../src/web/models/roles.py#L106) | `role_id int` *, `name str` *, `permissions list[str]` *, `description str = ''`, `is_system_role bool` * |
| [TicketCreateRequest](../../src/web/models/tickets.py#L28) | `client_id int` *, `text_of_ticket TicketText` *, `description TicketDescriptionText = ''`, `user_id int = 0`, `contact_user_id int = 0`, `department_id int = 0`, `remote_work_recommended bool = False`, `urgency TicketUrgency = TicketUrgency.NORMAL`, `planned_at UtcDatetime \| None = None`, `comment TicketCommentText = ''` |
| [TicketCommentBaseRequest](../../src/web/models/tickets.py#L63) | `comment TicketCommentText = ''` |
| [TicketRequiredCommentRequest](../../src/web/models/tickets.py#L73) | `comment RequiredTicketCommentText` * Наследует поля `TicketCommentBaseRequest`. |
| [TicketDescriptionRequest](../../src/web/models/tickets.py#L89) | `description TicketDescriptionText = ''` |
| [TicketContactUserRequest](../../src/web/models/tickets.py#L95) | `contact_user_id int = Field(ge=0)` * |
| [TicketChangeDepartmentRequest](../../src/web/models/tickets.py#L101) | `department_id int = Field(ge=0)` * |
| [TicketRemoteWorkRecommendationRequest](../../src/web/models/tickets.py#L107) | `remote_work_recommended bool` * |
| [TicketUrgencyRequest](../../src/web/models/tickets.py#L113) | `urgency TicketUrgency` * |
| [TicketScheduleRequest](../../src/web/models/tickets.py#L124) | `planned_at UtcDatetime` * |
| [TicketAssignRequest](../../src/web/models/tickets.py#L137) | `executor_id int = Field(gt=0)` *, `comment TicketCommentText = ''` |
| [TicketStartWorkRequest](../../src/web/models/tickets.py#L149) | `work_is_remote bool = False`, `comment TicketCommentText = ''` |
| [TicketStartRemoteWorkRequest](../../src/web/models/tickets.py#L162) | `comment TicketCommentText = ''` |
| [TicketResumeWorkRequest](../../src/web/models/tickets.py#L178) | `work_is_remote bool = False`, `comment TicketCommentText = ''` |
| [TicketCompleteWorkRetroactivelyRequest](../../src/web/models/tickets.py#L196) | `work_is_remote bool = False`, `actual_started_at UtcDatetime \| None = None`, `actual_finished_at UtcDatetime \| None = None`, `duration timedelta = Field(default_factory=timedelta)`, `comment TicketCommentText = ''` |
| [TicketResponse](../../src/web/models/tickets.py#L243) | `ticket_id int` *, `client_id int` *, `user_id int` *, `contact_user_id int` *, `user_ticket_id int` *, `department_id int` *, `text_of_ticket str` *, `description str` *, `date_created datetime` *, `date_finished datetime \| None` *, `planned_at datetime \| None = None`, `remote_work_recommended bool` *, `urgency TicketUrgency` *, `current_executor_id int = 0`, `last_executor_id int = 0`, `is_closed bool` *, `time_spent int = 0`, `statuses list[dict[str, Any]] = Field(default_factory=list)`, `comments list[dict[str, Any]] = Field(default_factory=list)` |
| [UserTicketCreateRequest](../../src/web/models/tikcets_user.py#L20) | `text_of_ticket TicketText` *, `contact_user_id int = Field(default=0, ge=0)`, `description TicketDescriptionText = ''`, `remote_work_recommended bool = False`, `urgency TicketUrgency = TicketUrgency.NORMAL`, `comment TicketCommentText = ''` |
| [UserTicketActionRequest](../../src/web/models/tikcets_user.py#L38) | `comment TicketCommentText = ''` |
| [UserTicketCommentRequest](../../src/web/models/tikcets_user.py#L42) | `comment RequiredTicketCommentText` * |
| [UserTicketDescriptionRequest](../../src/web/models/tikcets_user.py#L46) | `description TicketDescriptionText = ''` |
| [UserTicketContactUserRequest](../../src/web/models/tikcets_user.py#L50) | `contact_user_id int = Field(ge=0)` * |
| [TicketUserResponse](../../src/web/models/tikcets_user.py#L56) | `ticket_user_id int` *, `client_id int` *, `user_id int` *, `contact_user_id int` *, `text_of_ticket str` *, `description str` *, `current_status str` *, `date_created datetime` *, `date_finished datetime \| None` *, `is_closed bool` *, `statuses list[dict[str, Any]]` *, `comments list[dict[str, Any]]` * |
| [UserCreateRequest](../../src/web/models/users.py#L8) | `client_id int` *, `first_name str` *, `last_name str = ''`, `email str = ''`, `phone str = ''`, `login str = ''`, `password str = ''`, `enable bool = True`, `enable_account bool = True`, `roles set[int] = Field(default_factory=set)` |
| [UserUpdateRequest](../../src/web/models/users.py#L34) | `first_name str = ''`, `last_name str = ''`, `email str = ''`, `phone str = ''` |
| [UserAttachAccountRequest](../../src/web/models/users.py#L47) | `login str` *, `password str` *, `enable_account bool = True` |
| [UserChangePasswordRequest](../../src/web/models/users.py#L59) | `password str` * |
| [UserRolesRequest](../../src/web/models/users.py#L69) | `roles set[int] = Field(default_factory=set)` |
| [UserResponse](../../src/web/models/users.py#L79) | `employee_id int` *, `first_name str = ''`, `last_name str = ''`, `enabled bool = True`, `email str = ''`, `phone str = ''`, `login str = ''`, `enabled_login bool = False`, `date_created str = ''`, `roles set[int] = Field(default_factory=set)`, `client_id int` * |
| [TicketCommentRequest](../../src/web/models/tickets.py#L69) | Поля `TicketCommentBaseRequest`. |
| [TicketAcceptRequest](../../src/web/models/tickets.py#L77) | Поля `TicketCommentRequest`. |
| [TicketRejectRequest](../../src/web/models/tickets.py#L81) | Поля `TicketRequiredCommentRequest`. |
| [TicketDeferRequest](../../src/web/models/tickets.py#L85) | Поля `TicketRequiredCommentRequest`. |
| [TicketPauseWorkRequest](../../src/web/models/tickets.py#L174) | Поля `TicketCommentRequest`. |
| [TicketFinishWorkRequest](../../src/web/models/tickets.py#L185) | Поля `TicketCommentRequest`. |
| [TicketExecuteRequest](../../src/web/models/tickets.py#L230) | Поля `TicketCommentRequest`. |
| [TicketCancelRequest](../../src/web/models/tickets.py#L234) | Поля `TicketRequiredCommentRequest`. |

Login принимает `application/x-www-form-urlencoded` с обязательными `username` и `password`. Стандартная форма FastAPI также принимает необязательные `scope` (строка с пробелами, по умолчанию пустая), `grant_type` (значение `password` при наличии), `client_id`, `client_secret`. v3 передаёт логин и пароль. В JSON ответа login/refresh сервер возвращает поля `TokenResponse`. Для logout ответ 200 содержит `message: "Logged out successfully"`, для health — `status: "ok"`. [Маршруты auth](../../src/web/routers/auth.py#L72) · [Модели auth](../../src/web/auth/models.py).

### Уточнения по данным Ticket

- После trim тема `TicketText` имеет 2–4000 символов, описание 0–4000, необязательный комментарий 0–1000, обязательный комментарий 1–1000. `TicketUrgency` — `normal`, `urgent` или `maintenance`. [Валидация текста](../../src/web/models/ticket_input.py) · [Пороги](../../src/domain/value_objects.py#L219) · [Срочность](../../src/domain/ticket_components.py#L53).
- `UtcDatetime` требует timezone-aware значение, нормализуется в UTC, проверка планирования использует календарную дату UTC. Ретроспективная работа принимает либо пару timestamps с `начало < конец ≤ момент регистрации`, либо положительную длительность. [Модели Ticket](../../src/web/models/tickets.py) · [Валидация дат](../../src/domain/ticket.py#L922) · [Валидация эпизода](../../src/domain/statuses/ticket_status_record.py#L216).
- Текущий статус Admin — `statuses.at(-1)?.status`, дата создания в UI — `statuses[0]?.date_created`. `TicketResponse` не содержит `current_status`, в отличие от `TicketUserResponse`. `remote_work_recommended` — флаг заявки, `work_is_remote` — поле записи истории активного эпизода. Статусы ответов — lower snake case. Порядок и поля вложенных словарей описаны в [BACKEND_ANALYSIS.md](BACKEND_ANALYSIS.md#модели-и-выдача).
- `POST /admin/tickets/` требует существующего активного клиента с `client_id > 0`. При `user_id=0` создаётся отдельная заявка с первым статусом `created`. При активном заявителе из этого клиента сервер создаёт связанный TicketUser и использует `created_from_request_user`. `created_from_ticket_user` возникает при создании через User API. Начальный статус не передаётся в теле. При `contact_user_id=0` контакт подставляется из `user_id`; явно указанный контакт должен быть активным и принадлежать тому же клиенту. Ненулевой отдел должен существовать и быть активным. При `ticket.accepted` сервер может добавить `accepted` в той же операции, поэтому ответ 201 уже может показывать принятый текущий статус. [Создание](../../src/application/services/ticket_service.py#L125) · [User-источник](../../src/application/services/ticket_user_service.py#L84).
- Для scoped выдачи пользователей клиента работают обе формы, `GET /admin/users/?client_id=<id>` и `GET /admin/users/client/{client_id}`. Значение query `client_id=0` означает все записи, ненулевое значение задаёт фильтр, пустой набор возвращается как `200 []`. Выбор явного пути — предложение v3. Ошибка об отсутствии query в первоначальном отчёте исправлена в контракте. [get_all_users](../../src/web/routers/admin/users.py#L120) · [get_by_client](../../src/web/routers/admin/users.py#L188).
- В выдаче заявок нет произвольного query для фильтрации/поиска, пагинации и сортировки. Сортировку, фильтры и страницы вычислять из выбранного набора. Нет endpoint редактирования определения роли, batch grant+revoke, вложений и массовых действий. [Роутер Ticket](../../src/web/routers/admin/tickets.py) · [Роутер ролей](../../src/web/routers/admin/roles.py).

## Ошибки и восстановление

PUT карточек Admin, User и Client использует `model_dump()` с defaults. Пропущенное поле может очистить значение, пустое имя может привести к доменной ошибке. Для Admin `department_id=0` в PUT означает попытку снять отдел, которую сервер может отклонить при связанных заявках. Формировать PUT из актуального полного снимка редактируемых полей и сверять скачок состояния. Отдельное назначение отдела использует положительный ID существующего активного отдела в PATCH `…/department`, снятие — DELETE `…/department`. [Admin](../../src/application/services/admin_service.py#L145) · [User](../../src/web/routers/admin/users.py#L210) · [Client](../../src/web/routers/admin/clients.py#L154).

| HTTP | Контракт и реакция клиента |
|---|---|
| 400 | Доменное ограничение / валидация приложения. Сохранять ввод, обновить карточку при возможном изменении статуса. |
| 401 | Недействительная аутентификация, включая отключённый субъект/аккаунт или клиент User при проверке Bearer. Для защищённого запроса допускается ограниченный refresh по правилам auth. |
| 403 | Недостаточно прав. Обновить разрешения по контексту, без refresh на 403. |
| 404 | Запись отсутствует. Предложить возврат к разрешённому списку. |
| 409 | Optimistic lock во время серверной записи, сопоставленный `ItemAlreadyExistsError` или конфликт ключа. Несопоставленная ошибка уникальности может дать 500. Перечитать актуальное состояние и сохранить ввод. Условный PATCH с версией или ETag отсутствует. |
| 422 | FastAPI `detail[]` с `loc,msg,type` для ошибок схемы. Возможен текстовый `detail` при неоднозначном Idempotency-Key. Показывать ошибки поля и безопасное общее сообщение. |
| 503 | Хранилище временно недоступно. Безопасный GET можно повторить, неизвестный результат записи проверяется чтением. |
| 500 | Общее сообщение о сбое, внутренние детали и поля ответа не выводятся в лог клиента. |
| Сеть / таймаут | HTTP-кода нет. Для мутации исход может быть неизвестен. Отобразить проверку состояния и сохранить черновик. |

Стандартная ошибка приложения содержит `detail` и может содержать `error_type`. Ответы `HTTPException` и FastAPI validation имеют собственный формат. При 204 не декодировать JSON. [Обработчики](../../src/web/main.py#L50) · [Формат ошибки](../../src/web/execeptions/exception_handlers.py#L326).

Идемпотентность принимает один заголовок `Idempotency-Key` (1–128 печатных ASCII без пробела) и сохраняет успешный результат на 24 часа. Повтор с тем же актором, ключом и payload может вернуть более старый снимок с исходным HTTP-кодом. Повтор с изменённым payload или другой операцией даёт 409. На неизвестный результат отправлять прежний ключ только для того же неизменённого намерения. После повтора с карточкой сверять свежий GET при наличии права чтения. [Реализация](../../src/web/idempotency.py#L42).
