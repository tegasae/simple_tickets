# Независимое первичное заключение арбитра

Снимок: `d497e75d4937e8edea98783a5af924c247622e06`, ветка `api-new-client-scheme`. Прочитаны только исходники и `/tmp/tickets-recheck-user-notes.md`; старый аудит и заключения коллег не читались. Исходники не изменены, `.env` и реальные БД не открывались. Проверка авторизации исключительно статическая.

## A1 — P1: каскад отключения клиента блокируется обычными открытыми заявками

Основное место: `src/domain/services/client_service.py:226–235`, безусловный `ticket.suspend()`. Достижимость: `PATCH /admin/clients/{client_id}/disable` (`src/web/routers/admin/clients.py:152–168`) → application `disable` → `tickets.get_open(client_id)` → gateway `WHERE date_finished IS NULL` (`src/adapters/repositories/gateways/ticket_gateway.py:58–67`). Оба состояния AT_WORK и READY_FOR_REVIEW имеют `date_finished=None`, но перехода SUSPENDED нет в `src/domain/statuses/rules/ticket_status_transition.py:76–96,113–119`.

Следствие: одной такой заявки достаточно для DomainOperationError и отката всей транзакции, клиент и пользователи остаются включёнными. Для AT_WORK это противоречит собственному правилу сервиса «работа продолжается»; для READY_FOR_REVIEW — прямому уточнению автора о переходе в SUSPENDED. Это не требование автоматически выполнять заявку и не предложение восстанавливать SUSPENDED: эти решения автора сохранены.

Доказательство на синтетических объектах: стандартные `Ticket.create → accept → assign → start_work` и `Ticket.create → accept → assign → register_work(duration=1 minute)` создают соответственно AT_WORK и READY_FOR_REVIEW. В обоих случаях `ClientService.disable(client=synthetic_client, users=[], open_tickets=[ticket], open_ticket_users=[], actor_employee_id=1)` выдаёт `status transition is not allowed: at_work -> suspended` / `ready_for_review -> suspended`. Реальные БД не использовались. Правильный ремонт должен одновременно исключить AT_WORK из каскада и реализовать согласованный READY_FOR_REVIEW → SUSPENDED.

## A2 — P2: тот же пропущенный переход мешает отключать пользователя после завершения работы

Основное место: `src/domain/services/user_service.py:376–379`; отбор `_should_suspend` в строках 435–448 исключает только терминальные состояния и AT_WORK. READY_FOR_REVIEW попадает в список и падает на `suspend()`, поскольку соответствующего ребра нет (ссылка выше). Достижимость: `PATCH /admin/users/{employee_id}/disable`, `src/web/routers/admin/users.py:351–366`, затем application `disable` в строках 458–493. Условие — хотя бы одна связанная заявка пользователя или контактного пользователя в READY_FOR_REVIEW. Вся транзакция откатывается, пользователь не отключается. Это общий корень с A1, их следует объединить в итоговом списке, сохранив обе точки входа и отдельную ошибку AT_WORK для клиента.

## A3 — P2: штатный набор тестов остался на удалённом интерфейсе

`run_pyramid.sh:3` запускает `tests_pyramid`, но `tests_pyramid/unit/domain/test_domain_services.py:10` импортирует отсутствующий `AdminDepartmentService` из модуля, где объявлен только `AdminService`. Строки 11–15 импортируют пять вообще отсутствующих модулей `ticket_client_service`, `ticket_execution_service`, `ticket_management_service`, `ticket_review_service`, `ticket_user_sync_service`. Это детерминированный ImportError при сборке даже до проверки поведения. Также корневой `pytest.ini:2` указывает отсутствующий каталог `tests`.

Ограничение проверки: попытка `python -m pytest --collect-only -q tests_pyramid/unit/domain/test_domain_services.py` остановилась раньше: в доступном Python отсутствует pytest. Поэтому фактическое сообщение pytest о сборке не заявляется; несовместимые импорты подтверждены сравнением с перечнем файлов и определениями классов. Тесты требуют обновления, прежде чем их можно использовать как доказательство исправлений.

## A4 — явный незавершённый запрос, отдельно от регрессий: постоянного хранилища refresh-токенов нет

Автор прямо просил память и постоянное хранилище (заметка 159). `src/web/auth/storage.py` содержит только абстрактный TokenStorage и TokenStorageMemory; зависимости `src/web/dependencies/auth.py:39–40` жёстко создают память. Встроенное описание самого класса предупреждает о потере при рестарте и несовместимости с несколькими worker (`storage.py:59–65`). Это подтверждённый пробел выполнения запроса, а не неожиданная новая уязвимость. При нескольких процессах refresh произвольно попадает в процесс без токена; после рестарта refresh утрачивается. Дополнительно обе переменные realm фактически указывают на один singleton (`storage.py:68–76`), но проверки subject_type в refresh/logout препятствуют прямому смешению realm, поэтому отдельный security finding из этого не вывожу.

## Что не следует ошибочно объявлять дефектом

SUSPENDED у TicketUser сознательно терминален. `finish-work` оставляет READY_FOR_REVIEW согласно воле автора. Встроенная production SECRET_KEY отклоняется валидатором, несмотря на оставшееся значение по умолчанию. Ответ DTO, сформированный внутри `with`, не возвращается вызывающему коду до успешного `__exit__`; сам по себе такой `return` не доказывает потерю коммита.
