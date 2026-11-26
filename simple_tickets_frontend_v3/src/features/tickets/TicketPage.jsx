import { useEffect, useLayoutEffect, useRef } from "react";
import { ErrorPanel, RouteLink, StatePanel } from "../../app/layout.jsx";
import { relatedPath } from "../../app/routes.js";
import { t } from "../../shared/i18n/messages.js";
import { formatDateTime, normalizeTicket, statusLabel, urgencyLabel } from "./model.js";
import { editableFields } from "./editing.js";
import TicketFields from "./TicketFields.jsx";
import TicketCommentForm from "./TicketCommentForm.jsx";
import { allowedFields, canPostComment, fieldLabels } from "./workspaceState.js";
import { fieldErrors, writeError } from "./writeMessages.js";
import WorkflowPanel from "./workflow/WorkflowPanel.jsx";

function Reference({ label, value }) {
  return <div><dt>{t(label)}</dt><dd>{value || t("common.missing")}</dd></div>;
}

function Timeline({ items, history }) {
  if (!items.length) return <p className="muted">{t(history ? "ticket.noHistory" : "ticket.noComments")}</p>;
  return (
    <ol className="timeline">
      {items.map((item, index) => (
        <li key={item.id ?? index}>
          <div>
            <strong>{history ? statusLabel(item.status) : t("ticket.author", { id: item.actor_id || t("common.missing") })}</strong>
            <span>{formatDateTime(item.date_created)}</span>
          </div>
          {item.comment && <p>{item.comment}</p>}
        </li>
      ))}
    </ol>
  );
}

function LinkedReference({ ticketId, name, type, value, allowed, onRelation }) {
  const linkId = `relation-${name}`;
  if (!value || !allowed) return <Reference label={`ticket.${name}`} value={value} />;
  const href = relatedPath(ticketId, type, value);
  return <div><dt>{t(`ticket.${name}`)}</dt><dd>
    <RouteLink href={href} onFollow={() => onRelation(href, linkId)} id={linkId}>
      {t(`relation.${name}`, { id: value })}
    </RouteLink>
  </dd></div>;
}

function prettyValue(field, value) {
  if (field === "planned_at") return formatDateTime(value);
  if (field === "urgency") return urgencyLabel(value);
  if (typeof value === "boolean") return t(value ? "work.yes" : "work.no");
  return value || t("common.missing");
}

function EditStatus({ id, record, work }) {
  const outcome = record.outcome;
  const status = outcome?.status;
  const conflicts = outcome?.conflicts ?? [];
  const hasConflict = status === "conflict" || conflicts.length > 0;
  const unknown = status === "unconfirmed";
  if (!hasConflict && !unknown && status !== "partial") return null;
  const current = outcome.ticket ? editableFields(outcome.ticket) : {};
  const names = (fields) => fields.map((field) => t(fieldLabels[field])).join(", ");
  return (
    <div className="edit-result" role="status">
      {status === "partial" && <p>{t("work.partial")}</p>}
      {outcome.applied?.length > 0 && <p>{t("work.fieldsApplied", { fields: names(outcome.applied) })}</p>}
      {outcome.remaining?.length > 0 && <p>{t("work.fieldsRemaining", { fields: names(outcome.remaining) })}</p>}
      {unknown && <>
        <p>{t("work.unconfirmed")}</p>
        {record.editError && <p>{writeError(record.editError)}</p>}
        <button type="button" className="btn" disabled={record.busy} onClick={() => work.check(id)}>{t("work.check")}</button>
      </>}
      {!unknown && hasConflict && <>
        <p>{t("work.conflicts")}</p>
        <ul className="conflict-values">
          {conflicts.map((field) => <li key={field}>
            <strong>{t(fieldLabels[field])}</strong>
            <span>{t("work.serverValue", { value: prettyValue(field, current[field]) })}</span>
            <span>{t("work.draftValue", { value: prettyValue(field, record.changes[field]) })}</span>
          </li>)}
        </ul>
        {outcome.ticket && <button type="button" className="btn" disabled={record.busy}
          onClick={() => work.adoptLatest(id)}>{t("work.adoptBaseline")}</button>}
      </>}
    </div>
  );
}

