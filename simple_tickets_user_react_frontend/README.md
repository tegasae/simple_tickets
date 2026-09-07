# Simple Tickets — User React frontend

Отдельный frontend для User, принадлежащего Client.

## Что умеет

- Login / refresh / logout через `/auth/user/*`.
- Получение заявок текущего пользователя через `GET /user/tickets/?client_id=...`.
- Создание `TicketUser` через `POST /user/tickets/`.
- Просмотр карточки, пользовательской истории статусов и комментариев.
- Отмена пользователем только из `created`.
- Подтверждение выполнения только из `waiting_for_confirmation`.
- Четыре темы: 1С 8.3, классическая, футуристическая и Barbie.
- Адаптивная верстка.

Frontend не обращается к внутреннему `/admin/tickets/*` и не показывает внутренний `Ticket`.

## Client ID

Текущий API требует `client_id` для `GET /user/tickets/` и `POST /user/tickets/`, но не предоставляет отдельного `/user/me`, откуда frontend мог бы получить Client автоматически. Поэтому Client ID вводится на странице login и хранится локально как контекст организации. В `/auth/user/login` он не отправляется.

Backend должен самостоятельно проверять, что аутентифицированный User принадлежит указанному Client.

## Запуск

```bash
npm install
npm run dev
```

По умолчанию Vite dev-server: `http://127.0.0.1:5175`.

Backend: `http://127.0.0.1:8000`, запросы `/api/*` проксируются Vite на backend.

Production:

```bash
npm run build
```
