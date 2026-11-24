# Повторный независимый консилиум Python-бэкенда

Проверен `tegasae/simple_tickets`, ветка `api-new-client-scheme`, **`bbf7a392dafe0fede2d5d017af36281b6f4f40a2`**. Исходники и прежние материалы не изменены. Предлагаемые исправления применялись только в `/tmp`.

Основные каскадные исправления работают: отключение владельца или клиента закрывает обе карточки на проверке как финальный `SUSPENDED`; `AT_WORK` продолжается; `finish-work` оставляет отдельную проверку. Главный текущий приоритет — обход права назначения пользовательских ролей через создание User. После него следует исправить отзыв ролей, ожидаемые HTTP-ошибки и согласованность правил контакта/отдела.

**Сравнение:** из 23 конкретных групп первого аудита 22 исправлены, 1 исправлена частично — общая обработка ожидаемых ошибок. Из 7 групп патчей предыдущего recheck 6 выполнены, 1 осталась — автор обычного комментария сотрудника. Эти наборы пересекаются; складывать их как 30 независимых ошибок нельзя. Прежние открытые вопросы о контакте, refresh и SQLite-конкуренции перечислены отдельно. В этом проходе впервые выделены **6 тем**: выдача User-ролей при создании, их отзыв, SQL проверки назначений, UTC новых сущностей, включение Admin в отключённом отделе, оставшиеся shell-ссылки на удалённые тесты. Из них именно поломка shell-запуска возникла вследствие удаления тестов; остальные причины уже присутствовали раньше. [Сопоставление каждой прежней находки](previous-findings.md).

## Архитектурная оценка

Разделение на домен, прикладные сервисы, UoW, репозитории, gateway/mapper и FastAPI позволяет локализовать исправления. Версии корней реально проверяются, одна UoW объединяет две карточки, историю и связанные guard-версии. Искусственные сбои второго сохранения и сборки DTO откатывают изменения; это подтверждённая сильная сторона текущей реализации.

Слабое место — согласование правил между слоями. Два статуса одной пары представляют разные уровни детализации; ручная проверка прав повторяется в нескольких командах; типизированные ошибки не везде доходят до HTTP. Поэтому локально корректный код даёт неверный результат на полном пути API → домен → SQLite. Исправление SQL-предиката назначения ролей и ошибки UTC также показывают необходимость интеграционных проверок, а не только проверок отдельных объектов.

Оснований для масштабного переписывания нет. Перед production нужны регрессии критических путей в CI, согласованный жизненный цикл сессий и проверки конкуренции на фактическом PostgreSQL-драйвере. Текущий код подключает SQLite напрямую; изменение одной настройки БД не является готовым переходом на PostgreSQL. Нагрузочные характеристики и эксплуатационная готовность этим аудитом не установлены.

## Снимок, требования и независимость

