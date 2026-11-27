import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { ADMIN_PERMISSIONS, can, hasPermission } from "../permissions.js";
import { useReferenceData } from "../referenceData.jsx";
import {
  formatDateTime,
  formatDuration,
  getCurrentExecutorId,
  getCurrentStatus,
  getLastExecutorId,
  isTerminalStatus,
  personName,
  previewText,
  statusLabel,
  toLocalInputValue,
  toUtcIsoFromLocal,
} from "../ticketUtils.js";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";

const VIEWS = [
  ["all", "Все"],
  ["open", "Открытые"],
  ["closed", "Закрытые"],
  ["mine", "Назначенные мне"],
  ["remote", "Рекомендовано удалённо"],
];

const EDITABLE_STATUSES = new Set(["CREATED", "CREATED_FROM_TICKET_USER", "ACCEPTED", "DEFERRED"]);
const REQUIRED_WORKFLOW_COMMENT = new Set(["reject", "defer", "cancel"]);

const EMPTY_CREATE = {
  client_id: 0,
  user_id: 0,
  contact_user_id: 0,
  department_id: 0,
  text_of_ticket: "",
  description: "",
  remote_work_recommended: false,
  urgency: "normal",
  planned_at: "",
  comment: "",
};

function mapById(rows, key, valueGetter) {
  return Object.fromEntries((rows || []).map((row) => [row[key], valueGetter(row)]));
}

function getTicketActions(ticket, permissions) {
  const status = getCurrentStatus(ticket);
  const terminal = isTerminalStatus(status) || Boolean(ticket?.is_closed);
  const operate = can.ticketsOperate(permissions);
  return {
    accept: hasPermission(permissions, ADMIN_PERMISSIONS.TICKET_ACCEPTED)
      && ["CREATED", "CREATED_FROM_TICKET_USER", "DEFERRED", "ASSIGNED", "SUSPENDED"].includes(status),
    reject: can.ticketsCancel(permissions) && ["CREATED", "CREATED_FROM_TICKET_USER"].includes(status),
    defer: operate && ["ACCEPTED", "ASSIGNED", "PAUSED", "SUSPENDED"].includes(status),
    assign: operate && ["ACCEPTED", "DEFERRED", "ASSIGNED"].includes(status),
    startWork: can.ticketsWork(permissions) && status === "ASSIGNED",
    startRemoteWork: can.ticketsRemoteWork(permissions) && status === "ASSIGNED" && Boolean(ticket?.remote_work_recommended),
    pause: can.ticketsWork(permissions) && status === "AT_WORK",
    resume: can.ticketsWork(permissions) && status === "PAUSED",
    finish: can.ticketsWork(permissions) && status === "AT_WORK",
    retrospective: can.ticketsRetrospective(permissions) && status === "ASSIGNED",
    execute: can.ticketsExecute(permissions) && ["READY_FOR_REVIEW", "SUSPENDED"].includes(status),
    cancel: can.ticketsCancel(permissions) && !terminal,
    editData: operate && EDITABLE_STATUSES.has(status),
    comment: operate && !terminal,
  };
}

