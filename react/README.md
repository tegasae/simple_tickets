# Simple Tickets React frontend

Отдельный React/Vite frontend для Simple Tickets API.

## Структура проекта

```text
project/
    src/        # backend
    frontend/   # прежний FastAPI/Jinja frontend
    react/      # этот React frontend
```

## Запуск

```bash
cd react
npm install
BACKEND_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Открыть:

```text
http://127.0.0.1:5173
```

React обращается к backend через `/api/*`. Vite proxy переписывает `/api/admin/clients/` в `http://127.0.0.1:8000/admin/clients/`.

## Что реализовано

- Admin login через `/auth/admin/login`.
- Refresh token через `/auth/admin/refresh`.
- Permissions через `/admin/admins/permissions`.
- Список клиентов загружается целиком, пагинация/сортировка/фильтры выполняются на frontend-е.
- Карточка клиента в диалоге: вкладки `Основное` и `Пользователи`.
- Редактирование клиента: `name`, `email`, `address`, `phone`, `description`, enable/disable.
- Пользователи клиента: список, сортировка, фильтры, карточка справа.
- Пользователь: создание, редактирование, enable/disable.
- Аккаунт пользователя: attach/detach/change password.
- Три темы: `onec`, `classic`, `futuristic`.
- Настройки темы, таблиц, страниц и фильтров сохраняются в `localStorage`.

## Темы

- `onec` — максимально приближённый стиль 1С 8.3: серые панели, плотные таблицы, плоские кнопки, жёлтая рабочая область.
- `classic` — спокойный классический web-интерфейс.
- `futuristic` — тёмная glassmorphism-тема с glow-кнопками, анимациями, живыми панелями и красивым сворачиванием окна клиента.
