import assert from 'node:assert/strict';
import test from 'node:test';
import { confirmsWorkflow, sameWorkflowHistory, sameWorkflowState } from '../src/features/tickets/workflow/receipts.js';

const actorId = 5;
const executorId = 7;
const assigned = { id: 31, status: 'assigned', actor_id: 3, executor_id: executorId, comment: '' };
const date_created = '2026-01-01T09:00:00Z';
const before = {
  statuses: [assigned], current_executor_id: executorId, department_id: 4,
  remote_work_recommended: true, is_closed: false,
};

function after(...records) {
  return { ...before, statuses: [...before.statuses, ...records] };
}

test('pre-read distinguishes workflow drift from unrelated edits', () => {
  assert.equal(sameWorkflowState(before, { ...before, description: 'Edited' }), true);
  assert.equal(sameWorkflowState(before, { ...before, current_executor_id: 9 }), false);
  assert.equal(sameWorkflowState(before, { ...before, remote_work_recommended: false }), false);
  assert.equal(sameWorkflowHistory(before, { ...before, remote_work_recommended: false }), true);
  assert.equal(sameWorkflowState(before, after({ ...assigned, id: 43 })), false);
});

test('repeated assignment requires a new event with the intended actor and executor', () => {
  const payload = { executor_id: executorId };
  assert.equal(confirmsWorkflow(before, before, 'assign', payload, actorId), false);
  assert.equal(confirmsWorkflow(after({ ...assigned, id: 42 }), before, 'assign', payload, actorId), false);
  assert.equal(confirmsWorkflow(after({ ...assigned, id: 42, actor_id: actorId }), before, 'assign', payload, actorId), true);
});

test('hotline confirms assignment and remote start from ACCEPTED, including after later events', () => {
  const accepted = { ...before, statuses: [{ id: 40, status: 'accepted' }], current_executor_id: 0 };
  const assignment = { id: 41, status: 'assigned', actor_id: actorId, executor_id: actorId, comment: '', date_created };
  const work = { id: 42, status: 'at_work', actor_id: actorId, executor_id: 0, work_is_remote: true, comment: '', date_created };
  const snapshot = { ...accepted, statuses: [...accepted.statuses, assignment, work], current_executor_id: actorId };
  assert.equal(confirmsWorkflow(snapshot, accepted, 'startRemoteWork', {}, actorId), true);
  assert.equal(confirmsWorkflow({ ...snapshot, current_executor_id: executorId }, accepted, 'startRemoteWork', {}, actorId), false);
  assert.equal(confirmsWorkflow(snapshot, accepted, 'startRemoteWork', {}, executorId), false);
  const paused = { ...snapshot, statuses: [...snapshot.statuses, { id: 45, status: 'paused' }] };
  assert.equal(confirmsWorkflow(paused, accepted, 'startRemoteWork', {}, actorId), true);
});

test('retrospective receipt matches both events and the submitted mode, time and comment', () => {
  const work = { id: 42, status: 'at_work', actor_id: actorId, work_is_remote: true, duration: 'PT40M', comment: 'Work', date_created };
  const review = { id: 43, status: 'ready_for_review', actor_id: actorId, comment: '', date_created };
  const payload = { work_is_remote: true, duration: 2400, comment: ' Work ' };
  assert.equal(confirmsWorkflow(after(work, review), before, 'registerWork', payload, actorId), true);
  assert.equal(confirmsWorkflow(after(work, review), before, 'registerWork', { ...payload, duration: 1200 }, actorId), false);
  assert.equal(confirmsWorkflow(after({ ...work, work_is_remote: false }, review), before, 'registerWork', payload, actorId), false);
  assert.equal(confirmsWorkflow(after(work, { ...review, date_created: '2026-01-01T09:01:00Z' }), before, 'registerWork', payload, actorId), false);
  const interval = { actual_started_at: '2026-01-01T08:00:00Z', actual_finished_at: '2026-01-01T09:00:00Z' };
  assert.equal(confirmsWorkflow(after({ ...work, ...interval }, review), before, 'registerWork',
    { ...interval, work_is_remote: true, comment: 'Work' }, actorId), true);
});
