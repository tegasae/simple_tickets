# Design boundaries

- This is an **Admin frontend**.
- It manages internal `Ticket`, never `TicketUser`.
- Permission-aware hiding is convenience only; backend RBAC is authoritative.
- Lists are intentionally loaded as whole collections for now, matching the current backend scale and postponed Ticket search.
- No frontend router dependency was added; navigation stays state-based to preserve the small dependency footprint of the original React prototype.
