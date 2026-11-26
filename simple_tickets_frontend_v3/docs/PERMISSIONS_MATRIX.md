# Матрица прав и условий Admin

Сервер определяет права по текущему Admin и ролям. Таблица использует строковые permission. «Или» означает, что достаточно одного из указанных прав при соблюдении условий. Профили «оператор», «диспетчер», «исполнитель», «горячая линия», «администратор» описывают задачи и служат тестовыми наборами. Состав реальных ролей узнаём через API. [Перечень прав](../../src/domain/rbac/permissions.py) · [Собственные права](../../src/web/routers/admin/admins.py#L117).

## Действия с заявкой

| Операция | Permission | Условия / результат | Источник |
|---|---|---|---|
| Список, scoped list, карточка | `ticket.view` | Набор определён GET; действия вычисляются отдельно. | [Сервис](../../src/application/services/ticket_service.py#L1047) |
| Создать | `ticket.created` или `ticket.operation` | Обязательны допустимый клиент и тема; при рекомендации дополнительно `ticket.set_remote_recommendation`. Справочники требуют соответствующие view. | [Сервис](../../src/application/services/ticket_service.py#L79) |
| Править описание, контакт, отдел, срочность, расписание | `ticket.operation` | Раздельные PATCH, снятие плана DELETE /schedule; ограничения статуса и связанных записей определены командой. | [Сервис](../../src/application/services/ticket_service.py#L278) |
| Комментарий | `ticket.operation` | Непустой текст. Проверяется право и возможность комментария в текущем состоянии. | [Сервис](../../src/application/services/ticket_service.py#L247) |
| Рекомендация | `ticket.set_remote_recommendation` | Поддержка флага отделена от фактического способа работы. | [Сервис](../../src/application/services/ticket_service.py#L395) |
| Приёмка | `ticket.accepted` | Переход к `accepted` из начального статуса, `deferred`, `assigned` или `ready_for_review` при соблюдении правил. | [Сервис](../../src/application/services/ticket_service.py#L503) |
| Отклонение | `ticket.canceled` | Начальное состояние, требуется комментарий, результат `rejected`. | [Команда](../../src/application/services/ticket_service.py#L538) |
| Отложить | `ticket.operation` | Из `accepted, assigned, at_work, paused`; в `at_work` исключён текущий исполнитель. Комментарий обязателен. | [Команда](../../src/application/services/ticket_service.py#L573) |
| Назначить другого Admin | `ticket.assign_executor` | Активный исполнитель того же отдела. Из `accepted/deferred/assigned/at_work/paused/ready_for_review`; в `at_work` актёр не текущий исполнитель. Каталог выбора требует `admin.view`. | [Команда](../../src/application/services/ticket_service.py#L604) · [Переходы](../../src/domain/statuses/rules/ticket_status_transition.py) |
| Самоназначение через /executor | `ticket.at_work_remote` | `accepted/assigned`, рекомендация, текущий исполнитель отсутствует или актёр, положительный совпадающий отдел. Результат `assigned`. | [Ветка self](../../src/application/services/ticket_service.py#L642) |
| Старт обычной работы | `ticket.at_work` | Из `assigned`, текущий исполнитель. Эта команда имеет собственное поле `work_is_remote`, для сценария DEC-003 используется /start-remote-work. | [Команда](../../src/application/services/ticket_service.py#L672) |
| Старт работы на горячей линии | `ticket.at_work_remote` | `accepted`: рекомендация, действующий Admin, равный положительный ID отдела, самоназначение. `assigned`: рекомендация, актёр уже текущий исполнитель. Результат `at_work`, тело `{}` или `{comment}`. | [Команда](../../src/application/services/ticket_service.py#L710) |
| Пауза | `ticket.at_work` или `ticket.at_work_remote` | Из `at_work`, текущий исполнитель неретроспективного эпизода. Для remote-only эпизод должен быть удалённым. | [Доступ](../../src/application/services/ticket_service.py#L866) · [Валидаторы](../../src/domain/statuses/rules/ticket_transition_validators.py#L68) |
| Продолжение | `ticket.at_work` или, для удалённого режима, `ticket.at_work_remote` | Из `paused`, текущий исполнитель. Выбор remote-only требует рекомендации и удалённого режима. | [Доступ](../../src/application/services/ticket_service.py#L810) |
| Сдача результата | `ticket.at_work` или `ticket.at_work_remote` | Из `at_work` в `ready_for_review`. Обычный эпизод сдаёт текущий исполнитель, ретроспективный может сдавать другой Admin с общим правом. Remote-only — текущий удалённый исполнитель. | [Команда](../../src/application/services/ticket_service.py#L828) · [Валидаторы](../../src/domain/statuses/rules/ticket_transition_validators.py#L89) |
| Ретроспектива | `ticket.at_work_retrospective` | Времена или длительность, применяются доменные правила назначения и перехода. | [Команда](../../src/application/services/ticket_service.py#L895) |
| Административное завершение | `ticket.executed` | Только из `ready_for_review` в `executed`. Очередь DEC-008 отдельно согласуется. | [Команда](../../src/application/services/ticket_service.py#L950) |
| Отмена / удаление | `ticket.canceled` / `ticket.delete` | Отмена допускается по матрице переходов, требует причины. Удаление физическое, 204, может затронуть связанный TicketUser, допустимо и для активного состояния. | [Команды](../../src/application/services/ticket_service.py#L987) |

`GET /open` и `GET /closed` следуют серверной классификации. Розыск видимых действий использует canonical current status. Неизвестное или отсутствующее состояние показывается в read-only режиме. [Модели](API_CONTRACT.md#уточнения-по-данным-ticket).

## Справочники и роли

| Ресурс | Чтение | Мутации и условия | Источник |
|---|---|---|---|
| Клиенты | `client.view` | Create принимает `client.create` или `client.operation` или `client.decision`. Update/delete — `client.operation`. Enable/disable — `client.decision`. | [Client](../../src/application/services/client_service.py#L82) |
| Отделы | `department.view` | `department.operation`. Сервер проверяет ссылки при отключении/удалении. Для новых связей предлагать только активные отделы. | [Department](../../src/application/services/department_service.py#L78) |
| Сотрудники Admin | `admin.view` | `admin.operation` для профиля, отдела и аккаунта. Grant/revoke отдельно с `role.assign`. При создании с ролями нужны оба разрешения. | [Admin](../../src/application/services/admin_service.py#L135) |
| Пользователи User в Admin | `user.view` | `user.operation` для профиля и аккаунта. Grant/revoke с `role_user.assign`. При создании с ролями нужны оба разрешения. Для grant требуется действующий User и активный клиент. | [User](../../src/application/services/user_service.py#L129) · [Grant](../../src/application/services/user_service.py#L340) |
| Каталоги ролей Admin / User | `role.assign` / `role_user.assign` | Те же отдельные права для create/delete. Системную или назначенную роль нельзя удалить. Для чтения списка строк permission достаточно действующего Admin. | [Роутер](../../src/web/routers/admin/roles.py#L64) · [Сервис](../../src/application/services/role_service.py#L86) |

Профиль субъекта читается по отдельному view. Если доступна операция выдачи роли, но нет права просмотра цели, интерфейс не имитирует наличие справочника и сообщает об ограничении. Выдача действующему получателю и отзыв у отключённого получателя — разные серверные условия. После изменения собственной роли необходимо перечитать /permissions. [Grant/revoke Admin](../../src/application/services/admin_service.py#L321) · [Grant/revoke User](../../src/application/services/user_service.py#L340).

User-доступ вне интерфейса первого релиза. Различия `ticket.view(.all)` и `ticket.operation(.all)` приведены в [API_CONTRACT.md](API_CONTRACT.md).
