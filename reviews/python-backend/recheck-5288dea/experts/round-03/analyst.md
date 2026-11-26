# Эксперт А: решения после критики и два узких патча, раунд 03

24.11.2026. Полностью прочитаны `experts/round-02/{analyst,python,qa}.md`. Новых требований после OWNER-CONFIRMATION не использовано. Первые два раунда не переписывались.

Вход прежний: код `5288dea85d8f7e7e4c84d4801781d297e0e14475`. Повторная проверка всех 205+2 файлов дала совпадение с манифестами:

- code manifest SHA256: `00c005b64c36f100382334212b0f71e2e7bc390a31cb0e08001f2e81672717bf`;
- requirements manifest SHA256: `ed4dd4e6ad341b1713b8bf404c9f19dba239425375793b1f973e0a9cd3b5d287`.

## Принято, отклонено, уточнено

| Вопрос | Решение и основание |
|---|---|
| Отзыв refresh и постоянная идентичность Account | **Принято.** Устаревшие refresh переживают password/disable-enable; мой Account replacement воспроизведён QA независимо. Отсутствие account_id и общей session UoW — подтверждённые причины. Разрешённый TTL ранее выданного access не разрешает выдавать новые пары через отозванный refresh. Два настоящих concurrent refresh не заменяют тест refresh/login против отзыва. |
| Абсолютный срок сессии и defaults | **Принято с разделением.** Скользящий срок и access за первоначальным пределом подтверждены даже с 5 минутами/7 сутками. Defaults 30 минут/1 сутки — отдельное расхождение кода; реальные env overrides неизвестны. Прямой TokenService test доказывает логику, QA HTTP test подтверждает активный путь. Production готовность этим не доказана. |
| Идемпотентность | **Принято как отсутствие обязательной реализации.** Десять создающих маршрутов, кроме отдельного Account. Повторный Department 409 по имени не является replay. 24-часовой срок не проверен как работающий механизм: такого механизма нет. Исправление middleware после COMMIT или UNIQUE на связь Ticket/TicketUser обязательство не выполняет. |
| TicketUser.CREATED.actor при Admin регистрации | **Принято.** Owner и инициатор разделяются; ошибка узко подтверждена во внешней истории. Подготовлен patch 01. |
| Ноль во внутренней автоматической Ticket.CREATED_FROM_TICKET_USER | **Отклонено как доказанный дефект.** QA во втором раунде снял эту нормативную претензию. Системная convention прямо описана в `tickets.md:210–241` и поддержана кодом; OWNER-CONFIRMATION не расширяет требование явно на это событие. Patch 01 её сохраняет; не меняет user_action validators. |
| Administrative JSON comments | **Принято.** Обычные и статусные комментарии, включая пустой, должны быть строками на web/DTO boundary. Доменный VO и persistence корректно остаются объектами. Подготовлен patch 02. |
| Self-assignment guard | **Принято как существенный риск с точной границей.** Оба endpoint достижимы, CAS Admin пропущен и version delta 0 подтверждена несколькими экспертами. Успешный запрещённый interleaving на PostgreSQL не выполнен; нельзя повышать до доказанного PG runtime-инцидента или объявлять исправленным одним SQLite-тестом. |
| Department без touch в пользовательском create | **Уточнено.** Application DTO допускает ветку, но User HTTP model запрещает поле; QA получил 422 настоящим запросом. Это латентный риск прямого application caller/будущего API, не подтверждённая гонка активного User POST. |
| NULL version | **Принято как условная DDL/persistence несовместимость.** Собственный repository test и HTTP QA подтверждают TypeError/500 Department/Admin и ложный version conflict User/Client. Путь появления NULL штатным текущим API не показан; рабочие данные не проверялись. Нельзя называть массовой production поломкой. Нужен единый data contract, а не только локальное исправление int(None). |
| Ссылка на change_contact_user в моём раунде 1 | **Уточнено по замечанию QA.** Правильный anchor текущего SHA: `src/domain/ticket.py:465–482`, запрет очистки при user_id>0 — `:477–480`. Старый anchor `:493–512` неточен. Содержательный положительный вывод сохраняется. |
| User confirmation и отдельный execute | **Уточнено.** Текущий terminal CONFIRMED_BY_USER нельзя менять по одному старому фрагменту целевого документа. Последнее обязательное решение эту ветвь явно не переопределяет. Дополнительный договор нужен до смены workflow. |

Принимаю ограничения испытаний коллег: SQL smoke не проверяет все бизнес-результаты SELECT; SQLite ASGI-тесты не заменяют PG, workers, рестарт и внешний deployment. Не возвращаю в список дефектов допустимое сохранение AT_WORK у отключённого Client и отдельный execute после finish. Отсутствие UNIQUE пары, неизмеренная производительность и предложенные параметры мониторинга не становятся доказанными runtime ошибками.

