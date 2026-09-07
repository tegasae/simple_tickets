# API contract used by User frontend

- `POST /auth/user/login` — `application/x-www-form-urlencoded`: username, password
- `POST /auth/user/refresh` — `{ "refresh_token": "..." }`
- `POST /auth/user/logout` — `{ "refresh_token": "..." }`
- `GET /user/tickets/?client_id=N`
- `POST /user/tickets/`
- `GET /user/tickets/{ticket_user_id}`
- `PATCH /user/tickets/{ticket_user_id}/cancel` — `{ "comment": "..." }`
- `PATCH /user/tickets/{ticket_user_id}/confirm-execution` — `{ "comment": "..." }`

UI treats `UserTicketResponse.ticket_id` as the public TicketUser identifier used in the `/user/tickets/{ticket_user_id}` path.
