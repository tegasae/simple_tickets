import assert from "node:assert/strict";
import test from "node:test";
import { readRoute, relatedPath } from "../src/app/routes.js";
import {
  allowedFields, canCreateTicket, canPostComment, changeNewField, emptyTicket, hasNewDraft, isDirty, withinReplayWindow,
} from "../src/features/tickets/workspaceState.js";

test("author needs client.view and can open the new route without the ticket view grant", () => {
  assert.equal(canCreateTicket(["ticket.created", "client.view"]), true);
  assert.equal(canCreateTicket(["ticket.created"]), false);
  assert.equal(canCreateTicket(["ticket.view", "client.view"]), false);
  assert.deepEqual(readRoute("/tickets/new"), { page: "newTicket" });
});

test("related routes retain the ticket context and validate both identifiers", () => {
  assert.deepEqual(readRoute(relatedPath(17, "user", 5)), { page: "related", id: 17, type: "user", relatedId: 5 });
  assert.equal(readRoute("/tickets/0/client/5").page, "notFound");
  assert.equal(readRoute("/tickets/1/client/0").page, "notFound");
  assert.equal(readRoute("/tickets/1/client/9007199254740993").page, "notFound");
});

test("changing client clears only the dependent selections and keeps the rest of the draft", () => {
  const draft = { ...emptyTicket, client_id: 1, user_id: 9, contact_user_id: 10, text_of_ticket: "Тема" };
  assert.deepEqual(changeNewField(draft, "client_id", 2), {
    ...draft, client_id: 2, user_id: 0, contact_user_id: 0,
  });
  assert.deepEqual(changeNewField(draft, "client_id", 1), draft);
  assert.equal(hasNewDraft(draft), true);
  assert.equal(hasNewDraft(emptyTicket), false);
  assert.equal(isDirty({ changes: {}, comment: "Комментарий" }), true);
});

test("field edits and comments have distinct state and permission requirements", () => {
  assert.deepEqual(allowedFields("created", ["ticket.set_remote_recommendation"]), ["remote_work_recommended"]);
  assert.equal(allowedFields("accepted", ["ticket.operation"]).length, 5);
  assert.deepEqual(allowedFields("at_work", ["ticket.operation", "ticket.set_remote_recommendation"]), []);
  assert.equal(canPostComment("at_work", ["ticket.operation"], false), true);
  assert.equal(canPostComment("at_work", ["ticket.view"], false), false);
  assert.equal(canPostComment("cancelled", ["ticket.operation"], false), false);
  assert.equal(canPostComment("accepted", ["ticket.operation"], true), false);
});

test("an uncertain POST cannot replay outside the safe idempotency interval", () => {
  const intent = { startedAt: 1000 };
  const limit = 23 * 60 * 60 * 1000;
  assert.equal(withinReplayWindow(intent, 1000 + limit - 1), true);
  assert.equal(withinReplayWindow(intent, 1000 + limit), false);
  assert.equal(withinReplayWindow(intent, 999), false);
  assert.equal(withinReplayWindow(null, 1000), false);
});
