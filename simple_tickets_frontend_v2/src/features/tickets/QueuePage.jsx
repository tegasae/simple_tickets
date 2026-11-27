import { useLayoutEffect, useMemo, useRef } from "react";
import { ErrorPanel, RouteLink, StatePanel } from "../../app/layout.jsx";
import { queueOptions, queuePath, sizeOptions } from "../../app/routes.js";
import { getMessageRevision, t } from "../../shared/i18n/messages.js";
import { formatDateTime, formatNumber, normalizeTicket, paginate, selectTickets, statusLabel, urgencyLabel } from "./model.js";

function SortHeading({ column, route, updateRoute }) {
  const active = route.sort.startsWith(`${column}-`);
  const ascending = active && route.sort.endsWith("-asc");
  const next = active && !ascending ? "asc" : "desc";
  return (
    <th scope="col" aria-sort={active ? (ascending ? "ascending" : "descending") : undefined}>
      <button className="sort-button" type="button" onClick={() => updateRoute({ sort: `${column}-${next}`, number: 1 })}>
        {t(column === "id" ? "ticket.number" : "ticket.createdAt")}
        <span aria-hidden="true">{active ? (ascending ? "↑" : "↓") : "↕"}</span>
      </button>
    </th>
  );
}

export default function QueuePage({
  route, result, navigate, updateRoute, criteria, setCriteria, openTicket, returnFocus, onFocusRestored, canHotline,
}) {
  const rows = useMemo(() => (result.data ?? []).map(normalizeTicket), [result.data]);
  const messages = getMessageRevision();
  const { search, status, urgency } = criteria;
  const filtered = useMemo(() => selectTickets(rows, { search, status, urgency, sort: route.sort }),
    [rows, search, status, urgency, route.sort, messages]);
  const page = paginate(filtered, route.number, route.size);
  const hasRows = filtered.length > 0;
  const range = hasRows ? t("queue.range", {
    start: formatNumber(page.start + 1), end: formatNumber(page.start + page.rows.length), total: formatNumber(filtered.length),
  }) : t(rows.length ? "queue.empty.search" : "queue.empty.title");
  const table = useRef(null);
  const heading = useRef(null);
  const searchField = useRef(null);
  const filterSummary = useRef(null);
  const statuses = [...new Set(rows.map((row) => row.status).filter(Boolean))];
  const urgencies = [...new Set(rows.map((row) => row.urgency).filter(Boolean))];
  if (criteria.status && !statuses.includes(criteria.status)) statuses.push(criteria.status);
  if (criteria.urgency && !urgencies.includes(criteria.urgency)) urgencies.push(criteria.urgency);
  const activeCount = Number(Boolean(criteria.status)) + Number(Boolean(criteria.urgency));

  useLayoutEffect(() => {
    if (!returnFocus && document.activeElement === document.body) heading.current?.focus({ preventScroll: true });
  }, [returnFocus]);

  useLayoutEffect(() => {
    if (!returnFocus || result.phase === "loading") return;
    const target = returnFocus.id === null ? null : table.current?.querySelector(`#ticket-link-${returnFocus.id}`);
    if (target) {
      window.scrollTo(0, returnFocus.scroll);
      target.focus({ preventScroll: true });
    } else {
      heading.current?.focus();
    }
    onFocusRestored();
  }, [returnFocus, result.phase, onFocusRestored]);

  function apply(patch) {
    setCriteria((value) => ({ ...value, ...patch }));
    updateRoute({ number: 1 }, { replace: true });
  }

  function submit(event) {
    event.preventDefault();
    apply({ search: criteria.draft.trim() });
  }

  function reset() {
    apply({ draft: "", search: "", status: "", urgency: "" });
    searchField.current?.focus();
  }

  function clearFilter(key) {
    apply({ [key]: "" });
    filterSummary.current?.focus();
  }

  function reload() {
    heading.current?.focus({ preventScroll: true });
    result.reload();
  }

  return (
    <section aria-labelledby="queue-heading">
      <header className="page-head"><h1 ref={heading} id="queue-heading" tabIndex={-1}>{t("queue.title")}</h1></header>
      <nav className="queue-tabs" aria-label={t("queue.areas")}>
        {queueOptions.filter((queue) => queue !== "hotline" || canHotline).map((queue) => (
          <RouteLink key={queue} href={queuePath({ ...route, queue, number: 1 })} navigate={navigate}
            aria-current={route.queue === queue ? "page" : undefined} className="queue-tab">
            {t(`queue.${queue}`)}
          </RouteLink>
        ))}
      </nav>
      <div className="panel">
        <p className="visually-hidden" role="status" aria-atomic="true">{result.phase === "ready" ? range : ""}</p>
        <div className="queue-controls">
          <form className="search-form" onSubmit={submit}>
            <label htmlFor="queue-search">{t("queue.search")}</label>
            <div className="search-row">
              <input ref={searchField} id="queue-search" type="search" value={criteria.draft} placeholder={t("queue.placeholder")}
                onChange={(event) => setCriteria((value) => ({ ...value, draft: event.target.value }))} />
              <button className="btn btn-primary">{t("queue.find")}</button>
            </div>
          </form>
          <details className="filters" open={criteria.filtersOpen} onToggle={(event) => {
            const open = event.currentTarget.open;
            setCriteria((value) => value.filtersOpen === open ? value : { ...value, filtersOpen: open });
          }}>
            <summary ref={filterSummary}>{activeCount ? t("queue.filtersCount", { count: activeCount }) : t("queue.filters")}</summary>
            <div className="filter-fields">
              <div className="filter-field">
                <label htmlFor="filter-status">{t("ticket.status")}</label>
                <select id="filter-status" value={criteria.status} onChange={(event) => apply({ status: event.target.value })}>
                  <option value="">{t("queue.any")}</option>
                  {statuses.map((status) => <option key={status} value={status}>{statusLabel(status)}</option>)}
                </select>
              </div>
              <div className="filter-field">
                <label htmlFor="filter-urgency">{t("ticket.urgency")}</label>
                <select id="filter-urgency" value={criteria.urgency} onChange={(event) => apply({ urgency: event.target.value })}>
                  <option value="">{t("queue.any")}</option>
                  {urgencies.map((urgency) => <option key={urgency} value={urgency}>{urgencyLabel(urgency)}</option>)}
                </select>
              </div>
            </div>
          </details>
          {(criteria.search || activeCount > 0) && (
            <div className="active-filters">
              {criteria.search && <span className="search-value">{t("queue.activeSearch", { value: criteria.search })}</span>}
              {criteria.status && <button className="filter-chip" aria-label={t("queue.clearStatus")} type="button"
                onClick={() => clearFilter("status")}>{t("queue.activeStatus", { value: statusLabel(criteria.status) })} ×</button>}
              {criteria.urgency && <button className="filter-chip" aria-label={t("queue.clearUrgency")} type="button"
                onClick={() => clearFilter("urgency")}>{t("queue.activeUrgency", { value: urgencyLabel(criteria.urgency) })} ×</button>}
              <button type="button" className="btn btn-quiet" onClick={reset}>{t("common.reset")}</button>
            </div>
          )}
        </div>
        {result.phase === "loading" && <StatePanel title={t("common.loading")} loading />}
        {result.phase === "error" && <ErrorPanel error={result.error} retry={reload} />}
        {result.phase === "ready" && !hasRows && (
          rows.length === 0
            ? <StatePanel title={t("queue.empty.title")}>
                <button type="button" className="btn" onClick={reload}>{t("common.refresh")}</button>
              </StatePanel>
            : <StatePanel title={t("queue.empty.search")} description={t("queue.empty.hint")}>
                <button type="button" className="btn" onClick={reset}>{t("common.reset")}</button>
              </StatePanel>
        )}
        {result.phase === "ready" && hasRows && (
          <>
            <p className="table-hint" id="queue-scroll-hint">{t("queue.tableScroll")}</p>
            <div className="table-wrap" ref={table} tabIndex={0} role="region"
              aria-labelledby="queue-heading" aria-describedby="queue-scroll-hint">
              <table aria-labelledby="queue-heading">
                <thead>
                  <tr>
                    <SortHeading column="id" route={route} updateRoute={updateRoute} />
                    <th scope="col">{t("ticket.title")}</th>
                    <th scope="col">{t("ticket.status")}</th>
                    <SortHeading column="created" route={route} updateRoute={updateRoute} />
                    <th scope="col">{t("ticket.client")}</th>
                    <th scope="col">{t("ticket.executor")}</th>
                  </tr>
                </thead>
                <tbody>
                  {page.rows.map((row) => (
                    <tr key={row.ticket_id}>
                      <td>
                        <RouteLink href={`/tickets/${row.ticket_id}`} id={`ticket-link-${row.ticket_id}`}
                          className="ticket-link" onFollow={() => openTicket(row.ticket_id)}>
                          {t("common.identifier", { id: row.ticket_id })}
                        </RouteLink>
                      </td>
                      <td className="ticket-title-cell">{row.text_of_ticket || t("common.missing")}
                        {row.remote_work_recommended && <div className="muted">{t("ticket.remoteRecommended")}</div>}
                      </td>
                      <td><span className="badge" data-status={row.status}>{statusLabel(row.status)}</span></td>
                      <td className="time-cell">{formatDateTime(row.createdAt)}</td>
                      <td>{row.client_id || t("common.missing")}</td>
                      <td>{row.current_executor_id || t("common.missing")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <nav className="pagination" aria-label={t("queue.pagination")}>
              <button className="btn" type="button" aria-disabled={page.current <= 1}
                onClick={() => { if (page.current > 1) updateRoute({ number: page.current - 1 }); }}>{t("queue.previous")}</button>
              <span>{range}</span>
              <button className="btn" type="button" aria-disabled={page.current >= page.pages}
                onClick={() => { if (page.current < page.pages) updateRoute({ number: page.current + 1 }); }}>{t("queue.next")}</button>
              <label className="page-size">{t("queue.pageSize")}
                <select value={route.size} onChange={(event) => updateRoute({ size: Number(event.target.value), number: 1 })}>
                  {sizeOptions.map((size) => <option key={size} value={size}>{formatNumber(size)}</option>)}
                </select>
              </label>
            </nav>
          </>
        )}
      </div>
    </section>
  );
}
