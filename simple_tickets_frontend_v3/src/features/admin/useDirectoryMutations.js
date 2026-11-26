import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../api/transport.js";
import { errorText, t } from "../../shared/i18n/messages.js";
import { isUnknownWrite, operationKey, withinReplayWindow } from "../tickets/workspaceState.js";
import { canDirectory, canDirectoryAction, directoryFormValues, directoryPayload, DIRECTORIES } from "./directoryModel.js";

const idle = Object.freeze({ busy: false, feedback: null });
const rolesActions = ["grantRoles", "revokeRoles"];

function scope(resource, id) {
  return `${resource}:${id ?? "new"}`;
}

function sameValue(left, right) {
  if (Array.isArray(left) && Array.isArray(right)) {
    return left.length === right.length && left.every((value) => right.includes(value));
  }
  return left === right;
}

function matches(record, expected) {
  return Object.entries(expected).every(([key, value]) => sameValue(record[key], value));
}

function snapshotFields(resource, record) {
  const fields = (DIRECTORIES[resource].fields.update ?? []).map((field) => field.name);
  return Object.fromEntries([...fields, "enabled", "enabled_login", "login", "department_id", "roles", "is_system_role"]
    .map((key) => [key, record[key]]));
}

function feedback(status, key, extra) {
  return { status, message: t(key), ...extra };
}

function expectedCommand(action, data) {
  if (action === "enable" || action === "disable") return { enabled: action === "enable" };
  if (action === "enableAccount" || action === "disableAccount") return { enabled_login: action === "enableAccount" };
  if (action === "attachAccount") return { login: data.login.trim(), enabled_login: data.enable_account };
  if (action === "detachAccount") return { login: "", enabled_login: false };
  if (action === "changeDepartment") return { department_id: data.department_id };
  if (action === "removeDepartment") return { department_id: 0 };
  return null;
}

function observed(record, expectation) {
  if (expectation?.roles) {
    return expectation.roles.every((id) => record.roles.includes(id) === expectation.granted);
  }
  return Boolean(expectation?.fields && matches(record, expectation.fields));
}

