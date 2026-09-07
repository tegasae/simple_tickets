# Validation against uploaded `simple_tickets(3).zip`

Run date: 2026-09-04

- collected: **355 tests**
- passed: **349**
- failed: **6**
- active-backend coverage with supplied `.coveragerc`: **~81%**

The six failures are strict regression tests and represent production differences
in the uploaded archive:

1. `ClientApplicationService.disable()` persists a changed Ticket twice.
2. `TicketApplicationService.create_ticket()` in the uploaded archive does not
   reject a disabled Department.
3. `TicketApplicationService.update_details()` in the uploaded archive accepts
   a new contact User belonging to another Client.
4. `TicketUserApplicationService.create_from_user()` in the uploaded archive
   does not reject a disabled Department.
5. `UserApplicationService.delete()` does not detect references from an
   internal Ticket when no TicketUser exists.
6. `GET /admin/tickets/` dispatches to `ticket_search_service().search()`, while
   that service is not exposed by the active `ApplicationServiceFactory`;
   the contract expects `ticket_service().get_all()` according to the current
   decision to postpone search.

Items 2–4 were subsequently discussed/fixed in the conversation, so a newer
local working tree should pass those corresponding tests.

The tests are intentionally not marked `xfail`: after each production fix the
suite should become greener without modifying the regression test.
