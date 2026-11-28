# Матрица покрытия документацией

Сверка охватывает 107 операций и 178 модулей опубликованного снимка, 17 таблиц, 25 правил и шесть профилей. «Выполнено» относится к зафиксированному сценарию, а «статическая сверка» к контракту по коду, схеме или OpenAPI.

## Роли и процессы

| Бизнес-роль или процесс | Где описан | Правило и свидетельство |
|---|---|---|
| Обычный сотрудник | [Руководство](../user-guide.md#user-roles) · [Права](../backend.md#backend-08) | BR-002/023, C-12 и учебный базовый профиль. |
| Инженер | [Руководство](../user-guide.md#user-roles) · [Права](../backend.md#backend-08) | BR-007/009/011–013. Штатный рабочий сценарий и пример QA. |
| Инженер с правом работы на горячей линии | [Руководство](../user-guide.md#user-hotline) · [Права](../backend.md#backend-08) | BR-008/010. Штатные тесты рекомендации и назначения. C-01/02/13. |
| Ведущий инженер | [Руководство](../user-guide.md#user-roles) · [Права](../backend.md#backend-08) | BR-005/014/023. C-12 и учебные права с текущей глобальной областью. |
| Менеджер | [Руководство](../user-guide.md#user-registration) · [Права](../backend.md#backend-08) | BR-004–007/014/015. C-13 и маршруты подтверждения, назначения, изменения рекомендации. |
| Руководитель отдела | [Руководство](../user-guide.md#user-roles) · [Права](../backend.md#backend-08) | BR-020/023/025. Учебная комбинация, C-13. QA проверил профиль и отделы. |
| Пользователь клиента | [Руководство](../user-guide.md#user-registration) · [Права](../backend.md#backend-08) | BR-001–003/018. Синтетическая подача и подтверждение связанной пары. |
| Создание и передача в работу | [Руководство](../user-guide.md#user-registration) · [Права](../backend.md#backend-08) | BR-002–006, три происхождения и рабочий цикл. |
| Назначение, работа, пауза и ретроспектива | [Руководство](../user-guide.md#user-work) · [Права](../backend.md#backend-08) | BR-007–013, штатные проверки работы. Переходы сверены с графом. |
| Подтверждение и возврат | [Руководство](../user-guide.md#user-confirm) · [Права](../backend.md#backend-08) | BR-012/014/018/024, QA execute и клиентский штатный тест. |
| Отключение, отмена и справочники | [Руководство](../user-guide.md#user-faq) · [Права](../backend.md#backend-08) | BR-015/016/019–021/025, дополнение QA и тесты удаления отделов/карточек в поддержанных случаях. |

## Бизнес-правила

| ID | Сценарий | Вид подтверждения |
|---|---|---|
| BR-001 | Область клиентского доступа | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-002 | Регистрация | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-003 | Контакт | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-004 | Редактируемые поля | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-005 | Приём | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-006 | План и отсрочка | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-007 | Чужое назначение | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-008 | Самоназначение | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-009 | Обычная работа | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-010 | Горячая линия | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-011 | Пауза | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-012 | Готовность | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-013 | Ретроспектива | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-014 | Подтверждение Admin | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-015 | Отказ и отмена | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-016 | Удаление | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-017 | История и комментарии | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-018 | Действия User | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-019 | Каскад отключения | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-020 | Отделы и профили | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-021 | Сессии | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-022 | Повтор создания | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-023 | Роли | [Каталог](../backend.md#br-catalog). Статическая сверка области и граничных условий. |
| BR-024 | Целостность пары | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |
| BR-025 | Подготовка отдела и профиля | [Каталог](../backend.md#br-catalog). Код и указанные штатные или дополнительные сценарии. [Факты](validation.md). |

## HTTP и прикладные входы

Для каждой операции указан обработчик выбранного снимка. Прикладные вызовы, их параметры, ветви прав и схемы ответа перечислены в соответствующем пункте полного каталога. Фоновые и внутренние методы без маршрута перечислены в модулях приложения ниже.

| Метод и путь | Обработчик | Каталог |
|---|---|---|
| `GET /admin/admins/` | [get_all_admins](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L106) | [Контракт](../backend.md#api-get-admin-admins) |
| `POST /admin/admins/` | [create_admin](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L77) | [Контракт](../backend.md#api-post-admin-admins) |
| `GET /admin/admins/by-login/{login}` | [find_admin_by_login](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L147) | [Контракт](../backend.md#api-get-admin-admins-by-login-login) |
| `GET /admin/admins/permissions` | [get_permissions](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L124) | [Контракт](../backend.md#api-get-admin-admins-permissions) |
| `DELETE /admin/admins/{employee_id}` | [delete_admin](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L421) | [Контракт](../backend.md#api-delete-admin-admins-employee-id) |
| `GET /admin/admins/{employee_id}` | [get_admin](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L169) | [Контракт](../backend.md#api-get-admin-admins-employee-id) |
| `PUT /admin/admins/{employee_id}` | [update_admin](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L191) | [Контракт](../backend.md#api-put-admin-admins-employee-id) |
| `DELETE /admin/admins/{employee_id}/account` | [detach_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L239) | [Контракт](../backend.md#api-delete-admin-admins-employee-id-account) |
| `POST /admin/admins/{employee_id}/account` | [attach_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L215) | [Контракт](../backend.md#api-post-admin-admins-employee-id-account) |
| `PATCH /admin/admins/{employee_id}/account/disable` | [disable_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L284) | [Контракт](../backend.md#api-patch-admin-admins-employee-id-account-disable) |
| `PATCH /admin/admins/{employee_id}/account/enable` | [enable_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L260) | [Контракт](../backend.md#api-patch-admin-admins-employee-id-account-enable) |
| `DELETE /admin/admins/{employee_id}/department` | [remove_admin_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L461) | [Контракт](../backend.md#api-delete-admin-admins-employee-id-department) |
| `PATCH /admin/admins/{employee_id}/department` | [change_admin_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L439) | [Контракт](../backend.md#api-patch-admin-admins-employee-id-department) |
| `PATCH /admin/admins/{employee_id}/disable` | [disable_admin](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L378) | [Контракт](../backend.md#api-patch-admin-admins-employee-id-disable) |
| `PATCH /admin/admins/{employee_id}/enable` | [enable_admin](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L400) | [Контракт](../backend.md#api-patch-admin-admins-employee-id-enable) |
| `PATCH /admin/admins/{employee_id}/password` | [change_password](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L310) | [Контракт](../backend.md#api-patch-admin-admins-employee-id-password) |
| `DELETE /admin/admins/{employee_id}/roles` | [revoke_roles](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L358) | [Контракт](../backend.md#api-delete-admin-admins-employee-id-roles) |
| `POST /admin/admins/{employee_id}/roles` | [grant_roles](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/admins.py#L334) | [Контракт](../backend.md#api-post-admin-admins-employee-id-roles) |
| `GET /admin/clients/` | [get_all_clients](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/clients.py#L120) | [Контракт](../backend.md#api-get-admin-clients) |
| `POST /admin/clients/` | [create_client](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/clients.py#L91) | [Контракт](../backend.md#api-post-admin-clients) |
| `DELETE /admin/clients/{client_id}` | [delete_client](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/clients.py#L228) | [Контракт](../backend.md#api-delete-admin-clients-client-id) |
| `GET /admin/clients/{client_id}` | [get_client](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/clients.py#L139) | [Контракт](../backend.md#api-get-admin-clients-client-id) |
| `PUT /admin/clients/{client_id}/contact` | [update_contact](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/clients.py#L161) | [Контракт](../backend.md#api-put-admin-clients-client-id-contact) |
| `PATCH /admin/clients/{client_id}/disable` | [disable_client](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/clients.py#L185) | [Контракт](../backend.md#api-patch-admin-clients-client-id-disable) |
| `PATCH /admin/clients/{client_id}/enable` | [enable_client](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/clients.py#L207) | [Контракт](../backend.md#api-patch-admin-clients-client-id-enable) |
| `GET /admin/departments/` | [get_all_departments](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/departments.py#L96) | [Контракт](../backend.md#api-get-admin-departments) |
| `POST /admin/departments/` | [create_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/departments.py#L70) | [Контракт](../backend.md#api-post-admin-departments) |
| `DELETE /admin/departments/{department_id}` | [delete_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/departments.py#L205) | [Контракт](../backend.md#api-delete-admin-departments-department-id) |
| `GET /admin/departments/{department_id}` | [get_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/departments.py#L116) | [Контракт](../backend.md#api-get-admin-departments-department-id) |
| `PUT /admin/departments/{department_id}` | [update_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/departments.py#L137) | [Контракт](../backend.md#api-put-admin-departments-department-id) |
| `PATCH /admin/departments/{department_id}/disable` | [disable_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/departments.py#L183) | [Контракт](../backend.md#api-patch-admin-departments-department-id-disable) |
| `PATCH /admin/departments/{department_id}/enable` | [enable_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/departments.py#L162) | [Контракт](../backend.md#api-patch-admin-departments-department-id-enable) |
| `GET /admin/roles/admin` | [get_all_admin_roles](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L138) | [Контракт](../backend.md#api-get-admin-roles-admin) |
| `POST /admin/roles/admin` | [create_admin_role](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L110) | [Контракт](../backend.md#api-post-admin-roles-admin) |
| `GET /admin/roles/admin/permissions` | [get_admin_permissions](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L70) | [Контракт](../backend.md#api-get-admin-roles-admin-permissions) |
| `DELETE /admin/roles/admin/{role_id}` | [delete_admin_role](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L179) | [Контракт](../backend.md#api-delete-admin-roles-admin-role-id) |
| `GET /admin/roles/admin/{role_id}` | [get_admin_role](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L159) | [Контракт](../backend.md#api-get-admin-roles-admin-role-id) |
| `GET /admin/roles/user` | [get_all_user_roles](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L246) | [Контракт](../backend.md#api-get-admin-roles-user) |
| `POST /admin/roles/user` | [create_user_role](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L218) | [Контракт](../backend.md#api-post-admin-roles-user) |
| `GET /admin/roles/user/permissions` | [get_user_permissions](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L80) | [Контракт](../backend.md#api-get-admin-roles-user-permissions) |
| `DELETE /admin/roles/user/{role_id}` | [delete_user_role](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L286) | [Контракт](../backend.md#api-delete-admin-roles-user-role-id) |
| `GET /admin/roles/user/{role_id}` | [get_user_role](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/roles.py#L266) | [Контракт](../backend.md#api-get-admin-roles-user-role-id) |
| `GET /admin/tickets/` | [get_all_tickets](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L129) | [Контракт](../backend.md#api-get-admin-tickets) |
| `POST /admin/tickets/` | [create_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L91) | [Контракт](../backend.md#api-post-admin-tickets) |
| `GET /admin/tickets/by-client/{client_id}` | [get_tickets_by_client](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L213) | [Контракт](../backend.md#api-get-admin-tickets-by-client-client-id) |
| `GET /admin/tickets/by-contact-user/{contact_user_id}` | [get_tickets_by_contact_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L273) | [Контракт](../backend.md#api-get-admin-tickets-by-contact-user-contact-user-id) |
| `GET /admin/tickets/by-department/{department_id}` | [get_tickets_by_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L303) | [Контракт](../backend.md#api-get-admin-tickets-by-department-department-id) |
| `GET /admin/tickets/by-executor/{executor_id}` | [get_tickets_by_current_executor](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L333) | [Контракт](../backend.md#api-get-admin-tickets-by-executor-executor-id) |
| `GET /admin/tickets/by-user/{user_id}` | [get_tickets_by_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L243) | [Контракт](../backend.md#api-get-admin-tickets-by-user-user-id) |
| `GET /admin/tickets/closed` | [get_closed_tickets](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L185) | [Контракт](../backend.md#api-get-admin-tickets-closed) |
| `GET /admin/tickets/open` | [get_open_tickets](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L157) | [Контракт](../backend.md#api-get-admin-tickets-open) |
| `DELETE /admin/tickets/{ticket_id}` | [delete_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L1089) | [Контракт](../backend.md#api-delete-admin-tickets-ticket-id) |
| `GET /admin/tickets/{ticket_id}` | [get_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L362) | [Контракт](../backend.md#api-get-admin-tickets-ticket-id) |
| `PATCH /admin/tickets/{ticket_id}/accept` | [accept_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L692) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-accept) |
| `PATCH /admin/tickets/{ticket_id}/cancel` | [cancel_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L1058) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-cancel) |
| `POST /admin/tickets/{ticket_id}/comments` | [add_comment](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L413) | [Контракт](../backend.md#api-post-admin-tickets-ticket-id-comments) |
| `PATCH /admin/tickets/{ticket_id}/complete-work-retroactively` | [complete_work_retroactively](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L988) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-complete-work-retroactively) |
| `PATCH /admin/tickets/{ticket_id}/contact-user` | [change_contact_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L482) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-contact-user) |
| `PATCH /admin/tickets/{ticket_id}/defer` | [defer_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L758) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-defer) |
| `PATCH /admin/tickets/{ticket_id}/department` | [change_department](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L517) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-department) |
| `PATCH /admin/tickets/{ticket_id}/description` | [update_description](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L448) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-description) |
| `PATCH /admin/tickets/{ticket_id}/execute` | [execute_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L1026) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-execute) |
| `PATCH /admin/tickets/{ticket_id}/executor` | [assign_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L789) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-executor) |
| `PATCH /admin/tickets/{ticket_id}/finish-work` | [finish_work](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L956) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-finish-work) |
| `PATCH /admin/tickets/{ticket_id}/pause-work` | [pause_work](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L890) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-pause-work) |
| `PATCH /admin/tickets/{ticket_id}/reject` | [reject_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L725) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-reject) |
| `PATCH /admin/tickets/{ticket_id}/remote-work-recommended` | [set_remote_work_recommended](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L550) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-remote-work-recommended) |
| `PATCH /admin/tickets/{ticket_id}/resume-work` | [resume_work](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L923) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-resume-work) |
| `DELETE /admin/tickets/{ticket_id}/schedule` | [clear_ticket_schedule](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L655) | [Контракт](../backend.md#api-delete-admin-tickets-ticket-id-schedule) |
| `PATCH /admin/tickets/{ticket_id}/schedule` | [schedule_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L623) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-schedule) |
| `PATCH /admin/tickets/{ticket_id}/start-remote-work` | [start_remote_work](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L858) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-start-remote-work) |
| `PATCH /admin/tickets/{ticket_id}/start-work` | [start_work](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L826) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-start-work) |
| `PATCH /admin/tickets/{ticket_id}/urgency` | [change_urgency](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/tickets.py#L584) | [Контракт](../backend.md#api-patch-admin-tickets-ticket-id-urgency) |
| `GET /admin/users/` | [get_all_users](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L127) | [Контракт](../backend.md#api-get-admin-users) |
| `POST /admin/users/` | [create_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L98) | [Контракт](../backend.md#api-post-admin-users) |
| `GET /admin/users/by-login/{login}` | [find_user_by_login](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L150) | [Контракт](../backend.md#api-get-admin-users-by-login-login) |
| `GET /admin/users/client/{client_id}` | [get_by_client](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L195) | [Контракт](../backend.md#api-get-admin-users-client-client-id) |
| `DELETE /admin/users/{employee_id}` | [delete_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L427) | [Контракт](../backend.md#api-delete-admin-users-employee-id) |
| `GET /admin/users/{employee_id}` | [get_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L175) | [Контракт](../backend.md#api-get-admin-users-employee-id) |
| `PUT /admin/users/{employee_id}` | [update_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L217) | [Контракт](../backend.md#api-put-admin-users-employee-id) |
| `DELETE /admin/users/{employee_id}/account` | [detach_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L259) | [Контракт](../backend.md#api-delete-admin-users-employee-id-account) |
| `POST /admin/users/{employee_id}/account` | [attach_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L238) | [Контракт](../backend.md#api-post-admin-users-employee-id-account) |
| `PATCH /admin/users/{employee_id}/account/disable` | [disable_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L302) | [Контракт](../backend.md#api-patch-admin-users-employee-id-account-disable) |
| `PATCH /admin/users/{employee_id}/account/enable` | [enable_account](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L278) | [Контракт](../backend.md#api-patch-admin-users-employee-id-account-enable) |
| `PATCH /admin/users/{employee_id}/disable` | [disable_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L387) | [Контракт](../backend.md#api-patch-admin-users-employee-id-disable) |
| `PATCH /admin/users/{employee_id}/enable` | [enable_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L408) | [Контракт](../backend.md#api-patch-admin-users-employee-id-enable) |
| `PATCH /admin/users/{employee_id}/password` | [change_password](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L325) | [Контракт](../backend.md#api-patch-admin-users-employee-id-password) |
| `DELETE /admin/users/{employee_id}/roles` | [revoke_roles](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L367) | [Контракт](../backend.md#api-delete-admin-users-employee-id-roles) |
| `POST /admin/users/{employee_id}/roles` | [grant_roles](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/admin/users.py#L345) | [Контракт](../backend.md#api-post-admin-users-employee-id-roles) |
| `POST /auth/admin/login` | [login](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/auth.py#L73) | [Контракт](../backend.md#api-post-auth-admin-login) |
| `POST /auth/admin/logout` | [logout](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/auth.py#L94) | [Контракт](../backend.md#api-post-auth-admin-logout) |
| `POST /auth/admin/refresh` | [refresh](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/auth.py#L84) | [Контракт](../backend.md#api-post-auth-admin-refresh) |
| `POST /auth/user/login` | [login_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/auth.py#L108) | [Контракт](../backend.md#api-post-auth-user-login) |
| `POST /auth/user/logout` | [logout_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/auth.py#L128) | [Контракт](../backend.md#api-post-auth-user-logout) |
| `POST /auth/user/refresh` | [refresh_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/auth.py#L119) | [Контракт](../backend.md#api-post-auth-user-refresh) |
| `GET /health` | [health_check](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/main.py#L96) | [Контракт](../backend.md#api-get-health) |
| `GET /user/tickets/` | [get_my_tickets](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L176) | [Контракт](../backend.md#api-get-user-tickets) |
| `POST /user/tickets/` | [create_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L138) | [Контракт](../backend.md#api-post-user-tickets) |
| `GET /user/tickets/all` | [get_all_tickets](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L205) | [Контракт](../backend.md#api-get-user-tickets-all) |
| `GET /user/tickets/closed` | [get_closed_tickets](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L264) | [Контракт](../backend.md#api-get-user-tickets-closed) |
| `GET /user/tickets/open` | [get_open_tickets](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L235) | [Контракт](../backend.md#api-get-user-tickets-open) |
| `GET /user/tickets/{ticket_user_id}` | [get_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L293) | [Контракт](../backend.md#api-get-user-tickets-ticket-user-id) |
| `PATCH /user/tickets/{ticket_user_id}/cancel` | [cancel_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L454) | [Контракт](../backend.md#api-patch-user-tickets-ticket-user-id-cancel) |
| `POST /user/tickets/{ticket_user_id}/comments` | [add_comment](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L343) | [Контракт](../backend.md#api-post-user-tickets-ticket-user-id-comments) |
| `PATCH /user/tickets/{ticket_user_id}/confirm` | [confirm_ticket](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L488) | [Контракт](../backend.md#api-patch-user-tickets-ticket-user-id-confirm) |
| `PATCH /user/tickets/{ticket_user_id}/contact-user` | [change_contact_user](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L415) | [Контракт](../backend.md#api-patch-user-tickets-ticket-user-id-contact-user) |
| `PATCH /user/tickets/{ticket_user_id}/description` | [update_description](https://github.com/tegasae/simple_tickets/blob/1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69/src/web/routers/user/tickets.py#L380) | [Контракт](../backend.md#api-patch-user-tickets-ticket-user-id-description) |

## Python-модули и внутренние операции

Число включает классы и методы. Прямое упоминание тестом указывает импорт, а не покрытие строк. Методы прикладных сервисов, доменные валидаторы и служебные операции найдены в списках символов каждого модуля.

| Модуль | Символы | Свидетельство |
|---|---:|---|
| [`config.py`](../backend.md#module-config-py) | 1 | Статическая карта |
| [`main.py`](../backend.md#module-main-py) | 1 | Статическая карта |
| [`models.py`](../backend.md#module-models-py) | 7 | Статическая карта |
| [`scripts/migrate_backend_storage.py`](../backend.md#module-scripts-migrate-backend-storage-py) | 6 | `tests/test_creation_and_refresh.py` |
| [`src/__init__.py`](../backend.md#module-src-init-py) | 0 | Статическая карта |
| [`src/adapters/__init__.py`](../backend.md#module-src-adapters-init-py) | 0 | Статическая карта |
| [`src/adapters/repositories/__init__.py`](../backend.md#module-src-adapters-repositories-init-py) | 0 | Статическая карта |
| [`src/adapters/repositories/account.py`](../backend.md#module-src-adapters-repositories-account-py) | 13 | Статическая карта |
| [`src/adapters/repositories/admin.py`](../backend.md#module-src-adapters-repositories-admin-py) | 19 | Статическая карта |
| [`src/adapters/repositories/base_repository.py`](../backend.md#module-src-adapters-repositories-base-repository-py) | 8 | Статическая карта |
| [`src/adapters/repositories/client_repository.py`](../backend.md#module-src-adapters-repositories-client-repository-py) | 9 | Статическая карта |
| [`src/adapters/repositories/creation_result_repository.py`](../backend.md#module-src-adapters-repositories-creation-result-repository-py) | 9 | Статическая карта |
| [`src/adapters/repositories/department_repository.py`](../backend.md#module-src-adapters-repositories-department-repository-py) | 7 | Статическая карта |
| [`src/adapters/repositories/exceptions.py`](../backend.md#module-src-adapters-repositories-exceptions-py) | 6 | Статическая карта |
| [`src/adapters/repositories/gateways/__init__.py`](../backend.md#module-src-adapters-repositories-gateways-init-py) | 0 | Статическая карта |
| [`src/adapters/repositories/gateways/account_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-account-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/admin_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-admin-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/client_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-client-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/creation_result_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-creation-result-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/department_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-department-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/employee_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-employee-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/employee_role_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-employee-role-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/refresh_session_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-refresh-session-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/role_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-role-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/ticket_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-ticket-gateway-py) | 3 | Статическая карта |
| [`src/adapters/repositories/gateways/ticket_user_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-ticket-user-gateway-py) | 3 | Статическая карта |
| [`src/adapters/repositories/gateways/user_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-user-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/gateways/user_role_gateway.py`](../backend.md#module-src-adapters-repositories-gateways-user-role-gateway-py) | 1 | Статическая карта |
| [`src/adapters/repositories/mappers/__init__.py`](../backend.md#module-src-adapters-repositories-mappers-init-py) | 0 | Статическая карта |
| [`src/adapters/repositories/mappers/admin_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-admin-mapper-py) | 7 | Статическая карта |
| [`src/adapters/repositories/mappers/client_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-client-mapper-py) | 3 | Статическая карта |
| [`src/adapters/repositories/mappers/creation_result_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-creation-result-mapper-py) | 6 | Статическая карта |
| [`src/adapters/repositories/mappers/department_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-department-mapper-py) | 3 | Статическая карта |
| [`src/adapters/repositories/mappers/refresh_session_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-refresh-session-mapper-py) | 4 | Статическая карта |
| [`src/adapters/repositories/mappers/role_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-role-mapper-py) | 5 | Статическая карта |
| [`src/adapters/repositories/mappers/ticket_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-ticket-mapper-py) | 7 | Статическая карта |
| [`src/adapters/repositories/mappers/ticket_user_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-ticket-user-mapper-py) | 7 | Статическая карта |
| [`src/adapters/repositories/mappers/user_mapper.py`](../backend.md#module-src-adapters-repositories-mappers-user-mapper-py) | 6 | Статическая карта |
| [`src/adapters/repositories/refresh_session_repository.py`](../backend.md#module-src-adapters-repositories-refresh-session-repository-py) | 7 | Статическая карта |
| [`src/adapters/repositories/role_repository.py`](../backend.md#module-src-adapters-repositories-role-repository-py) | 6 | Статическая карта |
| [`src/adapters/repositories/ticket_repository.py`](../backend.md#module-src-adapters-repositories-ticket-repository-py) | 26 | Статическая карта |
| [`src/adapters/repositories/ticket_user_repository.py`](../backend.md#module-src-adapters-repositories-ticket-user-repository-py) | 20 | Статическая карта |
| [`src/adapters/repositories/user_repository.py`](../backend.md#module-src-adapters-repositories-user-repository-py) | 14 | Статическая карта |
| [`src/adapters/uow/__init__.py`](../backend.md#module-src-adapters-uow-init-py) | 0 | Статическая карта |
| [`src/adapters/uow/sqlite_unit_of_work.py`](../backend.md#module-src-adapters-uow-sqlite-unit-of-work-py) | 8 | `tests/test_creation_and_refresh.py`, `tests/test_creation_operation.py` |
| [`src/application/__init__.py`](../backend.md#module-src-application-init-py) | 0 | Статическая карта |
| [`src/application/assemblers/__init__.py`](../backend.md#module-src-application-assemblers-init-py) | 0 | Статическая карта |
| [`src/application/assemblers/assembler.py`](../backend.md#module-src-application-assemblers-assembler-py) | 16 | Статическая карта |
| [`src/application/dto/__init__.py`](../backend.md#module-src-application-dto-init-py) | 0 | Статическая карта |
| [`src/application/dto/client_dto.py`](../backend.md#module-src-application-dto-client-dto-py) | 3 | Статическая карта |
| [`src/application/dto/department_dto.py`](../backend.md#module-src-application-dto-department-dto-py) | 3 | Статическая карта |
| [`src/application/dto/employee_dto.py`](../backend.md#module-src-application-dto-employee-dto-py) | 7 | Статическая карта |
| [`src/application/dto/roles_dto.py`](../backend.md#module-src-application-dto-roles-dto-py) | 3 | Статическая карта |
| [`src/application/dto/ticket_dto.py`](../backend.md#module-src-application-dto-ticket-dto-py) | 5 | Статическая карта |
| [`src/application/dto/ticket_search_dto.py`](../backend.md#module-src-application-dto-ticket-search-dto-py) | 1 | Статическая карта |
| [`src/application/exceptions.py`](../backend.md#module-src-application-exceptions-py) | 5 | Статическая карта |
| [`src/application/factory.py`](../backend.md#module-src-application-factory-py) | 10 | Статическая карта |
| [`src/application/helper/__init__.py`](../backend.md#module-src-application-helper-init-py) | 0 | Статическая карта |
| [`src/application/helper/actor_helper.py`](../backend.md#module-src-application-helper-actor-helper-py) | 13 | Статическая карта |
| [`src/application/helper/employee_helper.py`](../backend.md#module-src-application-helper-employee-helper-py) | 5 | Статическая карта |
| [`src/application/services/__init__.py`](../backend.md#module-src-application-services-init-py) | 0 | Статическая карта |
| [`src/application/services/admin_service.py`](../backend.md#module-src-application-services-admin-service-py) | 23 | Статическая карта |
| [`src/application/services/client_service.py`](../backend.md#module-src-application-services-client-service-py) | 11 | Статическая карта |
| [`src/application/services/department_service.py`](../backend.md#module-src-application-services-department-service-py) | 11 | Статическая карта |
| [`src/application/services/role_service.py`](../backend.md#module-src-application-services-role-service-py) | 23 | Статическая карта |
| [`src/application/services/ticket_search_service.py`](../backend.md#module-src-application-services-ticket-search-service-py) | 0 | Статическая карта |
| [`src/application/services/ticket_service.py`](../backend.md#module-src-application-services-ticket-service-py) | 43 | Статическая карта |
| [`src/application/services/ticket_user_service.py`](../backend.md#module-src-application-services-ticket-user-service-py) | 25 | Статическая карта |
| [`src/application/services/user_service.py`](../backend.md#module-src-application-services-user-service-py) | 23 | Статическая карта |
| [`src/domain/__init__.py`](../backend.md#module-src-domain-init-py) | 0 | Статическая карта |
| [`src/domain/account.py`](../backend.md#module-src-domain-account-py) | 20 | Статическая карта |
| [`src/domain/client.py`](../backend.md#module-src-domain-client-py) | 13 | `tests/test_creation_and_refresh.py` |
| [`src/domain/datetime_check.py`](../backend.md#module-src-domain-datetime-check-py) | 5 | Статическая карта |
| [`src/domain/department.py`](../backend.md#module-src-domain-department-py) | 14 | Статическая карта |
| [`src/domain/employee.py`](../backend.md#module-src-domain-employee-py) | 34 | `tests/test_creation_and_refresh.py` |
| [`src/domain/exceptions.py`](../backend.md#module-src-domain-exceptions-py) | 19 | Статическая карта |
| [`src/domain/policies/__init__.py`](../backend.md#module-src-domain-policies-init-py) | 0 | Статическая карта |
| [`src/domain/policies/admin.py`](../backend.md#module-src-domain-policies-admin-py) | 4 | Статическая карта |
| [`src/domain/policies/user.py`](../backend.md#module-src-domain-policies-user-py) | 3 | Статическая карта |
| [`src/domain/rbac/__init__.py`](../backend.md#module-src-domain-rbac-init-py) | 0 | Статическая карта |
| [`src/domain/rbac/employee_protocol.py`](../backend.md#module-src-domain-rbac-employee-protocol-py) | 4 | Статическая карта |
| [`src/domain/rbac/permissions.py`](../backend.md#module-src-domain-rbac-permissions-py) | 3 | `tests/test_creation_and_refresh.py`, `tests/test_creation_operation.py`, `tests/test_ticket_workflows.py` |
| [`src/domain/rbac/role.py`](../backend.md#module-src-domain-rbac-role-py) | 10 | Статическая карта |
| [`src/domain/rbac/role_new.py`](../backend.md#module-src-domain-rbac-role-new-py) | 14 | `tests/test_creation_and_refresh.py`, `tests/test_creation_operation.py` |
| [`src/domain/rbac/role_repository.py`](../backend.md#module-src-domain-rbac-role-repository-py) | 6 | Статическая карта |
| [`src/domain/rbac/typevar.py`](../backend.md#module-src-domain-rbac-typevar-py) | 0 | Статическая карта |
| [`src/domain/repositories/__init__.py`](../backend.md#module-src-domain-repositories-init-py) | 0 | Статическая карта |
| [`src/domain/repositories/account_repository.py`](../backend.md#module-src-domain-repositories-account-repository-py) | 10 | Статическая карта |
| [`src/domain/repositories/admin_repository.py`](../backend.md#module-src-domain-repositories-admin-repository-py) | 17 | Статическая карта |
| [`src/domain/repositories/client_repository.py`](../backend.md#module-src-domain-repositories-client-repository-py) | 9 | Статическая карта |
| [`src/domain/repositories/creation_result_repository.py`](../backend.md#module-src-domain-repositories-creation-result-repository-py) | 11 | Статическая карта |
| [`src/domain/repositories/department_repository.py`](../backend.md#module-src-domain-repositories-department-repository-py) | 7 | Статическая карта |
| [`src/domain/repositories/refresh_session_repository.py`](../backend.md#module-src-domain-repositories-refresh-session-repository-py) | 7 | Статическая карта |
| [`src/domain/repositories/ticket_repository.py`](../backend.md#module-src-domain-repositories-ticket-repository-py) | 20 | Статическая карта |
| [`src/domain/repositories/ticket_user_repository.py`](../backend.md#module-src-domain-repositories-ticket-user-repository-py) | 15 | Статическая карта |
| [`src/domain/repositories/user_repository.py`](../backend.md#module-src-domain-repositories-user-repository-py) | 11 | Статическая карта |
| [`src/domain/services/__init__.py`](../backend.md#module-src-domain-services-init-py) | 0 | Статическая карта |
| [`src/domain/services/admin_service.py`](../backend.md#module-src-domain-services-admin-service-py) | 15 | Статическая карта |
| [`src/domain/services/client_service.py`](../backend.md#module-src-domain-services-client-service-py) | 7 | Статическая карта |
| [`src/domain/services/department_service.py`](../backend.md#module-src-domain-services-department-service-py) | 6 | Статическая карта |
| [`src/domain/services/role_service.py`](../backend.md#module-src-domain-services-role-service-py) | 4 | Статическая карта |
| [`src/domain/services/ticket_service.py`](../backend.md#module-src-domain-services-ticket-service-py) | 28 | Статическая карта |
| [`src/domain/services/ticket_sync_service.py`](../backend.md#module-src-domain-services-ticket-sync-service-py) | 8 | Статическая карта |
| [`src/domain/services/ticket_user_service.py`](../backend.md#module-src-domain-services-ticket-user-service-py) | 9 | Статическая карта |
| [`src/domain/services/user_service.py`](../backend.md#module-src-domain-services-user-service-py) | 21 | Статическая карта |
| [`src/domain/statuses/__init__.py`](../backend.md#module-src-domain-statuses-init-py) | 0 | Статическая карта |
| [`src/domain/statuses/mapping_statuses.py`](../backend.md#module-src-domain-statuses-mapping-statuses-py) | 1 | Статическая карта |
| [`src/domain/statuses/rules/__init__.py`](../backend.md#module-src-domain-statuses-rules-init-py) | 0 | Статическая карта |
| [`src/domain/statuses/rules/ticket_origin_rule.py`](../backend.md#module-src-domain-statuses-rules-ticket-origin-rule-py) | 2 | Статическая карта |
| [`src/domain/statuses/rules/ticket_state_rule.py`](../backend.md#module-src-domain-statuses-rules-ticket-state-rule-py) | 2 | Статическая карта |
| [`src/domain/statuses/rules/ticket_status_rule.py`](../backend.md#module-src-domain-statuses-rules-ticket-status-rule-py) | 2 | Статическая карта |
| [`src/domain/statuses/rules/ticket_status_transition.py`](../backend.md#module-src-domain-statuses-rules-ticket-status-transition-py) | 1 | Статическая карта |
| [`src/domain/statuses/rules/ticket_transition_rule.py`](../backend.md#module-src-domain-statuses-rules-ticket-transition-rule-py) | 1 | Статическая карта |
| [`src/domain/statuses/rules/ticket_transition_validators.py`](../backend.md#module-src-domain-statuses-rules-ticket-transition-validators-py) | 7 | Статическая карта |
| [`src/domain/statuses/ticket_status.py`](../backend.md#module-src-domain-statuses-ticket-status-py) | 1 | Статическая карта |
| [`src/domain/statuses/ticket_status_record.py`](../backend.md#module-src-domain-statuses-ticket-status-record-py) | 10 | Статическая карта |
| [`src/domain/statuses/ticket_user_status.py`](../backend.md#module-src-domain-statuses-ticket-user-status-py) | 3 | Статическая карта |
| [`src/domain/statuses/ticket_user_status_record.py`](../backend.md#module-src-domain-statuses-ticket-user-status-record-py) | 7 | Статическая карта |
| [`src/domain/statuses/ticket_user_status_transitions.py`](../backend.md#module-src-domain-statuses-ticket-user-status-transitions-py) | 2 | Статическая карта |
| [`src/domain/ticket.py`](../backend.md#module-src-domain-ticket-py) | 49 | Статическая карта |
| [`src/domain/ticket_components.py`](../backend.md#module-src-domain-ticket-components-py) | 7 | Статическая карта |
| [`src/domain/ticket_user.py`](../backend.md#module-src-domain-ticket-user-py) | 31 | Статическая карта |
| [`src/domain/uow/__init__.py`](../backend.md#module-src-domain-uow-init-py) | 0 | Статическая карта |
| [`src/domain/uow/unit_of_work.py`](../backend.md#module-src-domain-uow-unit-of-work-py) | 7 | Статическая карта |
| [`src/domain/value_objects.py`](../backend.md#module-src-domain-value-objects-py) | 37 | Статическая карта |
| [`src/oauth2/__init__.py`](../backend.md#module-src-oauth2-init-py) | 0 | Статическая карта |
| [`src/oauth2/main.py`](../backend.md#module-src-oauth2-main-py) | 9 | Статическая карта |
| [`src/web/__init__.py`](../backend.md#module-src-web-init-py) | 0 | `tests/test_creation_and_refresh.py` |
| [`src/web/auth/__init__.py`](../backend.md#module-src-web-auth-init-py) | 0 | Статическая карта |
| [`src/web/auth/exceptions.py`](../backend.md#module-src-web-auth-exceptions-py) | 21 | Статическая карта |
| [`src/web/auth/models.py`](../backend.md#module-src-web-auth-models-py) | 5 | Статическая карта |
| [`src/web/auth/services/__init__.py`](../backend.md#module-src-web-auth-services-init-py) | 0 | Статическая карта |
| [`src/web/auth/services/auth_service.py`](../backend.md#module-src-web-auth-services-auth-service-py) | 13 | Статическая карта |
| [`src/web/auth/services/services.py`](../backend.md#module-src-web-auth-services-services-py) | 14 | Статическая карта |
| [`src/web/auth/services/shared_sessions.py`](../backend.md#module-src-web-auth-services-shared-sessions-py) | 7 | Статическая карта |
| [`src/web/auth/storage.py`](../backend.md#module-src-web-auth-storage-py) | 21 | Статическая карта |
| [`src/web/auth/storage_sqlite.py`](../backend.md#module-src-web-auth-storage-sqlite-py) | 15 | Статическая карта |
| [`src/web/auth/tokens.py`](../backend.md#module-src-web-auth-tokens-py) | 25 | Статическая карта |
| [`src/web/config.py`](../backend.md#module-src-web-config-py) | 7 | Статическая карта |
| [`src/web/dependencies/__init__.py`](../backend.md#module-src-web-dependencies-init-py) | 0 | Статическая карта |
| [`src/web/dependencies/auth.py`](../backend.md#module-src-web-dependencies-auth-py) | 10 | Статическая карта |
| [`src/web/dependencies/scheme.py`](../backend.md#module-src-web-dependencies-scheme-py) | 0 | Статическая карта |
| [`src/web/dependencies/services.py`](../backend.md#module-src-web-dependencies-services-py) | 4 | Статическая карта |
| [`src/web/execeptions/__init__.py`](../backend.md#module-src-web-execeptions-init-py) | 0 | Статическая карта |
| [`src/web/execeptions/exception_handlers.py`](../backend.md#module-src-web-execeptions-exception-handlers-py) | 13 | Статическая карта |
| [`src/web/idempotency.py`](../backend.md#module-src-web-idempotency-py) | 9 | Статическая карта |
| [`src/web/main.py`](../backend.md#module-src-web-main-py) | 1 | `tests/test_creation_and_refresh.py` |
| [`src/web/middleware/__init__.py`](../backend.md#module-src-web-middleware-init-py) | 0 | Статическая карта |
| [`src/web/middleware/middleware.py`](../backend.md#module-src-web-middleware-middleware-py) | 9 | Статическая карта |
| [`src/web/models/__init__.py`](../backend.md#module-src-web-models-init-py) | 0 | Статическая карта |
| [`src/web/models/admins.py`](../backend.md#module-src-web-models-admins-py) | 10 | Статическая карта |
| [`src/web/models/base_response.py`](../backend.md#module-src-web-models-base-response-py) | 3 | Статическая карта |
| [`src/web/models/clients.py`](../backend.md#module-src-web-models-clients-py) | 5 | Статическая карта |
| [`src/web/models/department.py`](../backend.md#module-src-web-models-department-py) | 4 | Статическая карта |
| [`src/web/models/roles.py`](../backend.md#module-src-web-models-roles-py) | 12 | Статическая карта |
| [`src/web/models/ticket_input.py`](../backend.md#module-src-web-models-ticket-input-py) | 0 | Статическая карта |
| [`src/web/models/tickets.py`](../backend.md#module-src-web-models-tickets-py) | 25 | Статическая карта |
| [`src/web/models/tikcets_user.py`](../backend.md#module-src-web-models-tikcets-user-py) | 7 | Статическая карта |
| [`src/web/models/users.py`](../backend.md#module-src-web-models-users-py) | 8 | Статическая карта |
| [`src/web/routers/__init__.py`](../backend.md#module-src-web-routers-init-py) | 0 | Статическая карта |
| [`src/web/routers/admin/__init__.py`](../backend.md#module-src-web-routers-admin-init-py) | 0 | Статическая карта |
| [`src/web/routers/admin/admins.py`](../backend.md#module-src-web-routers-admin-admins-py) | 21 | Статическая карта |
| [`src/web/routers/admin/clients.py`](../backend.md#module-src-web-routers-admin-clients-py) | 10 | Статическая карта |
| [`src/web/routers/admin/departments.py`](../backend.md#module-src-web-routers-admin-departments-py) | 10 | Статическая карта |
| [`src/web/routers/admin/roles.py`](../backend.md#module-src-web-routers-admin-roles-py) | 16 | Статическая карта |
| [`src/web/routers/admin/tickets.py`](../backend.md#module-src-web-routers-admin-tickets-py) | 37 | Статическая карта |
| [`src/web/routers/admin/users.py`](../backend.md#module-src-web-routers-admin-users-py) | 19 | Статическая карта |
| [`src/web/routers/auth.py`](../backend.md#module-src-web-routers-auth-py) | 7 | Статическая карта |
| [`src/web/routers/user/__init__.py`](../backend.md#module-src-web-routers-user-init-py) | 0 | Статическая карта |
| [`src/web/routers/user/tickets.py`](../backend.md#module-src-web-routers-user-tickets-py) | 20 | Статическая карта |
| [`utils/__init__.py`](../backend.md#module-utils-init-py) | 0 | Статическая карта |
| [`utils/db/__init__.py`](../backend.md#module-utils-db-init-py) | 0 | Статическая карта |
| [`utils/db/connect.py`](../backend.md#module-utils-db-connect-py) | 12 | `tests/test_creation_and_refresh.py`, `tests/test_creation_operation.py` |
| [`utils/db/exceptions.py`](../backend.md#module-utils-db-exceptions-py) | 8 | Статическая карта |
| [`utils/db/query.py`](../backend.md#module-utils-db-query-py) | 10 | Статическая карта |
| [`utils/db/sqlite_errors.py`](../backend.md#module-utils-db-sqlite-errors-py) | 1 | Статическая карта |
| [`utils/http/__init__.py`](../backend.md#module-utils-http-init-py) | 0 | Статическая карта |
| [`utils/http/get_json.py`](../backend.md#module-utils-http-get-json-py) | 4 | Статическая карта |

## Исключения

Текущая HTTP-сборка не включает интерфейс из репозитория, старые папки тестовых проходов и фронтенд. Содержимое баз, SQL-дампов с данными, .env и архивов исключено. Исторические Python-точки входа присутствуют в справочнике как прежний слой. Ролевые сравнительные матрицы описывают профиль, а не содержимое рабочей таблицы назначений.
