# Заметки по React frontend v1

## Решения

- Папка проекта: `react/`, параллельно с `src/` и прежним `frontend/`.
- Стек: React + Vite + vanilla CSS, без UI-библиотек.
- Backend вызывается через `/api/*`; в dev-режиме Vite проксирует запросы на `BACKEND_BASE_URL`.
- Настройки пользователя хранятся в `localStorage`:
  - тема интерфейса;
  - фильтры/сортировка/страницы таблицы клиентов;
  - фильтры/сортировка/страницы таблицы пользователей по каждому клиенту;
  - активная вкладка карточки клиента.

## Реализованные экраны

- Admin login.
- Рабочая область клиентов.
- Таблица клиентов с frontend-пагинацией, сортировкой, фильтрами по колонкам и фильтром `Все / Активные / Неактивные`.
- Карточка клиента в modal-window.
- Вкладка клиента `Основное`.
- Вкладка клиента `Пользователи`.
- Карточка пользователя справа внутри вкладки пользователей.
- Account panel пользователя: attach/detach/change password.

## Темы

- `onec`: плотный серо-жёлтый интерфейс, приближённый к 1С 8.3.
- `classic`: спокойный современный web-интерфейс.
- `futuristic`: тёмный glassmorphism, glow-кнопки, animated grid, hover-анимации, holographic modal open и animated minimize.

## Permissions

Frontend скрывает/отключает операции через permissions:

- `client.view` / `client.operation`
- `user.view` / `user.operation`

Проверки на frontend-е не заменяют backend RBAC, а только улучшают UI.

## Важные endpoint-ы

- `POST /auth/admin/login`
- `POST /auth/admin/refresh`
- `POST /auth/admin/logout`
- `GET /admin/admins/permissions`
- `GET /admin/clients/`
- `POST /admin/clients/`
- `GET /admin/clients/{client_id}`
- `PUT /admin/clients/{client_id}/contact`
- `PATCH /admin/clients/{client_id}/enable`
- `PATCH /admin/clients/{client_id}/disable`
- `DELETE /admin/clients/{client_id}`
- `GET /admin/users/?client_id=...`
- `POST /admin/users/`
- `PUT /admin/users/{employee_id}`
- `PATCH /admin/users/{employee_id}/enable`
- `PATCH /admin/users/{employee_id}/disable`
- `POST /admin/users/{employee_id}/account`
- `DELETE /admin/users/{employee_id}/account`
- `PATCH /admin/users/{employee_id}/password`

## Ограничения первой React-версии

- Роли пользователей пока не редактируются в UI.
- Карточка admin-ов и заявки ещё не реализованы.
- Таблицы сделаны вручную, без TanStack Table/DataGrid.
- Список клиентов целиком загружается в браузер; это нормально для ожидаемых 150–500 клиентов.
