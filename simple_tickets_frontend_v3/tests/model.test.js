import assert from "node:assert/strict";
import test from "node:test";
import { queuePath, readRoute } from "../src/app/routes.js";
import { formatDateTime, normalizeTicket, paginate, selectTickets, statusLabel } from "../src/features/tickets/model.js";

const sample = (id, status, date_created, text_of_ticket = "") => normalizeTicket({
  ticket_id: id,
  date_created: "2050-01-01T00:00:00Z",
  current_status: "wrong_status",
  text_of_ticket,
  statuses: date_created ? [{ status: "created", date_created }, { status }] : [],
});

test("a ticket uses the first date and the last status in its history", () => {
  const ticket = sample(1, "ready_for_review", "2026-11-01T10:00:00Z");
  assert.equal(ticket.status, "ready_for_review");
  assert.equal(ticket.createdAt, "2026-11-01T10:00:00Z");
  assert.equal(statusLabel("created"), "Создана");
  assert.equal(statusLabel("created_from_request_user"), "Создана по запросу клиента");
  assert.equal(statusLabel("created_from_ticket_user"), "Создана из заявки клиента");
  assert.equal(formatDateTime(sample(2, "", null).createdAt), "—");
  assert.equal(formatDateTime("not-a-date"), "—");
});

test("search matches the ID, subject, localized status and stable code", () => {
  const rows = [
    sample(1, "created", "2026-11-02T10:00:00Z", "Проверка"),
    sample(2, "created_from_ticket_user", "2026-11-03T10:00:00Z", "Архив"),
  ];
  for (const search of ["№ 2", "Архив", "из заявки клиента", "CREATED_FROM_TICKET_USER"]) {
    assert.deepEqual(selectTickets(rows, { search }).map((row) => row.ticket_id), [2]);
  }
  assert.deepEqual(selectTickets(rows, { status: "created" }).map((row) => row.ticket_id), [1]);
});

test("sorts the whole filtered result before pagination, preserves a tie breaker and puts missing dates last", () => {
  const rows = [
    sample(4, "created", null),
    sample(1, "created", "2026-11-01T10:00:00Z"),
    sample(2, "created", "2026-11-01T10:00:00Z"),
    sample(3, "created", "2026-11-02T10:00:00Z"),
  ];
  assert.deepEqual(selectTickets(rows).map((row) => row.ticket_id), [3, 2, 1, 4]);
  assert.deepEqual(selectTickets(rows, { sort: "created-asc" }).map((row) => row.ticket_id), [2, 1, 3, 4]);
  const page = paginate(selectTickets(rows), 2, 2);
  assert.equal(page.current, 2);
  assert.deepEqual(page.rows.map((row) => row.ticket_id), [1, 4]);
  assert.equal(paginate(rows, 99, 2).current, 2);
});

test("uses only the supported queue URL values and exact positive ticket IDs", () => {
  const route = readRoute("/tickets", "?queue=closed&sort=id-asc&page=2&size=50&search=private");
  assert.deepEqual(route, { page: "queue", queue: "closed", sort: "id-asc", number: 2, size: 50 });
  assert.equal(queuePath(route), "/tickets?queue=closed&sort=id-asc&page=2&size=50");
  assert.equal(readRoute("/tickets", "?queue=review&size=1000000").queue, "open");
  assert.equal(readRoute("/tickets", "?page=1.5").number, 1);
  assert.deepEqual(readRoute("/tickets/3/"), { page: "ticket", id: 3 });
  assert.equal(readRoute("/tickets/0").page, "notFound");
  assert.equal(readRoute("/tickets/9007199254740993").page, "notFound");
});