export default function TicketsPage({ permissions, showToast, pageContext, onNavigate }) {
  const refs = useReferenceData();
  const { clients, admins, departments, users } = refs;
  const [tickets, setTickets] = useState([]);
  const [view, setView] = useState("all");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [currentAdmin, setCurrentAdmin] = useState(null);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ clientId: 0, userId: 0, contactUserId: 0, departmentId: 0, executorId: 0, status: "", urgency: "" });

  const mayView = can.ticketsView(permissions);

  useEffect(() => {
    if (!mayView) return;
    const jobs = [];
    if (can.clientsView(permissions)) jobs.push(refs.ensureClients());
    if (can.adminsView(permissions)) jobs.push(refs.ensureAdmins());
    if (can.departmentsView(permissions)) jobs.push(refs.ensureDepartments());
    jobs.push(api.getCurrentAdmin().then(setCurrentAdmin).catch(() => setCurrentAdmin(null)));
    Promise.allSettled(jobs);
  }, [mayView, permissions.join("|")]);

  useEffect(() => {
    if (!mayView) return;
    loadTickets(view);
  }, [mayView, view]);

  useEffect(() => {
    if (!pageContext) return;
    if (pageContext.clientId) setFilters((f) => ({ ...f, clientId: Number(pageContext.clientId) }));
    if (pageContext.userId) setFilters((f) => ({ ...f, userId: Number(pageContext.userId) }));
  }, [pageContext]);

  useEffect(() => {
    if (!filters.clientId || !can.usersView(permissions)) return;
    refs.ensureUsersByClient(filters.clientId).catch(() => {});
  }, [filters.clientId, permissions.join("|")]);

  async function loadTickets(mode = view) {
    setLoading(true);
    try {
      let payload;
      if (mode === "open") payload = await api.getOpenTickets();
      else if (mode === "closed") payload = await api.getClosedTickets();
      else if (mode === "mine") {
        let actor = currentAdmin;
        if (!actor) {
          actor = await api.getCurrentAdmin();
          setCurrentAdmin(actor);
        }
        payload = await api.getTicketsByExecutor(actor.employee_id);
      } else payload = await api.getTickets();
      const rows = Array.isArray(payload) ? payload : [];
      setTickets(mode === "remote" ? rows.filter((t) => t.remote_work_recommended) : rows);
    } catch (error) {
      showToast(error.message || "Не удалось загрузить заявки", "error");
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }

  const clientMap = useMemo(() => mapById(clients, "client_id", (x) => x.name || `#${x.client_id}`), [clients]);
  const userMap = useMemo(() => mapById(users, "employee_id", (x) => personName(x, `Пользователь #${x.employee_id}`)), [users]);
  const adminMap = useMemo(() => mapById(admins, "employee_id", (x) => personName(x, `Сотрудник #${x.employee_id}`)), [admins]);
  const departmentMap = useMemo(() => mapById(departments, "department_id", (x) => x.name || `#${x.department_id}`), [departments]);
  const statuses = useMemo(() => [...new Set(tickets.map(getCurrentStatus).filter(Boolean))].sort(), [tickets]);
  const filterUsers = filters.clientId ? refs.getUsersForClient(filters.clientId) : [];

  const extraFilters = useMemo(() => (ticket) => {
    const currentStatus = getCurrentStatus(ticket);
    const executorId = getCurrentExecutorId(ticket);
    const lastExecutorId = getLastExecutorId(ticket);
    if (filters.clientId && Number(ticket.client_id) !== filters.clientId) return false;
    if (filters.userId && Number(ticket.user_id) !== filters.userId) return false;
    if (filters.contactUserId && Number(ticket.contact_user_id) !== filters.contactUserId) return false;
    if (filters.departmentId && Number(ticket.department_id) !== filters.departmentId) return false;
    if (filters.executorId && executorId !== filters.executorId) return false;
    if (filters.status && currentStatus !== filters.status) return false;
    if (filters.urgency && String(ticket.urgency).toLowerCase() !== filters.urgency) return false;
    const q = search.trim().toLowerCase();
    if (!q) return true;
    const haystack = [
      ticket.ticket_id,
      ticket.text_of_ticket,
      ticket.description,
      clientMap[ticket.client_id],
      departmentMap[ticket.department_id],
      userMap[ticket.user_id],
      userMap[ticket.contact_user_id],
      adminMap[executorId],
      adminMap[lastExecutorId],
      statusLabel(currentStatus),
    ].filter(Boolean).join(" ").toLowerCase();
    return haystack.includes(q);
  }, [filters, search, clientMap, departmentMap, userMap, adminMap]);

  const columns = useMemo(() => [
    { key: "ticket_id", label: "№", className: "num" },
    { key: "client", label: "Клиент", getValue: (t) => clientMap[t.client_id] || `#${t.client_id}` },
    { key: "department", label: "Отдел", getValue: (t) => t.department_id ? departmentMap[t.department_id] || `#${t.department_id}` : "—" },
    { key: "text", label: "Текст заявки", getValue: (t) => previewText(t.text_of_ticket, 50), render: (t) => <span title={t.text_of_ticket}>{previewText(t.text_of_ticket, 50)}</span> },
    { key: "planned_at", label: "Запланировано", getValue: (t) => t.planned_at || "", render: (t) => formatDateTime(t.planned_at) },
    { key: "status", label: "Статус", getValue: getCurrentStatus, render: (t) => <span className={`status-badge status-${getCurrentStatus(t).toLowerCase()}`}>{statusLabel(getCurrentStatus(t))}</span> },
    { key: "urgency", label: "Срочность", render: (t) => <span className={`urgency urgency-${String(t.urgency).toLowerCase()}`}>{String(t.urgency || "normal").toUpperCase()}</span> },
    { key: "current_executor", label: "Назначенный исполнитель", getValue: (t) => adminMap[getCurrentExecutorId(t)] || (getCurrentExecutorId(t) ? `#${getCurrentExecutorId(t)}` : "—") },
    { key: "last_executor", label: "Последний актуальный исполнитель", getValue: (t) => adminMap[getLastExecutorId(t)] || (getLastExecutorId(t) ? `#${getLastExecutorId(t)}` : "—") },
    { key: "time_spent", label: "Затрачено", getValue: (t) => Number(t.time_spent || 0), render: (t) => formatDuration(t.time_spent) },
  ], [clientMap, departmentMap, adminMap]);

  async function ensureTicketReferences(ticket) {
    if (!ticket) return;
    const jobs = [];
    if (ticket.client_id && can.clientsView(permissions)) jobs.push(refs.ensureClient(ticket.client_id));
    if (ticket.department_id && can.departmentsView(permissions)) jobs.push(refs.ensureDepartment(ticket.department_id));
    if (can.adminsView(permissions)) {
      if (getCurrentExecutorId(ticket)) jobs.push(refs.ensureAdmin(getCurrentExecutorId(ticket)));
      if (getLastExecutorId(ticket)) jobs.push(refs.ensureAdmin(getLastExecutorId(ticket)));
    }
    if (ticket.client_id && can.usersView(permissions)) jobs.push(refs.ensureUsersByClient(ticket.client_id));
    await Promise.allSettled(jobs);
  }

  async function openTicket(row) {
    try {
      const ticket = await api.getTicket(row.ticket_id);
      setSelected(ticket);
      ensureTicketReferences(ticket);
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  function clearFilters() {
    setSearch("");
    setFilters({ clientId: 0, userId: 0, contactUserId: 0, departmentId: 0, executorId: 0, status: "", urgency: "" });
  }

  if (!mayView) return <div className="empty-permission">Нет права просмотра заявок.</div>;

  return (
    <div className="tickets-page">
      <div className="view-header">
        <div><h1>Заявки</h1><p>Поиск и комбинированные фильтры выполняются на frontend.</p></div>
        <div className="view-actions">
          <button className="btn" onClick={() => loadTickets()} disabled={loading}>{loading ? "Обновление..." : "Обновить"}</button>
          {can.ticketsCreate(permissions) && <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>+ Новая заявка</button>}
        </div>
      </div>

      <div className="segmented-filter ticket-views">
        {VIEWS.map(([id, label]) => <button key={id} className={view === id ? "active" : ""} onClick={() => setView(id)}>{label}</button>)}
      </div>

      <section className="ticket-filter-panel">
        <div className="ticket-search-row">
          <input className="ticket-search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск по №, тексту, описанию, клиенту, отделу, исполнителю..." />
          <button className="btn" onClick={clearFilters}>Сбросить</button>
        </div>
        <div className="ticket-filter-grid">
          <SelectFilter label="Клиент" value={filters.clientId} onChange={(v) => setFilters((f) => ({ ...f, clientId: Number(v), userId: 0, contactUserId: 0 }))} options={clients.map((x) => [x.client_id, x.name])} />
          <SelectFilter label="Отдел" value={filters.departmentId} onChange={(v) => setFilters((f) => ({ ...f, departmentId: Number(v) }))} options={departments.map((x) => [x.department_id, x.name])} />
          <SelectFilter label="Назначенный исполнитель" value={filters.executorId} onChange={(v) => setFilters((f) => ({ ...f, executorId: Number(v) }))} options={admins.map((x) => [x.employee_id, personName(x, `#${x.employee_id}`)])} />
          <SelectFilter label="Пользователь" value={filters.userId} onChange={(v) => setFilters((f) => ({ ...f, userId: Number(v) }))} options={filterUsers.map((x) => [x.employee_id, personName(x, `#${x.employee_id}`)])} disabled={!filters.clientId} />
          <SelectFilter label="Контакт" value={filters.contactUserId} onChange={(v) => setFilters((f) => ({ ...f, contactUserId: Number(v) }))} options={filterUsers.map((x) => [x.employee_id, personName(x, `#${x.employee_id}`)])} disabled={!filters.clientId} />
          <SelectFilter label="Статус" value={filters.status} onChange={(v) => setFilters((f) => ({ ...f, status: v }))} options={statuses.map((x) => [x, statusLabel(x)])} />
          <SelectFilter label="Срочность" value={filters.urgency} onChange={(v) => setFilters((f) => ({ ...f, urgency: v }))} options={[["normal", "NORMAL"], ["urgent", "URGENT"], ["maintenance", "MAINTENANCE"]]} />
        </div>
      </section>

      <DataTable
        storageKey={`tickets.${view}`}
        title="Список заявок"
        rows={tickets}
        columns={columns}
        selectedId={selected?.ticket_id}
        getRowId={(row) => row.ticket_id}
        onRowClick={openTicket}
        extraFilters={extraFilters}
        emptyText={loading ? "Загрузка..." : "Заявки не найдены"}
      />

      {createOpen && <CreateTicketDialog refs={refs} clients={clients} departments={departments} onClose={() => setCreateOpen(false)} onCreated={(ticket) => { setCreateOpen(false); setSelected(ticket); ensureTicketReferences(ticket); loadTickets(); }} showToast={showToast} />}
      {selected && <TicketDialog ticket={selected} permissions={permissions} refs={refs} clients={clients} users={users} admins={admins} departments={departments} onClose={() => setSelected(null)} onChanged={(ticket) => { setSelected(ticket); ensureTicketReferences(ticket); setTickets((rows) => rows.map((r) => r.ticket_id === ticket.ticket_id ? ticket : r)); }} showToast={showToast} onNavigate={onNavigate} />}
    </div>
  );
}

function SelectFilter({ label, value, onChange, options, disabled = false }) {
  return <label><span>{label}</span><select disabled={disabled} value={value} onChange={(e) => onChange(e.target.value)}><option value="">Все</option>{options.map(([id, text]) => <option key={id} value={id}>{text}</option>)}</select></label>;
}

function CreateTicketDialog({ refs, clients, departments, onClose, onCreated, showToast }) {
  const [form, setForm] = useState(EMPTY_CREATE);
  const [busy, setBusy] = useState(false);
  const availableUsers = form.client_id ? refs.getUsersForClient(form.client_id) : [];

  useEffect(() => {
    if (form.client_id) refs.ensureUsersByClient(form.client_id).catch(() => {});
  }, [form.client_id]);

  function patch(key, value) { setForm((f) => ({ ...f, [key]: value })); }
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const ticket = await api.createTicket({
        client_id: Number(form.client_id),
        text_of_ticket: form.text_of_ticket,
        description: form.description,
        user_id: Number(form.user_id || 0),
        contact_user_id: Number(form.contact_user_id || 0),
        department_id: Number(form.department_id || 0),
        remote_work_recommended: Boolean(form.remote_work_recommended),
        urgency: form.urgency,
        planned_at: form.planned_at ? toUtcIsoFromLocal(form.planned_at) : null,
        comment: form.comment,
      });
      showToast("Заявка создана", "success");
      onCreated(ticket);
    } catch (error) { showToast(error.message, "error"); }
    finally { setBusy(false); }
  }

  return <Modal title="Новая заявка" onClose={onClose} wide>
    <form onSubmit={submit} className="form-grid ticket-create-form">
      <label><span>Клиент *</span><select required value={form.client_id} onChange={(e) => setForm((f) => ({ ...f, client_id: Number(e.target.value), user_id: 0, contact_user_id: 0 }))}><option value="0">—</option>{clients.map((x) => <option key={x.client_id} value={x.client_id}>{x.name}</option>)}</select></label>
      <label><span>Пользователь</span><select value={form.user_id} onChange={(e) => patch("user_id", Number(e.target.value))}><option value="0">Без пользователя</option>{availableUsers.map((x) => <option key={x.employee_id} value={x.employee_id}>{personName(x, `#${x.employee_id}`)}</option>)}</select></label>
      <label><span>Контакт</span><select value={form.contact_user_id} onChange={(e) => patch("contact_user_id", Number(e.target.value))}><option value="0">—</option>{availableUsers.map((x) => <option key={x.employee_id} value={x.employee_id}>{personName(x, `#${x.employee_id}`)}</option>)}</select></label>
      <label><span>Отдел</span><select value={form.department_id} onChange={(e) => patch("department_id", Number(e.target.value))}><option value="0">—</option>{departments.map((x) => <option key={x.department_id} value={x.department_id}>{x.name}</option>)}</select></label>
      <label className="wide-field"><span>Текст заявки *</span><textarea required rows="4" value={form.text_of_ticket} onChange={(e) => patch("text_of_ticket", e.target.value)} /></label>
      <label className="wide-field"><span>Описание</span><textarea rows="4" value={form.description} onChange={(e) => patch("description", e.target.value)} /></label>
      <label><span>Срочность</span><select value={form.urgency} onChange={(e) => patch("urgency", e.target.value)}><option value="normal">NORMAL</option><option value="urgent">URGENT</option><option value="maintenance">MAINTENANCE</option></select></label>
      <label><span>Запланировано</span><input type="datetime-local" value={form.planned_at} onChange={(e) => patch("planned_at", e.target.value)} /></label>
      <label className="check-row"><input type="checkbox" checked={form.remote_work_recommended} onChange={(e) => patch("remote_work_recommended", e.target.checked)} /><span>Рекомендовано удалённо</span></label>
      <label className="wide-field"><span>Комментарий</span><textarea rows="2" value={form.comment} onChange={(e) => patch("comment", e.target.value)} /></label>
      <div className="card-actions wide-field"><button type="button" className="btn" onClick={onClose}>Отмена</button><button className="btn btn-primary" disabled={busy || !form.client_id || !form.text_of_ticket.trim()}>{busy ? "Создание..." : "Создать"}</button></div>
    </form>
  </Modal>;
}

