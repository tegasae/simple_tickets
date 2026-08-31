# Simple Tickets Frontend v3

Отдельный frontend-сервис для административной части Simple Tickets.

## Стек

- FastAPI как frontend gateway/proxy
- Jinja2 templates
- Vanilla JavaScript
- CSS themes
- `localStorage` для пользовательских настроек интерфейса

## Основные экраны

- `/login` — авторизация администратора.
- `/clients` — список клиентов и работа с карточкой клиента.

## Возможности v3

### Клиенты

- Получение полного списка клиентов из backend `GET /admin/clients/`.
- Frontend-пагинация.
- Сортировка по колонкам.
- Фильтрация по колонкам.
- Фильтр по признаку `active / inactive / all`.
- Сохранение настроек таблицы в `localStorage`.
- Карточка клиента в модальном окне.
- Редактирование:
  - `name`
  - `email`
  - `address`
  - `phone`
  - `description`
  - `enabled / disabled`
- Только просмотр:
  - `client_id`
  - `date_created`
  - `created_by_admin`

### Пользователи клиента

- Вкладка `Пользователи` в карточке клиента.
- Загрузка пользователей клиента через `GET /admin/users/?client_id=...`.
- Frontend-сортировка и фильтрация.
- Карточка пользователя справа внутри вкладки.
- Создание пользователя.
- Редактирование basic fields:
  - `first_name`
  - `last_name`
  - `email`
  - `phone`
  - `enabled / disabled`
- Управление аккаунтом пользователя:
  - attach account
  - detach account
  - change password

### Темы интерфейса

- `onec` — стиль 1С 8.3.
- `classic` — классический web-интерфейс.
- `futuristic` — тёмный футуристический стиль.

Тема выбирается при входе или в рабочем интерфейсе и сохраняется в `localStorage`.

## Запуск

Из корня проекта:

```bash
pip install -r frontend/requirements.txt
export BACKEND_BASE_URL=http://127.0.0.1:8000
uvicorn frontend.main:app --host 0.0.0.0 --port 8080 --reload
```

Открыть:

```text
http://127.0.0.1:8080/login
```

## Backend API

Frontend обращается к backend через proxy endpoints `/frontend-api/...`, чтобы хранить access/refresh token в HTTP-only cookies.

Backend по умолчанию ожидается на:

```text
http://127.0.0.1:8000
```

Важно: `0.0.0.0` используется для bind сервера, но клиентские запросы должны идти на `127.0.0.1` или реальный host.

## Permissions

Frontend загружает permissions через:

```http
GET /admin/admins/permissions
```

И скрывает/блокирует операции записи, если нет:

- `client.operation`
- `user.operation`

Для просмотра пользователей учитываются `user.view`, `user.view.all`, `user.operation`, `user.operation.all`.
