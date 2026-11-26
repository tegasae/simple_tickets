import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { createReferencesApi } from "../api/resources/references.js";
import { createTicketsApi } from "../api/resources/tickets.js";
import { createWorkflowApi } from "../api/resources/workflow.js";
import QueuePage from "../features/tickets/QueuePage.jsx";
import TicketPage from "../features/tickets/TicketPage.jsx";
import { CloseDraftDialog, NewTicketPage, RelatedPage, WorkTabs } from "../features/tickets/WorkPages.jsx";
import { useNewTicket } from "../features/tickets/useNewTicket.js";
import { useTicketWork } from "../features/tickets/useTicketWork.js";
import { availableActions } from "../features/tickets/workflow/policy.js";
import { allowedFields, canCreateTicket, canPostComment, hasEdits, hasNewDraft, hasWorkflowInput, isDirty } from "../features/tickets/workspaceState.js";
import { errorText, t } from "../shared/i18n/messages.js";
import { ErrorPanel, RouteLink, Shell, StatePanel } from "./layout.jsx";
import LoginPage from "./LoginPage.jsx";
import { queuePath, readRoute, ticketPath } from "./routes.js";
import { useRemoteData } from "./useRemoteData.js";

function currentRoute() {
  return readRoute(window.location.pathname, window.location.search);
}

const initialCriteria = { draft: "", search: "", status: "", urgency: "", filtersOpen: false };

function QueueResource({ api, route, permissions, actorId, ...props }) {
  const hotline = route.queue === "hotline";
  const sourceQueue = hotline ? "open" : route.queue;
  const load = useCallback((signal) => api.list({ queue: sourceQueue, signal }), [api, sourceQueue]);
  const result = useRemoteData(route.queue, load);
  const data = useMemo(() => hotline && result.data
    ? result.data.filter((ticket) => availableActions(ticket, { permissions, actorId }).includes("startRemoteWork"))
    : result.data, [hotline, result.data, permissions, actorId]);
  return <QueuePage route={route} result={{ ...result, data }} {...props} />;
}

function TicketResource({ api, route, work, record, onBackRelated, ...props }) {
  const { id } = route;
  const load = useCallback((signal) => api.get(id, { signal }), [api, id]);
  const result = useRemoteData(`${id}:${record.revision}`, load);
  const remember = work.remember;
  useEffect(() => {
    if (result.phase === "ready") remember(id, result.data);
  }, [id, result.phase, result.data, remember]);

  if (route.page === "related") {
    if (result.phase === "ready") {
      return <RelatedPage ticket={result.data} route={route} referencesApi={props.referencesApi}
        permissions={props.permissions} onBack={onBackRelated} />;
    }
    const back = <RouteLink href={ticketPath(id)} onFollow={onBackRelated} className="back-link">
      {t("relation.back", { id })}
    </RouteLink>;
    if (result.phase === "error") return <ErrorPanel error={result.error} retry={result.reload} back={back} />;
    return <>{back}<StatePanel title={t("common.loading")} loading /></>;
  }
  return <TicketPage id={id} result={result} work={work} record={record} {...props} />;
}