function TicketDialog({ ticket, permissions, refs, clients, users, admins, departments, onClose, onChanged, showToast, onNavigate }) {
  const [action, setAction] = useState(null);
  const [tab, setTab] = useState("history");
  const [workflowComment, setWorkflowComment] = useState("");
  const [workflowBusy, setWorkflowBusy] = useState("");
  const actions = getTicketActions(ticket, permissions);
  const status = getCurrentStatus(ticket);
  const executorId = getCurrentExecutorId(ticket);
  const lastExecutorId = getLastExecutorId(ticket);
  const client = clients.find((x) => Number(x.client_id) === Number(ticket.client_id));
  const user = users.find((x) => Number(x.employee_id) === Number(ticket.user_id));
  const contact = users.find((x) => Number(x.employee_id) === Number(ticket.contact_user_id));
  const executor = admins.find((x) => Number(x.employee_id) === Number(executorId));
  const lastExecutor = admins.find((x) => Number(x.employee_id) === Number(lastExecutorId));
  const department = departments.find((x) => Number(x.department_id) === Number(ticket.department_id));
  const clientUsers = refs.getUsersForClient(ticket.client_id);

  useEffect(() => {
    if (ticket.client_id && can.usersView(permissions)) refs.ensureUsersByClient(ticket.client_id).catch(() => {});
  }, [ticket.client_id, permissions.join("|")]);

  async function apply(promise, success = "Заявка обновлена", clearWorkflowComment = false) {
    try {
      const next = await promise;
      if (next) onChanged(next);
      if (clearWorkflowComment) setWorkflowComment("");
      showToast(success, "success");
      setAction(null);
      return next;
    } catch (error) {
      showToast(error.message, "error");
      if (error.status === 409) {
        try { onChanged(await api.getTicket(ticket.ticket_id)); } catch { /* noop */ }
      }
      throw error;
    }
  }

  async function reload() {
    try { onChanged(await api.getTicket(ticket.ticket_id)); } catch (error) { showToast(error.message, "error"); }
  }

  async function runWorkflow(type) {
    const comment = workflowComment.trim();
    if (REQUIRED_WORKFLOW_COMMENT.has(type) && !comment) {
      showToast("Для этого действия нужен короткий комментарий / причина.", "error");
      return;
    }
    setWorkflowBusy(type);
    try {
      let promise;
      if (type === "accept") promise = api.acceptTicket(ticket.ticket_id, comment);
      else if (type === "reject") promise = api.rejectTicket(ticket.ticket_id, comment);
      else if (type === "defer") promise = api.deferTicket(ticket.ticket_id, comment);
      else if (type === "startRemoteWork") promise = api.startRemoteTicketWork(ticket.ticket_id, comment);
      else if (type === "pause") promise = api.pauseTicketWork(ticket.ticket_id, comment);
      else if (type === "finish") promise = api.finishTicketWork(ticket.ticket_id, comment);
      else if (type === "execute") promise = api.executeTicket(ticket.ticket_id, comment);
      else if (type === "cancel") promise = api.cancelTicket(ticket.ticket_id, comment);
      if (promise) await apply(promise, "Заявка обновлена", true);
    } catch {
      // apply() already reports backend errors.
    } finally {
      setWorkflowBusy("");
    }
  }

  const hasWorkflowButtons = [actions.accept, actions.reject, actions.defer, actions.assign, actions.startWork, actions.startRemoteWork, actions.pause, actions.resume, actions.finish, actions.retrospective, actions.execute, actions.cancel].some(Boolean);

  return <>
    <Modal title={`Заявка #${ticket.ticket_id}`} subtitle={`Статус: ${statusLabel(status)}`} onClose={onClose} wide>
      <div className="ticket-card">
        <div className="ticket-card-head"><div><span className="muted">Текст заявки</span><h2>{ticket.text_of_ticket}</h2></div><span className={`status-badge large status-${status.toLowerCase()}`}>{statusLabel(status)}</span></div>

        <div className="ticket-info-grid">
          <Info label="Клиент" value={client?.name || `#${ticket.client_id}`} onValueClick={onNavigate ? () => { onClose(); onNavigate("clients", { openClientId: ticket.client_id }); } : null} />
          <Info label="Пользователь" value={ticket.user_id ? personName(user, `#${ticket.user_id}`) : "—"} onValueClick={ticket.user_id && onNavigate ? () => { onClose(); onNavigate("users", { openUserId: ticket.user_id, clientId: ticket.client_id }); } : null} />
          <Info label="Контакт" value={ticket.contact_user_id ? personName(contact, `#${ticket.contact_user_id}`) : "—"} onValueClick={ticket.contact_user_id && onNavigate ? () => { onClose(); onNavigate("users", { openUserId: ticket.contact_user_id, clientId: ticket.client_id }); } : null} action={actions.editData ? () => setAction("contact") : null} />
          <Info label="Отдел" value={ticket.department_id ? department?.name || `#${ticket.department_id}` : "—"} action={actions.editData ? () => setAction("department") : null} />
          <Info label="Назначенный исполнитель" value={executorId ? personName(executor, `#${executorId}`) : "—"} action={actions.assign ? () => setAction("assign") : null} actionText={executorId ? "переназначить" : "назначить"} />
          <Info label="Последний актуальный исполнитель" value={lastExecutorId ? personName(lastExecutor, `#${lastExecutorId}`) : "—"} />
          <Info label="Срочность" value={String(ticket.urgency || "normal").toUpperCase()} action={actions.editData ? () => setAction("urgency") : null} />
          <Info label="Создана" value={formatDateTime(ticket.date_created)} />
          <Info label="Запланировано" value={formatDateTime(ticket.planned_at)} action={actions.editData ? () => setAction("schedule") : null} actionText={ticket.planned_at ? "изменить / снять" : "запланировать"} />
          <Info label="Затрачено" value={formatDuration(ticket.time_spent)} />
          <Info label="Удалённая работа" value={ticket.remote_work_recommended ? "Рекомендована" : "Не рекомендована"} action={actions.editData ? () => setAction("remoteRecommendation") : null} />
          {ticket.user_ticket_id > 0 && <Info label="Пользовательская заявка" value={`#${ticket.user_ticket_id}`} />}
        </div>

        <section className="ticket-actions-panel">
          <h3>Доступные действия</h3>
          <div className="ticket-action-buttons">
            {actions.accept && <button disabled={Boolean(workflowBusy)} className="btn btn-primary" onClick={() => runWorkflow("accept")}>Принять</button>}
            {actions.reject && <button disabled={Boolean(workflowBusy) || !workflowComment.trim()} className="btn btn-danger" onClick={() => runWorkflow("reject")}>Отклонить</button>}
            {actions.defer && <button disabled={Boolean(workflowBusy) || !workflowComment.trim()} className="btn" onClick={() => runWorkflow("defer")}>Отложить</button>}
            {actions.assign && <button disabled={Boolean(workflowBusy)} className="btn" onClick={() => setAction("assign")}>Назначить исполнителя</button>}
            {actions.startWork && <button disabled={Boolean(workflowBusy)} className="btn btn-primary" onClick={() => setAction("startWork")}>Начать работу</button>}
            {actions.startRemoteWork && <button disabled={Boolean(workflowBusy)} className="btn btn-primary" onClick={() => runWorkflow("startRemoteWork")}>Начать удалённо</button>}
            {actions.pause && <button disabled={Boolean(workflowBusy)} className="btn" onClick={() => runWorkflow("pause")}>Приостановить</button>}
            {actions.resume && <button disabled={Boolean(workflowBusy)} className="btn btn-primary" onClick={() => setAction("resume")}>Продолжить</button>}
            {actions.finish && <button disabled={Boolean(workflowBusy)} className="btn btn-primary" onClick={() => runWorkflow("finish")}>Завершить работу</button>}
            {actions.retrospective && <button disabled={Boolean(workflowBusy)} className="btn" onClick={() => setAction("retrospective")}>Зарегистрировать выполненную работу</button>}
            {actions.execute && <button disabled={Boolean(workflowBusy)} className="btn btn-primary" onClick={() => runWorkflow("execute")}>Выполнить</button>}
            {actions.cancel && <button disabled={Boolean(workflowBusy) || !workflowComment.trim()} className="btn btn-danger" onClick={() => runWorkflow("cancel")}>Отменить</button>}
            {!hasWorkflowButtons && <span className="muted">Нет доступных workflow-действий.</span>}
          </div>
          {hasWorkflowButtons && <label className="workflow-comment"><span>Комментарий к действию</span><textarea rows="2" value={workflowComment} onChange={(e) => setWorkflowComment(e.target.value)} placeholder="Короткий комментарий. Для отклонения, отложения и отмены обязателен." /></label>}
          {workflowBusy && <div className="muted workflow-progress">Выполнение...</div>}
        </section>

        <section className="ticket-text-block"><div className="section-title"><h3>Описание</h3>{actions.editData && <button className="link-button" onClick={() => setAction("description")}>изменить</button>}</div><p>{ticket.description || "—"}</p></section>
        <div className="ticket-card-tools"><button className="btn" onClick={reload}>Перечитать заявку</button></div>
        <div className="dialog-tabs ticket-tabs"><button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>История</button><button className={tab === "comments" ? "active" : ""} onClick={() => setTab("comments")}>Комментарии</button></div>
        {tab === "history" ? <History ticket={ticket} admins={admins} users={users} /> : <Comments ticket={ticket} admins={admins} users={users} canAdd={actions.comment} onAdd={() => setAction("comment")} />}
      </div>
    </Modal>
    {action && <TicketActionDialog type={action} ticket={ticket} workflowComment={workflowComment} users={clientUsers} admins={admins} departments={departments} onClose={() => setAction(null)} apply={apply} />}
  </>;
}

