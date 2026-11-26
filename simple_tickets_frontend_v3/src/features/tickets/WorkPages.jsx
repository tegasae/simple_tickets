import { useCallback, useLayoutEffect, useRef } from "react";
import { ApiError } from "../../api/transport.js";
import { ErrorPanel, RouteLink, StatePanel } from "../../app/layout.jsx";
import { ticketPath } from "../../app/routes.js";
import { useRemoteData } from "../../app/useRemoteData.js";
import { t } from "../../shared/i18n/messages.js";
import TicketFields from "./TicketFields.jsx";
import { fieldErrors, writeError } from "./writeMessages.js";
import { isDirty } from "./workspaceState.js";

export function WorkTabs({ ids, activeId, record, navigate, requestClose }) {
  if (!ids.length) return null;
  return (
    <nav aria-label={t("work.openTickets")} className="work-tabs">
      <ul>
        {ids.map((id) => {
          const item = record(id);
          const label = t("work.tabLabel", { id, title: item.title });
          return (
            <li key={id} className="work-tab">
              <RouteLink href={ticketPath(id)} navigate={navigate}
                id={`work-tab-${id}`} className="work-tab-link" aria-current={activeId === id ? "page" : undefined}>
                <span title={label}>{label}</span>
                {isDirty(item) && <span className="dirty-dot" aria-label={t("work.dirty")} role="img" />}
              </RouteLink>
              <button type="button" className="work-tab-close" aria-label={t("work.closeTab", { id })}
                aria-disabled={item.busy} onClick={() => requestClose(id)}>×</button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export function CloseDraftDialog({ id, busy, canSave, pendingWorkflow, onSaveClose, onDiscard, onContinue }) {
  const dialog = useRef(null);
  const title = useRef(null);
  const continueButton = useRef(null);
  useLayoutEffect(() => {
    const element = dialog.current;
    element.showModal();
    continueButton.current?.focus();
    return () => { if (element.open) element.close(); };
  }, []);
  useLayoutEffect(() => {
    if (busy) title.current?.focus();
  }, [busy]);
  function keepFocus(event) {
    if (event.key !== "Tab") return;
    const controls = [...dialog.current.querySelectorAll("button:not(:disabled)")];
    const first = controls[0];
    const last = controls.at(-1);
    const active = document.activeElement;
    if (!first) {
      event.preventDefault();
      title.current?.focus();
    } else if (!controls.includes(active) || active === (event.shiftKey ? first : last)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus();
    }
  }
  return (
    <dialog ref={dialog} className="draft-dialog" aria-labelledby="close-draft-heading"
      aria-describedby="close-draft-summary" onKeyDown={keepFocus}
      onCancel={(event) => { event.preventDefault(); if (!busy) onContinue(); }}>
      <h2 id="close-draft-heading" tabIndex={-1} ref={title}>
        {t(pendingWorkflow ? "workflow.closeTitle" : "work.closeTitle", { id })}
      </h2>
      <p id="close-draft-summary">{t(pendingWorkflow ? "workflow.closeDescription" : "work.closeDescription")}</p>
      <div className="work-actions">
        {canSave && <button type="button" className="btn btn-primary" disabled={busy} onClick={onSaveClose}>{t("work.saveClose")}</button>}
        <button ref={continueButton} type="button" className="btn" disabled={busy} onClick={onContinue}>{t("work.continue")}</button>
        <button type="button" className="btn" disabled={busy} onClick={onDiscard}>{t("work.discard")}</button>
      </div>
    </dialog>
  );
}

export function NewTicketPage({ creation, permissions, referencesApi, canView, openTicket }) {
  const { state } = creation;
  const heading = useRef(null);
  useLayoutEffect(() => {
    if (!state.createdId) heading.current?.focus();
  }, [state.createdId]);
  if (state.createdId) {
    return (
      <section className="panel">
        <StatePanel title={t("work.created", { id: state.createdId })} page>
          {canView && (
            <RouteLink href={ticketPath(state.createdId)} onFollow={() => openTicket(state.createdId, false)}>
              {t("work.openCreated", { id: state.createdId })}
            </RouteLink>
          )}
          <button type="button" className="btn" onClick={creation.reset}>{t("work.another")}</button>
        </StatePanel>
      </section>
    );
  }

  return (
    <section aria-labelledby="create-ticket-heading">
      <header className="page-head"><h1 ref={heading} tabIndex={-1} id="create-ticket-heading">{t("work.newTicket")}</h1></header>
      <div className="panel detail-panel">
        <TicketFields mode="create" values={state.values} onChange={creation.change} onSubmit={creation.submit}
          busy={state.busy} locked={state.uncertain}
          hideSubmit={state.error?.code === "replay-expired"}
          submitLabel={state.uncertain ? t("work.repeatIntent") : undefined}
          error={state.error ? writeError(state.error, { idempotent: state.uncertain }) : ""}
          fieldErrors={fieldErrors(state.error)} permissions={permissions} referencesApi={referencesApi} />
      </div>
    </section>
  );
}

function Detail({ label, value }) {
  return <div><dt>{t(label)}</dt><dd>{value || t("common.missing")}</dd></div>;
}

export function RelatedPage({ ticket, route, referencesApi, permissions, onBack }) {
  const { id, type, relatedId } = route;
  const isClient = type === "client";
  const relation = isClient ? "client" : ticket.user_id === relatedId ? "requester" : "contact";
  const sameRelation = isClient ? ticket.client_id === relatedId : [ticket.user_id, ticket.contact_user_id].includes(relatedId);
  const allowed = permissions.includes(isClient ? "client.view" : "user.view");
  const load = useCallback((signal) => {
    if (!sameRelation) return Promise.reject(new ApiError(404));
    if (!allowed) return Promise.reject(new ApiError(403));
    return isClient ? referencesApi.client(relatedId, { signal }) : referencesApi.user(relatedId, { signal });
  }, [allowed, sameRelation, isClient, referencesApi, relatedId]);
  const result = useRemoteData(`${type}:${relatedId}:${allowed}:${sameRelation}`, load);
  const heading = useRef(null);
  useLayoutEffect(() => {
    const active = document.activeElement;
    if (result.phase === "ready" && (active === document.body || active?.id === "workspace")) heading.current?.focus();
  }, [result.phase]);

  const back = <RouteLink href={ticketPath(id)} onFollow={onBack} className="back-link">{t("relation.back", { id })}</RouteLink>;
  if (result.phase === "loading") return <>{back}<StatePanel title={t("common.loading")} loading /></>;
  if (result.phase === "error") {
    const status = result.error?.status;
    if (status === 403 || status === 404) {
      return (
        <StatePanel title={t(status === 403 ? "error.forbidden" : "error.notFound")}
          description={t(status === 403 ? "relation.noPermission" : "relation.notFound")} error page>
          {back}
        </StatePanel>
      );
    }
    return <ErrorPanel error={result.error} retry={result.reload} back={back} />;
  }

  const entity = result.data;
  const name = isClient ? entity.name : [entity.first_name, entity.last_name].filter(Boolean).join(" ");
  return (
    <article>
      {back}
      <header className="page-head">
        <p className="ticket-number">{t(`relation.${relation}`, { id: relatedId })}</p>
        <h1 ref={heading} tabIndex={-1}>{name || t("common.missing")}</h1>
      </header>
      <section className="panel detail-panel" aria-label={t("ticket.references")}>
        <dl className="metadata">
          <Detail label="ticket.status" value={t(entity.enabled ? "relation.active" : "relation.inactive")} />
          <Detail label="relation.email" value={entity.email} />
          <Detail label="relation.phone" value={entity.phone} />
          {isClient && <Detail label="relation.address" value={entity.address} />}
          {!isClient && <Detail label="ticket.client" value={entity.client_id} />}
        </dl>
        {isClient && entity.description && <p className="description">{entity.description}</p>}
      </section>
    </article>
  );
}