Первая локальная копия оставалась на `d497e75…`, удалённая ветка уже содержала `bbf7a39…`. Актуальный снимок проверен в отдельной связанной рабочей копии. До создания результатов она была чистой; diff SHA256 — `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Старые 26 неотслеживаемых файлов в исходной копии сохранены. [Полный протокол Git](snapshot.md).

Общий вход первого раунда — 198 файлов, включая 166 Python, текущий README, SQLite DDL и правила. SHA256 [манифеста](input-manifest.json): `8ad0911db59c2828a58f8e215d2ef0da291117ad20be52647d424573472e267d`. Старые экспертные заключения не включались. Собственные пояснения владельца из README извлечены отдельно от чужих выводов; TODO и пометки FIXED не принимались за доказательство. [Требования, наблюдения и вопросы](requirements.md).

После первого раунда владелец уточнил два правила: контакт можно менять через обе карточки при внутреннем `ACCEPTED/DEFERRED`; Admin нельзя включить до включения назначенного отдела или снятия назначения. Первичные заключения сохраняют прежнюю оценку неопределённости, третий раунд и итог учитывают новые ответы.

Координатор и три настоящих подагента первого этапа — модель среды `gpt-6.1-sol`: `/root/third_analyst` (системный анализ), `/root/third_python` (Python/хранение), `/root/third_qa` (QA/FastAPI). Независимый арбитр `/root/third_arbiter` — явно выбранная другая модель **`gpt-6.2-sol`**. Первый раунд проходил в отдельных чистых контекстах с одним пакетом. После его сдачи эксперты получили полные тексты коллег; затем все три критики и выполнили пересмотр. Первоначальный вывод арбитра зафиксирован до знакомства с коллегами. Во время паузы по просьбе владельца агенты были остановлены; продолжили те же агенты.

| Материалы | Системный аналитик | Python | QA |
|---|---|---|---|
| Независимый раунд 1 | [Заключение](experts/round-01/analyst.md) | [Заключение](experts/round-01/python.md) | [Заключение](experts/round-01/qa.md) |
| Перекрёстная критика | [Раунд 2](experts/round-02/analyst.md) | [Раунд 2](experts/round-02/python.md) | [Раунд 2](experts/round-02/qa.md) |
| Пересмотр | [Раунд 3](experts/round-03/analyst.md) | [Раунд 3](experts/round-03/python.md) | [Раунд 3](experts/round-03/qa.md) |

После трёх раундов QA привлёк отдельного помощника `/root/third_qa/previous_recheck` только для статической сверки семи прежних групп. Его [подлинный ответ](experts/support/previous-recheck-helper.md) сохранён; он не подменяет независимые первичные заключения.

Арбитр: [самостоятельный первый вывод](experts/arbiter-initial.md), [итоговый арбитраж](experts/arbiter-final.md). Неизменность первичных файлов проверяется по [их контрольным суммам](experts/initial-report-hashes.json).

## Подтверждённые замечания и порядок исправления

Все ссылки и строки относятся к исходному `bbf7a39`, **до** новых патчей. Высокая уверенность означает достижимый HTTP/SQL-сценарий и сверку кода; предположения о production в таблицу не включены. Полные условия, последствия, пути выполнения и регрессии — в [findings.md](findings.md).

| ID / приоритет | Факт и последствие | Исходник | Исправление и проверка |
|---|---|---|---|
| F01 / P1 | Admin только с `user.operation` создаёт User с привилегированной User-ролью, хотя отдельное назначение ему запрещено. | [user_service.py:75–116](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/application/services/user_service.py#L75-L116) | [01](patches/01-user-role-permissions.patch): дополнительное `role_user.assign`; регрессия отказа без записи и успеха без ролей/с нужными правами. |
| F02 / P2 | Оператор User-ролей может выдать роль, но отзыв требует чужое `role.assign` и даёт 403. | [user_service.py:363–389](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/application/services/user_service.py#L363-L389) | [01](patches/01-user-role-permissions.patch): одинаковое право при выдаче/отзыве; тест с включённым и отключённым Client. |
| F03 / P2 | `is_assigned` не замечает `users_roles`. DELETE доходит до FK и даёт 500; FK сохраняет роль. | [role_gateway.py:32–44](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/adapters/repositories/gateways/role_gateway.py#L32-L44) | [03](patches/03-role-assignment-query.patch) + [02](patches/02-expected-input-errors.patch): стандартный CASE/EXISTS, корректный 400 до DELETE; SQL и HTTP-регрессии. |
| F04 / P2 | Self-disable, удаление назначенной/системной роли и отрицательные Client/Role ID дают 500 вместо ожидаемого отказа. | [main.py:68–92](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/web/main.py#L68-L92), [role_service.py:96–105](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/application/services/role_service.py#L96-L105) | [02](patches/02-expected-input-errors.patch): `ApplicationValidateError` → 400; ошибки сохранения остаются серверными. |
| F05 / P2 | Неверные пароль/login/permission и слишком длинное description проходят HTTP-модель, затем `ValueError` превращается в 500. | [account.py:47–83](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/account.py#L47-L83), [tickets.py:88–91](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/web/models/tickets.py#L88-L91), [role_service.py:13–46](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/services/role_service.py#L13-L46) | [02](patches/02-expected-input-errors.patch): узкая доменная классификация и ограничения HTTP; 400/422, прежние данные сохранены, граница description 4000 работает. |
| F06 / P2 | Контакт связанной принятой заявки нельзя изменить: разрешение Ticket сталкивается с запретом TicketUser.IN_WORK. | [ticket_sync_service.py:137–142](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/services/ticket_sync_service.py#L137-L142), [ticket_user.py:228–241](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/ticket_user.py#L228-L241) | [05](patches/05-paired-contact-edit.patch): отдельное право изменения контакта; обе стороны CREATED/ACCEPTED/DEFERRED; более поздние состояния атомарно отклоняются. |
| F07 / P2 | Отключённый сотрудник включается в уже отключённом отделе — запрещённая владельцем комбинация флагов. | [admin_service.py:387–408](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/application/services/admin_service.py#L387-L408), [domain enable:169–174](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/services/admin_service.py#L169-L174) | [09](patches/09-admin-enable-department.patch): загрузка, проверка и touch отдела в UoW; успех после включения отдела/снятия назначения. |
| F08 / P2 | Обычный комментарий Admin при регистрации за User записан от имени владельца. | [ticket_user.py:117–123](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/ticket_user.py#L117-L123), [create_ticket:152–160](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/application/services/ticket_service.py#L152-L160) | [04](patches/04-staff-comment-author.patch): автор комментария — действующий Admin; начальный CREATED.actor этим патчем не меняется. |
| F09 / P2 | После переназначения login другому User старая refresh-сессия проверяет нового владельца имени, но выдаёт JWT со старым ID. | [auth_service.py:163–179](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/web/auth/services/auth_service.py#L163-L179), [refresh:225–249](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/web/auth/services/services.py#L225-L249) | [06](patches/06-refresh-subject-identity.patch): сверка ожидаемого стабильного subject ID; две HTTP-регрессии memory/SQLite. Захват другого аккаунта не доказан. |
| F10 / P2 | Local naive даты новых Department/Employee/Account объявляются UTC при чтении. На UTC+03 подтверждён сдвиг 10800 секунд. | [department.py:27](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/department.py#L27), [employee.py:97](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/employee.py#L97), [datetime_check.py:86–89](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/domain/datetime_check.py#L86-L89) | [07](patches/07-utc-dates.patch): aware UTC только для новых defaults/fallbacks; UTC/UTC+03, HTTP/SQL roundtrip, исторические даты не переписываются. |
| F11 / P2, SQLite | Read→write конфликт возникает до CAS версий и даёт 500; отдел иногда объявляет любую ошибку записи дублем. | [query.py:17–27](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/utils/db/query.py#L17-L27), [department_repository.py:58–86](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/src/adapters/repositories/department_repository.py#L58-L86) | [08](patches/08-database-error-classification.patch): временный отказ основной БД → 503, unique → 409, неизвестный сбой → 500; rollback/два HTTP-писателя/COMMIT проверены. |
| F12 / P3 | Оба shell-launcher ищут удалённый `tests_pyramid/pytest.ini` и завершаются exit 4 до запуска. | [run_pyramid.sh:3](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/run_pyramid.sh#L3), [run_coverage.sh:3](https://github.com/tegasae/simple_tickets/blob/bbf7a392dafe0fede2d5d017af36281b6f4f40a2/run_coverage.sh#L3) | [10](patches/10-current-test-launchers.patch): убрать отсутствующий target; явный каталог новых тестов собирается. Default CI требует отдельного актуального набора. |

Рекомендуемая последовательность: **01 → 02+03 → 04+05+09 → 06+07 → 08 → 10**, с регрессиями на каждом шаге. Нумерация файлов — идентификаторы, а не обязательный продуктовый приоритет. Весь комплект также проверен в порядке имён 01–10. [Описание каждого предлагаемого изменения и его границ](patches/README.md).

## Реально выполненные проверки

Python 3.12.14, SQLite 3.53.1; зависимости текущих requirements. [Точные версии](tests/environment.json), [команды и инструкции](tests/README.md), [результаты каждого теста без тел запросов/ответов](tests/results.json).

| Проверка | Исходный снимок | Временная копия после всех патчей |
|---|---|---|
| Синтаксис и основные импорты | 166 Python AST; `main`, `src.web.main`, `src.oauth2.main` импортируются | 167 AST, те же 3 импорта успешны |
| Подготовка gateway SQL | 115 EXPLAIN прошли на свежем DDL; это не доказательство логики запроса | Меняемый role SQL дополнительно проверен данными |
| 39 регрессий первого аудита | 37 passed, 2 failed из-за отменённой политики review | 37 passed, 2 deselected как неактуальные; новые тесты проверяют актуальное правило |
| 21 регрессия предыдущего recheck | 20 passed, 1 failed: автор комментария | 21 passed |
| 70 новых проверок | **29 passed, 41 failed**, без ошибок сборки | **70 passed** |
| Совместный итог | 86 passed, 44 failed, exit 1 | **128 passed, 2 deselected, exit 0** |
| Все 10 diff | Индивидуально `git apply --check --whitespace=error-all` | Последовательные check и реальное применение успешны |
| Стандартная сборка тестов / shell | `tests/` и `tests_pyramid/` отсутствуют. На layout с историческими review-тестами сборка останавливается с 2 import errors. Shell: exit 4 | Shell с явным `recheck_tests --collect-only`: exit 0, 70 collected. Запуск без target этим не объявлен исправленным |

В первом промежуточном patched-прогоне старый COMMIT-тест остановился на изменённом тексте исключения; операция `commit` затем сохранена в диагностике, тест в окончательном наборе проходит. Это не скрытый третий исключённый тест. Окончательный прогон дал 848 предупреждений зависимостей/устаревшего datetime adapter; они не превращены в 848 дефектов. Метрика покрытия всего продукта не измерялась.

## Ограничения и вопросы, которые остались

Проверены Python-домен, сервисы, UoW, SQL/gateway/mapper, схема, реальные зарегистрированные HTTP-пути и соответствующая документация. Данные только синтетические, SQLite временная. Фронтенд, архивы, рабочие БД, `.env`, реальные секреты и персональные данные не открывались. PostgreSQL, нагрузка, несколько серверов и production-конфигурация не проверялись.

- При `assign(self)` и удалённом самоназначении отсутствует общий guard версии Admin, присутствующий для другого исполнителя. Возможна гонка с disable/change_department на будущем PostgreSQL READ COMMITTED; на текущей SQLite нарушение инварианта не воспроизведено. До миграции нужны общий протокол guard и две транзакции с фактическим драйвером.
- Административный contact=0 и пользовательский contact=0 имеют разную семантику. Ответ о статусах её не определил; патч05 не меняет правило нуля.
- Кто записывается в initial CREATED.actor при регистрации за User, нужно явно описать отдельно от автора комментария. Существующее поведение owner сохранено; отдельного ответа владельца о семантике этого поля нет.
- Согласовать JSON-форму вложенных комментариев Ticket/TicketUser до изменения внешних типов. Поломка конкретного потребителя не установлена.
- Определить окончательный отзыв refresh при disable/смене аккаунта, допустимость оживания прежней сессии при reattach тому же субъекту, абсолютный срок и sliding TTL. Патч06 исправляет только несовпадение ID при переиспользовании имени. Патч08 относится к основной БД через Connection/Query; отдельный TokenStorageSQLite им не покрыт.
- UNIQUE пары, идемпотентность, автоматические повторы и оптимизация списков — отдельные решения. Дубли пары через штатный API не показаны; совпадение текста не является ключом операции. Масштабной переработки вместо указанных небольших исправлений не предлагается.

Прежние отчёты и первичные тексты сохранены. Финальные проверки области изменений перечислены в [git-verification.md](git-verification.md). PR, merge, commit и отправка в удалённую ветку не выполнялись; результат предоставлен как изменения задачи.