function Info({ label, value, action, actionText = "изменить", onValueClick }) {
  return <div className="info-item"><span>{label}</span><div>{onValueClick ? <button className="link-button value-link" onClick={onValueClick}>{value}</button> : <strong>{value}</strong>}{action && <button className="link-button" onClick={action}>{actionText}</button>}</div></div>;
}

function History({ ticket, admins, users }) {
  const people = new Map([...admins, ...users].map((x) => [Number(x.employee_id), personName(x, `#${x.employee_id}`)]));
  return <div className="timeline">{(ticket.statuses || []).map((record, i) => {
    const actorId = Number(record.actor_employee_id ?? record.actor_id ?? 0);
    const comment = typeof record.comment === "string" ? record.comment : record.comment?.value || "";
    return <article className="timeline-item" key={record.id ?? record.status_id ?? i}>
      <div className="timeline-time">{formatDateTime(record.date_created)}</div>
      <div className="timeline-content"><strong>{statusLabel(record.status)}</strong><span>{actorId ? people.get(actorId) || `#${actorId}` : "Действие пользователя"}</span>
        {Number(record.executor_id || 0) > 0 && <span>Исполнитель: {people.get(Number(record.executor_id)) || `#${record.executor_id}`}</span>}
        {record.actual_started_at && <span>Начало: {formatDateTime(record.actual_started_at)}</span>}
        {record.actual_finished_at && <span>Окончание: {formatDateTime(record.actual_finished_at)}</span>}
        {record.duration && <span>Продолжительность: {typeof record.duration === "number" ? formatDuration(record.duration) : String(record.duration)}</span>}
        {record.work_is_remote && <span>Удалённо</span>}
        {comment && <p>{comment}</p>}
      </div>
    </article>;
  })}</div>;
}

