import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { ApiError } from "../../api/transport.js";
import { changeNewField, emptyTicket, isUnknownWrite, operationKey, withinReplayWindow } from "./workspaceState.js";

const initialState = Object.freeze({ values: emptyTicket, busy: false, error: null, uncertain: false, intent: null, createdId: null });

export function useNewTicket(api, session, enabled, onCreated) {
  const [state, setState] = useState(initialState);
  const active = useRef(null);
  const allowed = useRef(enabled);
  useLayoutEffect(() => {
    allowed.current = enabled;
    if (!enabled) {
      active.current?.abort();
      active.current = null;
      setState((previous) => previous.busy ? { ...previous, busy: false, uncertain: true } : previous);
    }
  }, [enabled]);
  useEffect(() => () => { active.current?.abort(); }, []);

  function change(field, value) {
    setState((previous) => previous.busy || previous.uncertain ? previous : {
      ...previous, values: changeNewField(previous.values, field, value), error: null,
    });
  }

  function reset() {
    if (!active.current) setState(initialState);
  }

  async function submit() {
    if (active.current || !allowed.current) return;
    const payload = {
      ...state.values, text_of_ticket: state.values.text_of_ticket.trim(),
      description: state.values.description.trim(), comment: state.values.comment.trim(),
    };
    const fingerprint = JSON.stringify(payload);
    if (state.uncertain && state.intent?.fingerprint !== fingerprint) return;
    const reuse = state.intent?.fingerprint === fingerprint && withinReplayWindow(state.intent);
    if (state.uncertain && !reuse) {
      setState((previous) => ({ ...previous, error: new ApiError(0, "replay-expired") }));
      return;
    }
    const intent = reuse ? state.intent : { key: operationKey(), fingerprint, startedAt: Date.now() };
    const controller = new AbortController();
    active.current = controller;
    setState((previous) => ({ ...previous, busy: true, error: null, intent }));
    try {
      const ticket = await api.create(payload, { idempotencyKey: intent.key, signal: controller.signal });
      if (controller.signal.aborted || !allowed.current) return;
      setState({ ...initialState, createdId: ticket.ticket_id });
      onCreated();
    } catch (error) {
      if (controller.signal.aborted || !allowed.current) return;
      setState((previous) => ({
        ...previous, busy: false, error, uncertain: previous.uncertain || isUnknownWrite(error),
      }));
      if (error?.status === 401 || error?.status === 403) void session.reloadPermissions().catch(() => {});
    } finally {
      if (active.current === controller) active.current = null;
    }
  }

  return { state, change, reset, submit };
}