export default function TicketPage({
  id, result, backHref, onBack, record, work, permissions, referencesApi, workflowApi, actorId, onRelation,
  focusLink, onFocusRestored, onDeleted,
}) {
  const history = record.history;
  const heading = useRef(null);
  const editPanel = useRef(null);
  const moveEditFocus = useRef(false);
  useLayoutEffect(() => {
    if (!focusLink || result.phase !== "ready") return;
    (document.getElementById(focusLink) ?? heading.current)?.focus();
    onFocusRestored();
  }, [focusLink, result.phase, onFocusRestored]);
  useLayoutEffect(() => {
    if (!moveEditFocus.current || !record.editing || !editPanel.current) return;
    moveEditFocus.current = false;
    editPanel.current.focus();
  }, [record.editing, result.phase]);
  useEffect(() => {
    const active = document.activeElement;
    if (result.phase === "ready" && (active?.id === "workspace" || active === document.body)) {
      heading.current?.focus({ preventScroll: true });
    }
  }, [result.phase]);
  const back = <RouteLink href={backHref} onFollow={onBack} className="back-link">{t("ticket.back")}</RouteLink>;
  async function checkWorkflow() {
    if (await work.reloadWorkflow(id)) onDeleted(id);
  }

  if (result.phase === "loading") {
    return <>{back}<StatePanel title={t("common.loading")} loading /></>;
  }
  if (result.phase === "error") {
    if (result.error?.status === 404 && record.workflowPending?.action === "deleteTicket") {
      return <>{back}<StatePanel title={t("workflow.deleteCheck")} page>
        <button type="button" className="btn" disabled={record.busy} onClick={checkWorkflow}>{t("workflow.reload")}</button>
      </StatePanel></>;
    }
    return <ErrorPanel error={result.error} retry={result.reload} back={back} />;
  }

  const ticket = normalizeTicket(result.data);
  const canEdit = allowedFields(ticket.status, permissions).length > 0;
  const canComment = canPostComment(ticket.status, permissions, ticket.is_closed);
  const canResolveComment = record.commentUncertain && permissions.includes("ticket.operation");
  const editsBlocked = record.outcome?.status === "unconfirmed" || record.outcome?.status === "conflict"
    || record.outcome?.conflicts?.length > 0;
  return (
    <article className="ticket-detail">
      {back}
      <header className="page-head">
        <p className="ticket-number">{t("common.identifier", { id })}</p>
        <h1 ref={heading} tabIndex={-1}>{ticket.text_of_ticket || t("common.missing")}</h1>
        <span className="badge" data-status={ticket.status}>{statusLabel(ticket.status)}</span>
        {canEdit && !record.editing && <button type="button" className="btn ticket-edit-button"
          onClick={() => { moveEditFocus.current = true; work.beginEdit(id, ticket); }}>{t("work.edit")}</button>}
        {record.confirmed && <p role="status">{t("work.confirmed")}</p>}
      </header>
      <div className="detail-grid">
        <section className="panel detail-panel" aria-labelledby="description-heading">
          <h2 id="description-heading">{t("ticket.description")}</h2>
          <p className="description">{ticket.description || t("common.missing")}</p>
          {ticket.remote_work_recommended && <p className="notice">{t("ticket.remoteRecommended")}</p>}
        </section>
        <section className="panel detail-panel" aria-labelledby="references-heading">
          <h2 id="references-heading">{t("ticket.references")}</h2>
          <dl className="metadata">
            <Reference label="ticket.createdAt" value={formatDateTime(ticket.createdAt)} />
            <Reference label="ticket.planned" value={formatDateTime(ticket.planned_at)} />
            <Reference label="ticket.department" value={ticket.department_id} />
            <Reference label="ticket.executor" value={ticket.current_executor_id} />
            <Reference label="ticket.urgency" value={urgencyLabel(ticket.urgency)} />
            <LinkedReference ticketId={id} name="client" type="client" value={ticket.client_id}
              allowed={permissions.includes("client.view")} onRelation={onRelation} />
            <LinkedReference ticketId={id} name="requester" type="user" value={ticket.user_id}
              allowed={permissions.includes("user.view")} onRelation={onRelation} />
            <LinkedReference ticketId={id} name="contact" type="user" value={ticket.contact_user_id}
              allowed={permissions.includes("user.view")} onRelation={onRelation} />
          </dl>
        </section>
      </div>
      <WorkflowPanel ticket={ticket} permissions={permissions} actorId={actorId} api={workflowApi}
        busy={record.busy} form={record.workflowForm} feedback={record.workflowFeedback}
        onRun={async (action, payload) => {
          if (await work.runWorkflow(ticket, action, payload)) onDeleted(id);
        }}
        onReload={checkWorkflow} onFormChange={(form) => work.setWorkflowForm(id, form)} />
      {record.editing && (
        <section ref={editPanel} className="panel detail-panel ticket-edit-panel" tabIndex={-1} aria-labelledby="ticket-edit-heading">
          <h2 id="ticket-edit-heading">{t("ticketForm.edit")}</h2>
          <EditStatus id={id} record={record} work={work} />
          {canEdit && (
            <TicketFields mode="edit" values={{ ...ticket, ...record.baseline, ...record.changes }}
              onChange={(field, value) => work.change(id, field, value)}
              onSubmit={() => work.save(id)} referencesApi={referencesApi} permissions={permissions}
              busy={record.busy} locked={editsBlocked} hideSubmit={editsBlocked}
              error={record.editError && !editsBlocked ? writeError(record.editError) : ""}
              fieldErrors={fieldErrors(record.editError)} />
          )}
          {!canEdit && <p role="alert">{t("work.writeForbidden")}</p>}
        </section>
      )}
      <section className="panel detail-panel">
        <div className="history-controls">
          <button className="btn" type="button" aria-pressed={!history} onClick={() => work.update(id, { history: false })}>
            {t("ticket.comments")}
          </button>
          <button className="btn" type="button" aria-pressed={history} onClick={() => work.update(id, { history: true })}>
            {t("ticket.history")}
          </button>
        </div>
        <h2>{t(history ? "ticket.history" : "ticket.comments")}</h2>
        <Timeline history={history} items={history ? ticket.statuses : ticket.comments} />
        {!history && record.commentSent && <p role="status">{t("work.commentSent")}</p>}
        {!history && (canComment || canResolveComment) && <TicketCommentForm value={record.comment} onChange={(text) => work.setComment(id, text)}
          onSubmit={(text) => work.addComment(id, text)} busy={record.busy} locked={record.commentUncertain}
          disabled={record.commentError?.code === "replay-expired"}
          submitLabel={record.commentUncertain ? t("work.repeatIntent") : undefined}
          error={record.commentError ? writeError(record.commentError, { idempotent: record.commentUncertain }) : ""} />}
      </section>
    </article>
  );
}
