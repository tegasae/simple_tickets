# Simple Tickets Frontend

Отдельный frontend-сервис для Simple Tickets.

Структура проекта предполагается такая:

```text
src/        # основной backend
frontend/   # этот frontend-сервис
```

Frontend не импортирует код из `src/`. Он обращается к backend по HTTP.

## Что реализовано

- Страница авторизации администратора: `GET /login`
- Страница клиентов: `GET /clients`
- Авторизация через backend endpoint: `POST /auth/admin/login`
- Хранение access token в HttpOnly cookie frontend-сервиса
- Получение permissions: `GET /admin/admins/permissions`
- Работа с клиентами:
  - `GET /admin/clients/`
  - `POST /admin/clients/`
  - `PUT /admin/clients/{client_id}/contact`
  - `PATCH /admin/clients/{client_id}/enable`
  - `PATCH /admin/clients/{client_id}/disable`
  - `DELETE /admin/clients/{client_id}`

## Важное ограничение текущего API

По текущему OpenAPI обновление клиента доступно только через:

```http
PUT /admin/clients/{client_id}/contact
```

Этот endpoint обновляет только:

```text
email
address
phone
```

Поэтому в форме существующего клиента поле `name` сделано только для чтения.
При создании нового клиента `name` задаётся через:

```http
POST /admin/clients/
```

## Установка

Из корня проекта:

```bash
python -m venv .venv-frontend
source .venv-frontend/bin/activate
pip install -r frontend/requirements.txt
```

## Запуск backend

Пример:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Запуск frontend

Из корня проекта:

```bash
uvicorn frontend.main:app --host 0.0.0.0 --port 8080 --reload
```

Открыть:

```text
http://127.0.0.1:8080/login
```

## Настройка адреса backend

По умолчанию frontend ходит к backend по адресу:

```text
http://127.0.0.1:8000
```

Можно переопределить:

```bash
export BACKEND_BASE_URL=http://127.0.0.1:8000
uvicorn frontend.main:app --host 0.0.0.0 --port 8080 --reload
```

`0.0.0.0` обычно используется для bind-а сервера. Для исходящих запросов удобнее использовать `127.0.0.1`, `localhost` или реальный IP.

## Cookie settings

По умолчанию cookies создаются как `HttpOnly`, `SameSite=Lax`, `Secure=false`.

Для HTTPS можно включить secure cookies:

```bash
export FRONTEND_SECURE_COOKIES=true
```