function Workspace({ session, snapshot, route, navigate }) {
  const api = useMemo(() => createTicketsApi(session), [session]);
  const referencesApi = useMemo(() => createReferencesApi(session), [session]);
  const workflowApi = useMemo(() => createWorkflowApi(session), [session]);
  const [criteria, setCriteria] = useState(initialCriteria);
  const [returnFocus, setReturnFocus] = useState(null);
  const [queueRevision, setQueueRevision] = useState(0);
  const queueLocation = useRef(null);
  const relationOrigin = useRef(null);
  const previousRoute = useRef(null);
  const activeWorkspace = useRef(true);
  const viewAvailable = useRef(false);
  const [relationFocus, setRelationFocus] = useState(null);
  const [closingId, setClosingId] = useState(null);
  const { permissions, actorId } = snapshot;
  const canView = permissions.includes("ticket.view");
  const canHotline = permissions.includes("ticket.at_work_remote");
  const canCreate = canCreateTicket(permissions);
  const onChanged = useCallback(() => setQueueRevision((value) => value + 1), []);
  const work = useTicketWork(api, session, canView, permissions, onChanged, { workflowApi, actorId });
  const creation = useNewTicket(api, session, canCreate, onChanged);
  if (route.page === "queue" && (route.queue !== "hotline" || canHotline)) queueLocation.current = queuePath(route);
  const queueHref = queueLocation.current ?? queuePath();

  const ticket = route.page === "ticket" || route.page === "related" ? route.id : null;
  const [refreshingPermissions, setRefreshingPermissions] = useState(false);
  const openWork = work.open;
  useLayoutEffect(() => {
    viewAvailable.current = canView;
    if (canView && ticket) openWork(ticket);
    if (!canView) setClosingId(null);
  }, [canView, ticket, openWork]);
  useLayoutEffect(() => {
    activeWorkspace.current = true;
    return () => { activeWorkspace.current = false; };
  }, []);

  useEffect(() => {
    if (route.page === "login") navigate(canCreate && !canView ? "/tickets/new" : queuePath(), { replace: true });
    else if (route.page === "queue" && !canView && canCreate && window.location.pathname === "/") {
      navigate("/tickets/new", { replace: true });
    }
  }, [route, navigate, canCreate, canView]);

  useEffect(() => {
    const key = route.page === "newTicket" ? "work.newTicket" : ticket ? "ticket.title" : "queue.title";
    document.title = `${t(key)} · ${t("app.name")}`;
  }, [route.page, ticket]);

  useLayoutEffect(() => {
    const previous = previousRoute.current;
    const returned = previous?.page === "related" && route.page === "ticket" && previous.id === ticket;
    if (returned && relationOrigin.current?.id === ticket) setRelationFocus(relationOrigin.current.linkId);
    else setRelationFocus(null);
    if (ticket && canView && !returned) {
      window.scrollTo(0, 0);
      document.getElementById("workspace")?.focus({ preventScroll: true });
    }
    previousRoute.current = route;
  }, [route, ticket, canView]);

  const hasDrafts = Object.values(work.records).some(isDirty) || hasNewDraft(creation.state.values);
  useEffect(() => {
    if (!hasDrafts) return;
    const prevent = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", prevent);
    return () => window.removeEventListener("beforeunload", prevent);
  }, [hasDrafts]);

  function updateRoute(patch, options) {
    navigate(queuePath({ ...route, ...patch }), options);
  }

  function openTicket(id, fromQueue = true) {
    openWork(id);
    if (fromQueue) setReturnFocus({ id, scroll: window.scrollY });
    navigate(ticketPath(id), fromQueue ? { state: { i1TicketFromQueue: true } } : undefined);
  }

  function goBack() {
    if (window.history.state?.i1TicketFromQueue) window.history.back();
    else {
      setReturnFocus({ id: null, scroll: 0 });
      navigate(queueHref);
    }
  }

  function openRelation(href, linkId) {
    relationOrigin.current = { id: ticket, linkId };
    navigate(href, { state: { i2RelatedFromTicket: ticket } });
  }

  function goBackRelated() {
    if (window.history.state?.i2RelatedFromTicket === ticket) window.history.back();
    else navigate(ticketPath(ticket));
  }

  function closeTab(id) {
    if (!work.close(id)) return;
    setClosingId(null);
    const index = work.openIds.indexOf(id);
    const next = work.openIds[index + 1] ?? work.openIds[index - 1];
    if (ticket === id) {
      navigate(next ? ticketPath(next) : queueHref, { replace: true });
      if (!next) setReturnFocus({ id: null, scroll: 0 });
    } else {
      requestAnimationFrame(() => (document.getElementById(`work-tab-${next}`) ?? document.getElementById("workspace"))?.focus());
    }
  }

  function requestClose(id) {
    const record = work.record(id);
    if (record.busy) return;
    if (isDirty(record)) setClosingId(id);
    else closeTab(id);
  }

  const closingRecord = closingId && work.record(closingId);
  const closingHasEdits = hasEdits(closingRecord);
  const closingComment = closingRecord?.comment.trim();
  const canSaveClosing = Boolean(closingRecord && (closingHasEdits || closingComment)
    && !hasWorkflowInput(closingRecord.workflowForm)
    && !closingRecord.workflowPending
    && (!closingHasEdits || Object.keys(closingRecord.changes).every((field) => allowedFields(closingRecord.status, permissions).includes(field)))
    && closingRecord.outcome?.status !== "unconfirmed" && closingRecord.outcome?.status !== "conflict"
    && !closingRecord.outcome?.conflicts?.length
    && (!closingComment || canPostComment(closingRecord.status, permissions, closingRecord.closed)));

  async function saveAndClose() {
    const id = closingId;
    if (!canSaveClosing || !id || closingRecord.busy) return;
    const saved = (!closingHasEdits || await work.save(id))
      && (!closingComment || await work.addComment(id, closingComment));
    if (!activeWorkspace.current || !viewAvailable.current) return;
    if (saved) closeTab(id);
    else {
      setClosingId(null);
      navigate(ticketPath(id));
    }
  }

  const onFocusRestored = useCallback(() => setReturnFocus(null), []);
  const linkFocusRestored = useCallback(() => setRelationFocus(null), []);
  let content;

  async function retryPermissions() {
    if (refreshingPermissions) return;
    setRefreshingPermissions(true);
    try {
      await session.reloadPermissions();
    } finally {
      setRefreshingPermissions(false);
    }
  }

  if (route.page === "newTicket" && canCreate) {
    content = <NewTicketPage creation={creation} permissions={permissions} referencesApi={referencesApi}
      canView={canView} openTicket={openTicket} />;
  } else if (route.page === "newTicket") {
    content = <StatePanel title={t("error.forbidden")} description={t("work.writeForbidden")} error page>
      {canView && <RouteLink href={queueHref} navigate={navigate}>{t("ticket.back")}</RouteLink>}
    </StatePanel>;
  } else if (!canView) {
    const failedRecheck = snapshot.error && snapshot.error.status !== 403;
    content = <StatePanel title={t("error.forbidden")}
      description={failedRecheck ? errorText(snapshot.error) : t("error.noTicketsPermission")} error page>
      <button type="button" className="btn" onClick={retryPermissions} aria-disabled={refreshingPermissions} aria-busy={refreshingPermissions}>
        {t(refreshingPermissions ? "common.loading" : "common.retry")}
      </button>
    </StatePanel>;
  } else if (ticket) {
    content = <TicketResource key={ticket} api={api} route={route} work={work} record={work.record(ticket)}
      referencesApi={referencesApi} workflowApi={workflowApi} permissions={permissions} actorId={actorId}
      backHref={queueHref} onBack={goBack}
      onBackRelated={goBackRelated} onRelation={openRelation} focusLink={relationFocus}
      onFocusRestored={linkFocusRestored} />;
  } else if (route.page === "queue" && route.queue === "hotline" && !canHotline) {
    content = <StatePanel title={t("error.forbidden")} description={t("queue.hotlineForbidden")} error page>
      <RouteLink href={queuePath()} navigate={navigate}>{t("ticket.back")}</RouteLink>
    </StatePanel>;
  } else if (route.page === "queue" || route.page === "login") {
    const activeRoute = route.page === "login" ? readRoute("/tickets") : route;
    content = <QueueResource key={`${activeRoute.queue}:${queueRevision}`} api={api} route={activeRoute} criteria={criteria} setCriteria={setCriteria}
      returnFocus={returnFocus} onFocusRestored={onFocusRestored} canHotline={canHotline} permissions={permissions} actorId={actorId}
      navigate={navigate} updateRoute={updateRoute} openTicket={openTicket} />;
  } else {
    content = <StatePanel title={t("error.notFound")} page>
      <RouteLink href={queueHref} navigate={navigate}>{t("ticket.back")}</RouteLink>
    </StatePanel>;
  }

  return <Shell canView={canView} canCreate={canCreate} queueHref={queueHref} navigate={navigate}
    storageAvailable={snapshot.storageAvailable} onLogout={() => session.logout()}>
    {canView && <WorkTabs ids={work.openIds} activeId={ticket} record={work.record} navigate={navigate} requestClose={requestClose} />}
    {content}
    {canView && closingId && <CloseDraftDialog id={closingId} busy={closingRecord.busy} canSave={canSaveClosing}
      pendingWorkflow={Boolean(closingRecord.workflowPending)}
      onSaveClose={saveAndClose} onDiscard={() => closeTab(closingId)} onContinue={() => setClosingId(null)} />}
  </Shell>;
}