function Comments({ ticket, admins, users, canAdd, onAdd }) {
  const people = new Map([...admins, ...users].map((x) => [Number(x.employee_id), personName(x, `#${x.employee_id}`)]));
  return <div className="comments-panel">{canAdd && <div className="comments-actions"><button className="btn btn-primary" onClick={onAdd}>Добавить комментарий</button></div>}{(ticket.comments || []).map((comment, i) => <article className="comment-item" key={comment.id ?? comment.comment_id ?? i}><div><strong>{people.get(Number(comment.actor_id ?? comment.employee_id)) || `#${comment.actor_id ?? comment.employee_id ?? 0}`}</strong><span>{formatDateTime(comment.date_created)}</span></div><p>{typeof comment.comment === "string" ? comment.comment : comment.comment?.value || ""}</p></article>)}{!(ticket.comments || []).length && <div className="muted padded">Комментариев нет.</div>}</div>;
}

function TicketActionDialog({ type, ticket, workflowComment, users, admins, departments, onClose, apply }) {
  const [comment, setComment] = useState("");
  const [executorId, setExecutorId] = useState(getCurrentExecutorId(ticket) || 0);
  const [workIsRemote, setWorkIsRemote] = useState(false);
  const [value, setValue] = useState(() => {
    if (type === "description") return ticket.description || "";
    if (type === "contact") return String(ticket.contact_user_id || 0);
    if (type === "department") return String(ticket.department_id || 0);
    if (type === "urgency") return String(ticket.urgency || "normal");
    if (type === "remoteRecommendation") return String(Boolean(ticket.remote_work_recommended));
    if (type === "schedule") return toLocalInputValue(ticket.planned_at);
    return "";
  });
  const [startAt, setStartAt] = useState("");
  const [finishAt, setFinishAt] = useState("");
  const [hours, setHours] = useState(0);
  const [minutes, setMinutes] = useState(0);
  const [busy, setBusy] = useState(false);

  const titles = {
    assign: "Назначить исполнителя",
    startWork: "Начать работу",
    resume: "Продолжить работу",
    retrospective: "Зарегистрировать выполненную работу",
    description: "Изменить описание",
    contact: "Изменить контакт",
    department: "Изменить отдел",
    urgency: "Изменить срочность",
    schedule: "Планирование",
    remoteRecommendation: "Рекомендация удалённой работы",
    comment: "Добавить комментарий",
  };

  async function submit(e, clearSchedule = false) {
    e.preventDefault();
    setBusy(true);
    try {
      let promise;
      let clearWorkflowComment = false;
      if (type === "assign") { promise = api.assignTicket(ticket.ticket_id, Number(executorId), workflowComment.trim()); clearWorkflowComment = true; }
      else if (type === "startWork") { promise = api.startTicketWork(ticket.ticket_id, workIsRemote, workflowComment.trim()); clearWorkflowComment = true; }
      else if (type === "resume") { promise = api.resumeTicketWork(ticket.ticket_id, workIsRemote, workflowComment.trim()); clearWorkflowComment = true; }
      else if (type === "description") promise = api.updateTicketDescription(ticket.ticket_id, value);
      else if (type === "contact") promise = api.changeTicketContactUser(ticket.ticket_id, Number(value || 0));
      else if (type === "department") promise = api.changeTicketDepartment(ticket.ticket_id, Number(value || 0));
      else if (type === "urgency") promise = api.changeTicketUrgency(ticket.ticket_id, value || ticket.urgency);
      else if (type === "remoteRecommendation") promise = api.setTicketRemoteWorkRecommended(ticket.ticket_id, value === "true");
      else if (type === "schedule") promise = clearSchedule ? api.clearTicketSchedule(ticket.ticket_id) : api.scheduleTicket(ticket.ticket_id, toUtcIsoFromLocal(value));
      else if (type === "comment") promise = api.addTicketComment(ticket.ticket_id, comment);
      else if (type === "retrospective") {
        const duration = Math.max(0, Number(hours || 0) * 3600 + Number(minutes || 0) * 60);
        promise = api.completeTicketWorkRetroactively(ticket.ticket_id, {
          work_is_remote: workIsRemote,
          actual_started_at: startAt ? toUtcIsoFromLocal(startAt) : null,
          actual_finished_at: finishAt ? toUtcIsoFromLocal(finishAt) : null,
          duration,
          comment: workflowComment.trim(),
        });
        clearWorkflowComment = true;
      }
      await apply(promise, "Заявка обновлена", clearWorkflowComment);
    } catch {
      // apply() already shows the backend error and optionally reloads the ticket.
    } finally { setBusy(false); }
  }

  const validRetro = type !== "retrospective" || ((startAt && finishAt) || Number(hours) > 0 || Number(minutes) > 0);

  return <Modal title={titles[type] || "Действие"} onClose={onClose}>
    <form className="form-grid compact" onSubmit={submit}>
      {type === "assign" && <label><span>Исполнитель *</span><select required value={executorId} onChange={(e) => setExecutorId(Number(e.target.value))}><option value="0">—</option>{admins.map((x) => <option key={x.employee_id} value={x.employee_id}>{personName(x, `#${x.employee_id}`)}</option>)}</select></label>}
      {["startWork", "resume", "retrospective"].includes(type) && <label className="check-row"><input type="checkbox" checked={workIsRemote} onChange={(e) => setWorkIsRemote(e.target.checked)} /><span>Работа выполняется удалённо</span></label>}
      {type === "description" && <label className="wide-field"><span>Описание</span><textarea rows="5" value={value} onChange={(e) => setValue(e.target.value)} /></label>}
      {type === "contact" && <label><span>Контакт</span><select value={value} onChange={(e) => setValue(e.target.value)}><option value="0">—</option>{users.map((x) => <option key={x.employee_id} value={x.employee_id}>{personName(x, `#${x.employee_id}`)}</option>)}</select></label>}
      {type === "department" && <label><span>Отдел</span><select value={value} onChange={(e) => setValue(e.target.value)}><option value="0">—</option>{departments.map((x) => <option key={x.department_id} value={x.department_id}>{x.name}</option>)}</select></label>}
      {type === "urgency" && <label><span>Срочность</span><select value={value} onChange={(e) => setValue(e.target.value)}><option value="normal">NORMAL</option><option value="urgent">URGENT</option><option value="maintenance">MAINTENANCE</option></select></label>}
      {type === "remoteRecommendation" && <label><span>Рекомендация</span><select value={value} onChange={(e) => setValue(e.target.value)}><option value="true">Рекомендована</option><option value="false">Не рекомендована</option></select></label>}
      {type === "schedule" && <label><span>Запланировано</span><input type="datetime-local" value={value} onChange={(e) => setValue(e.target.value)} /></label>}
      {type === "retrospective" && <><label><span>Начало</span><input type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} /></label><label><span>Окончание</span><input type="datetime-local" value={finishAt} onChange={(e) => setFinishAt(e.target.value)} /></label><div className="wide-field duration-entry"><span>или продолжительность</span><label><span>Часы</span><input type="number" min="0" value={hours} onChange={(e) => setHours(e.target.value)} /></label><label><span>Минуты</span><input type="number" min="0" max="59" value={minutes} onChange={(e) => setMinutes(e.target.value)} /></label></div></>}
      {type === "comment" && <label className="wide-field"><span>Комментарий *</span><textarea required rows="3" value={comment} onChange={(e) => setComment(e.target.value)} /></label>}
      <div className="card-actions wide-field"><button type="button" className="btn" onClick={onClose}>Отмена</button>{type === "schedule" && ticket.planned_at && <button type="button" className="btn btn-danger" disabled={busy} onClick={(e) => submit(e, true)}>Снять план</button>}<button className="btn btn-primary" disabled={busy || (type === "assign" && !executorId) || (type === "comment" && !comment.trim()) || !validRetro}>{busy ? "Выполнение..." : "Сохранить"}</button></div>
    </form>
  </Modal>;
}