## Подготовленные patch 01 / 02

Исходники менялись только в `/tmp/analyst-patches-5288dea-K6XJbr`. В выходном каталоге сохранены обычные unified diff относительно неизменного input SHA:

- `patches/01-created-actor.patch`: 3 production-файла. Добавляет необязательный keyword `actor_employee_id` в `TicketUser.create` и `TicketUserService.create`, с прежним fallback на владельца при отсутствии параметра. Административный application path передаёт фактического Admin. Начальная ordinary comment фабрики с явно заданным инициатором также принадлежит ему; прежние вызовы без keyword сохраняют прежнюю семантику. Докстринги уточнены. Owner user_id и внутренний системный actor не меняются.
- `patches/02-admin-comment-json.patch`: 1 production-файл, административный assembler. Обычные comments извлекают строку `.value`, status comments извлекают CommonComment.value либо пустую строку для Empty. Domain VO, persistence и статусный граф не меняются.
- `tests/test_history_and_json.py`: 9 regression cases на неизменённой общей fixture `tests/conftest.py`, с настоящим HTTP login/dependencies/UoW и последующим чтением сохранённой истории. Покрыты Admin for User, User self-create, standalone Admin, старые factory calls без keyword, явно заданный factory initiator, три вида административного JSON ответа и сохранение legacy actor при чтении.

Историческая граница принципиальна: patch исправляет **новые регистрации**. В уже сохранённых строках owner ID не позволяет достоверно восстановить фактического инициатора. Обычный комментарий Admin также не является универсальным доказательством автора первоначального действия. Нет миграции/перезаписи historical rows; regression с синтетической legacy-строкой проверяет, что чтение не «угадывает» нового actor. Применение patch не исправит задним числом уже ошибочную историю.

## Проверка before / after

Для проверки самих опубликованных diff использована вторая чистая копия `/tmp/analyst-before-5288dea-Q8U804`, созданная из input. Общая fixture скопирована без изменений: SHA256 `3d58984b6e1be01e0005a8726b76aeb8908d462649b276b696549b10ee05d098` совпадает в output и обеих проверочных копиях. Все БД временные по текущему DDL, credentials случайные, `.env`/реальные БД не использовались.

Команды в этой чистой копии (до и после один и тот же тестовый файл):

```bash
cd /tmp/analyst-before-5288dea-Q8U804
PYTHONDONTWRITEBYTECODE=1 /tmp/tickets-bbf7a39-venv/bin/python -m pytest tests/test_history_and_json.py -p no:cacheprovider
patch --dry-run -p1 -i /workspace/work/simple_tickets-5288dea/reviews/python-backend/recheck-5288dea/patches/01-created-actor.patch
patch -p1 -i /workspace/work/simple_tickets-5288dea/reviews/python-backend/recheck-5288dea/patches/01-created-actor.patch
patch --dry-run -p1 -i /workspace/work/simple_tickets-5288dea/reviews/python-backend/recheck-5288dea/patches/02-admin-comment-json.patch
patch -p1 -i /workspace/work/simple_tickets-5288dea/reviews/python-backend/recheck-5288dea/patches/02-admin-comment-json.patch
PYTHONDONTWRITEBYTECODE=1 /tmp/tickets-bbf7a39-venv/bin/python -m pytest tests/test_history_and_json.py -p no:cacheprovider
```

Результаты финального тестового набора:

| Состояние | Результат | Примечание |
|---|---|---|
| Исходный SHA | **5 failed, 4 passed** | Неверный initial Admin actor; новый optional explicit actor ещё не поддерживается; три JSON contract cases получают объекты |
| Оба опубликованных patch применены | **9 passed** | Оба dry-run и применения чистые; pytest exit 0 |

Логи только в /tmp: `before-history-json.txt`, `after-applied-history-json.txt`. Имеющиеся 66 предупреждений о deprecated Pydantic/SQLite datetime API и TestClient зависимости не относятся к этим двум fixes. Полный существующий test suite не заявляется пройденным; это целевые регрессии двух узких исправлений.

## Оставшиеся работы и вопросы

Эти два patch не исправляют auth срок/отзыв, идемпотентность и executor guard. Для session revoke нужен завершённый сквозной протокол общей UoW, постоянной Account identity и согласования login/refresh с mutation; post-commit revoke hook недостаточен. Для уже ротированных старых сессий истинная первоначальная дата может быть утрачена — нельзя обещать восстановить её из текущего created_at; переходный режим требует явного решения. Идемпотентность должна охватывать всю согласованную область и фиксировать результат вместе с бизнес-эффектом до COMMIT; серверные авторетраи не добавляются. Конкретные ещё не выбранные технические лимиты не выдаются за новые требования.