export default function App({ session }) {
  const snapshot = useSyncExternalStore(session.subscribe, session.getSnapshot);
  const [booting, setBooting] = useState(true);
  const [route, setRoute] = useState(currentRoute);

  useEffect(() => {
    let active = true;
    session.restore().finally(() => { if (active) setBooting(false); });
    return () => { active = false; };
  }, [session]);

  useEffect(() => {
    const onPop = () => setRoute(currentRoute());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((href, { replace = false, state = null } = {}) => {
    if (href === window.location.pathname + window.location.search && !state) return;
    if (replace) window.history.replaceState(state, "", href);
    else window.history.pushState(state, "", href);
    setRoute(currentRoute());
  }, []);

  if (booting || snapshot.phase === "restoring") {
    return <main className="login-page"><StatePanel title={t("session.restoring")} loading /></main>;
  }
  if (snapshot.phase === "error") {
    return (
      <main className="login-page">
        <StatePanel title={t("error.title")} description={errorText(snapshot.error)} error page>
          <button type="button" className="btn btn-primary" onClick={() => session.restore()}>{t("common.retry")}</button>
          <button type="button" className="btn" onClick={() => session.logout()}>{t("session.logout")}</button>
        </StatePanel>
      </main>
    );
  }
  if (snapshot.phase !== "authenticated") return <LoginPage snapshot={snapshot} session={session} />;
  return <Workspace key={snapshot.actorId ?? "admin"} session={session} snapshot={snapshot} route={route} navigate={navigate} />;
}