export function useDirectoryMutations(api, session, onChanged) {
  const [entries, setEntries] = useState({});
  const running = useRef(new Map());
  const uncertain = useRef(new Map());

  useEffect(() => () => {
    for (const controller of running.current.values()) controller.abort();
    running.current.clear();
    uncertain.current.clear();
  }, []);

  function update(key, patch) {
    setEntries((previous) => ({ ...previous, [key]: { ...(previous[key] ?? idle), ...patch } }));
  }

  function start(key) {
    if (running.current.has(key)) return null;
    const controller = new AbortController();
    running.current.set(key, controller);
    update(key, { busy: true });
    return { controller, signal: api.bindSignal(controller.signal) };
  }

  function finish(key, controller) {
    if (running.current.get(key) !== controller) return;
    running.current.delete(key);
    update(key, { busy: false });
  }

  async function perform({ resource, id, allow, prepare, ownPermissions = false, signInAgain = false, replaying = false }) {
    const key = scope(resource, id);
    const currentRights = () => session.getSnapshot().permissions;
    if (uncertain.current.has(key) && !replaying) return feedback("unconfirmed", "directory.writeUnconfirmed");
    if (!allow(currentRights())) return feedback("rejected", "work.writeForbidden");
    const work = start(key);
    if (!work) return null;
    const { signal, controller } = work;
    let request;
    let sent = false;
    let result;
    let denied = false;
    try {
      update(key, { feedback: null });
      const latest = id === undefined ? null : await api.get(resource, id, { signal });
      signal.throwIfAborted();
      if (!allow(currentRights())) throw new ApiError(403);
      request = prepare(latest);
      sent = Boolean(request.send);
      const record = request.send ? await request.send(signal) : latest;
      signal.throwIfAborted();
      if (request.expectation && record && !observed(record, request.expectation)) {
        throw new ApiError(200, "invalid-response");
      }
      if (request.responseFields && (!record || !matches(record, request.responseFields))) {
        throw new ApiError(200, "invalid-response");
      }
      result = feedback("success", "directory.writeSuccess", { record, removed: request.removing === true });
      uncertain.current.delete(key);
      if (sent) onChanged();
    } catch (error) {
      if (signal.aborted) return null;
      denied = error?.status === 401 || error?.status === 403;
      if (sent && error?.code !== "invalid-request" && isUnknownWrite(error)) {
        uncertain.current.set(key, {
          expectation: request.expectation, removing: request.removing === true, replay: request.replay, ownPermissions,
          passwordChange: request.passwordChange === true,
        });
        result = feedback("unconfirmed", request.passwordChange ? "directory.passwordUnconfirmed" : "directory.writeUnconfirmed");
        onChanged();
      } else if (replaying) {
        result = feedback("unconfirmed", "directory.writeStillUnconfirmed");
      } else if (error?.status === 409 || (!sent && error?.status === 404)) {
        result = feedback("conflict", "directory.writeConflict");
      } else if (error?.status === 422) {
        result = feedback("rejected", "directory.writeValidation", { fields: error.fields });
      } else if (error?.status === 400 && request?.removing) {
        result = feedback("rejected", "directory.deleteBlocked");
      } else {
        result = { status: "rejected", message: error?.status === 403 ? t("work.writeForbidden") : errorText(error) };
      }
      if (!ownPermissions && denied) {
        void session.reloadPermissions().catch(() => {});
      }
    } finally {
      finish(key, controller);
    }
    if (signal.aborted) return null;
    const { record, ...message } = result;
    const pending = uncertain.current.get(key);
    update(key, { feedback: message, canReplay: withinReplayWindow(pending?.replay), passwordPending: pending?.passwordChange });
    if (ownPermissions && denied && !sent) {
      await session.recheckPermissions();
    }
    if (signInAgain && result.status === "success") void session.logout();
    return signal.aborted ? null : result;
  }

  function createRequest(resource, replay) {
    const { payload, idempotencyKey } = replay;
    return { replay, send: (signal) => api.create(resource, payload, { signal, idempotencyKey }) };
  }

  function save({ resource, id, mode, values, baseline }) {
    const creating = mode === "create";
    return perform({
      resource, id, allow: (permissions) => canDirectory(resource, creating ? "create" : "update", permissions),
      prepare(latest) {
        if (creating) {
          const payload = directoryPayload(resource, "create", values);
          return createRequest(resource, { payload, idempotencyKey: operationKey(), startedAt: Date.now() });
        }
        const prior = directoryPayload(resource, "update", directoryFormValues(resource, "update", baseline), baseline);
        const desired = directoryPayload(resource, "update", values, baseline);
        const current = directoryPayload(resource, "update", directoryFormValues(resource, "update", latest), latest);
        const changed = Object.keys(desired).filter((key) => !sameValue(prior[key], desired[key]));
        if (changed.some((key) => !sameValue(current[key], prior[key]) && !sameValue(current[key], desired[key]))) {
          throw new ApiError(409);
        }
        const fields = Object.fromEntries(changed.map((key) => [key, desired[key]]));
        if (matches(current, fields)) return {};
        const latestFields = Object.fromEntries(Object.keys(current).map((key) => [key, latest[key] ?? current[key]]));
        return {
          send: (signal) => api.update(resource, id, { ...latestFields, ...fields }, { signal }),
          expectation: { fields },
        };
      },
    });
  }

  function replayCreate(resource) {
    const key = scope(resource);
    const replay = uncertain.current.get(key)?.replay;
    if (!withinReplayWindow(replay)) {
      const result = feedback("unconfirmed", "directory.createReplayExpired");
      update(key, { feedback: result, canReplay: false });
      return Promise.resolve(result);
    }
    return perform({ resource, replaying: true,
      allow: (permissions) => canDirectory(resource, "create", permissions),
      prepare: () => createRequest(resource, replay) });
  }

  function command({ resource, id, action, record, data }) {
    const self = resource === "admins" && id === session.getSnapshot().actorId;
    return perform({
      resource, id, allow: (permissions) => canDirectoryAction(resource, action, permissions),
      ownPermissions: self && rolesActions.includes(action), signInAgain: self && action === "changePassword",
      prepare(latest) {
        if (rolesActions.includes(action)) {
          if (latest.enabled !== record.enabled || !sameValue(latest.roles, record.roles)) throw new ApiError(409);
          const granted = action === "grantRoles";
          const roles = data.roles.filter((id) => latest.roles.includes(id) !== granted);
          if (!roles.length) return {};
          return {
            send: (signal) => api.action(resource, id, action, { roles }, { signal }),
            expectation: { roles, granted },
          };
        }
        if (!matches(latest, snapshotFields(resource, record))) throw new ApiError(409);
        const fields = expectedCommand(action, data);
        return {
          send: (signal) => api.action(resource, id, action, data, { signal }),
          expectation: fields && { fields },
          responseFields: action === "changePassword" ? { login: latest.login } : null,
          passwordChange: action === "changePassword",
        };
      },
    });
  }

  function remove({ resource, id, record }) {
    const self = resource === "admins" && id === session.getSnapshot().actorId;
    return perform({
      resource, id, allow: (permissions) => canDirectory(resource, "remove", permissions) && !record.is_system_role,
      signInAgain: self,
      prepare(latest) {
        if (latest.is_system_role || !matches(latest, snapshotFields(resource, record))) throw new ApiError(409);
        return { removing: true, send: (signal) => api.remove(resource, id, { signal }) };
      },
    });
  }

  async function check(resource, id) {
    const key = scope(resource, id);
    const pending = uncertain.current.get(key);
    if (!pending || pending.passwordChange || !canDirectory(resource, "read", session.getSnapshot().permissions)) return null;
    const work = start(key);
    if (!work) return null;
    let result = feedback("unconfirmed", "directory.writeStillUnconfirmed");
    try {
      if (id === undefined) {
        await api.list(resource, { signal: work.signal });
      } else {
        const record = await api.get(resource, id, { signal: work.signal });
        if (observed(record, pending.expectation)) {
          result = feedback("success", "directory.writeObserved", { record });
        } else if (pending.expectation?.roles) {
          const { roles, granted } = pending.expectation;
          const applied = roles.filter((id) => record.roles.includes(id) === granted);
          const remaining = roles.filter((id) => !applied.includes(id));
          result = { status: "unconfirmed", record, message: t(applied.length ? "directory.rolesPartial" : "directory.rolesPending",
            { applied: applied.join(", "), remaining: remaining.join(", ") }) };
        }
      }
    } catch (error) {
      if (pending.removing && error?.status === 404 && canDirectory(resource, "read", session.getSnapshot().permissions)) {
        result = feedback("success", "directory.recordMissing", { removed: true });
      } else {
        result = { status: "unconfirmed", message: errorText(error) };
      }
    } finally {
      finish(key, work.controller);
    }
    if (work.signal.aborted) return null;
    if (result.record && pending.ownPermissions) {
      await session.recheckPermissions();
    }
    if (work.signal.aborted) return null;
    if (result.status === "success") uncertain.current.delete(key);
    const { record, ...message } = result;
    update(key, { feedback: message });
    return result;
  }

  return {
    state: (resource, id) => entries[scope(resource, id)] ?? idle,
    save, command, remove, check, replayCreate,
    clearConflict(resource, id) { update(scope(resource, id), { feedback: null }); },
    stopPasswordCheck(resource, id) {
      const key = scope(resource, id);
      if (!uncertain.current.get(key)?.passwordChange || running.current.has(key)) return;
      uncertain.current.delete(key);
      update(key, { passwordPending: false, feedback: feedback("notice", "directory.passwordCheckStopped") });
    },
  };
}
