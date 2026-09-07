import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { can } from "../permissions.js";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";

const STATUS_LABELS = {
  created: "Создана",
  created_from_ticket_user: "Создана User",
  rejected: "Отклонена",
  accepted: "Принята",
  deferred: "Отложена",
  scheduled: "Запланирована",
  assigned: "Назначена",
  ready_to_work: "Готова к работе",
  at_work: "В работе",
  paused: "Пауза",
  ready_for_review: "На проверке",
  executed: "Выполнена",
  cancelled: "Отменена",
  cancelled_by_user: "Отменена User",
};

const EMPTY_CREATE = {
  client_id: 0,
  user_id: 0,
  contact_user_id: 0,
  department_id: 0,
  text_of_ticket: "",
  description: "",
  is_remote: false,
  urgency_level: 0,
  comment: "",
};

const EMPTY_WORK = {
  executor_id: 0,
  planned_start_at: "",
  planned_finish_at: "",
  actual_started_at: "",
  actual_finished_at: "",
  comment: "",
  department_id: 0,
  description: "",
  contact_user_id: 0,
  is_remote: false,
};

function currentStatus(ticket) {
  return ticket?.statuses?.length
    ? ticket.statuses[ticket.statuses.length - 1].status
    : "";
}

function fmtDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("ru-RU");
  } catch {
    return String(value);
  }
}

function toIso(localValue) {
  if (!localValue) return null;
  return new Date(localValue).toISOString();
}

function datesOrdered(start, finish) {
  if (!start || !finish) return true;
  return new Date(finish).getTime() >= new Date(start).getTime();
}

export default function TicketsPage({ permissions, showToast }) {
  const [tickets, setTickets] = useState([]);
  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [lookupState, setLookupState] = useState({
    clients: false,
    users: false,
    admins: false,
    departments: false,
  });
  const [lookupWarning, setLookupWarning] = useState("");
  const [selected, setSelected] = useState(null);
  const [createForm, setCreateForm] = useState(null);
  const [work, setWork] = useState(EMPTY_WORK);

  const mayView = can.ticketsView(permissions);
  const mayOperate = can.ticketsOperate(permissions);
  const mayAccept = can.ticketsAccept(permissions);

  async function loadOptional(name, allowed, loader, setter) {
    if (!allowed) {
      setter([]);
      return { name, ok: false, expected: true };
    }
    try {
      const payload = await loader();
      setter(Array.isArray(payload) ? payload : []);
      return { name, ok: true };
    } catch (error) {
      setter([]);
      return { name, ok: false, expected: error?.status === 403 };
    }
  }

  async function load() {
    if (!mayView) return;
    try {
      const payload = await api.getTickets();
      setTickets(Array.isArray(payload) ? payload : []);
    } catch (error) {
      showToast(error.message, "error");
      return;
    }

    const results = await Promise.all([
      loadOptional("клиенты", can.clientsView(permissions), () => api.getClients(), setClients),
      loadOptional("пользователи", can.usersView(permissions), () => api.getUsers(), setUsers),
      loadOptional("Admin", can.adminsView(permissions), () => api.getAdmins(), setAdmins),
      // Department API currently uses admin.operation and has no separate permission.
      loadOptional("отделы", can.adminsOperate(permissions), () => api.getDepartments(), setDepartments),
    ]);

    setLookupState({
      clients: results[0].ok,
      users: results[1].ok,
      admins: results[2].ok,
      departments: results[3].ok,
    });

    const unavailable = results.filter((x) => !x.ok).map((x) => x.name);
    setLookupWarning(
      unavailable.length
        ? `Недоступны справочники: ${unavailable.join(", ")}. Для них используются ID.`
        : "",
    );
  }

  useEffect(() => {
    load();
  }, [mayView, permissions.join("|")]);

  const clientMap = useMemo(
    () => Object.fromEntries(clients.map((x) => [x.client_id, x.name])),
    [clients],
  );
  const userMap = useMemo(
    () => Object.fromEntries(users.map((x) => [
      x.employee_id,
      `${x.first_name} ${x.last_name}`.trim() || `User ${x.employee_id}`,
    ])),
    [users],
  );
  const adminMap = useMemo(
    () => Object.fromEntries(admins.map((x) => [
      x.employee_id,
      `${x.first_name} ${x.last_name}`.trim() || `Admin ${x.employee_id}`,
    ])),
    [admins],
  );
  const departmentMap = useMemo(
    () => Object.fromEntries(departments.map((x) => [x.department_id, x.name])),
    [departments],
  );

  const columns = [
    { key: "ticket_id", label: "ID", className: "num" },
    {
      key: "status",
      label: "Статус",
      getValue: (row) => currentStatus(row),
      render: (row) => (
        <span className={`badge status-${currentStatus(row)}`}>
          {STATUS_LABELS[currentStatus(row)] || currentStatus(row)}
        </span>
      ),
    },
    {
      key: "client_id",
      label: "Клиент",
      getValue: (row) => clientMap[row.client_id] || `#${row.client_id}`,
    },
    { key: "text_of_ticket", label: "Тема" },
    {
      key: "department_id",
      label: "Отдел",
      getValue: (row) => row.department_id
        ? departmentMap[row.department_id] || `#${row.department_id}`
        : "—",
    },
    {
      key: "user_id",
      label: "User",
      getValue: (row) => row.user_id
        ? userMap[row.user_id] || `#${row.user_id}`
        : "—",
    },
    {
      key: "admin_id",
      label: "Создал Admin",
      getValue: (row) => row.admin_id
        ? adminMap[row.admin_id] || `#${row.admin_id}`
        : "auto",
    },
    {
      key: "is_closed",
      label: "Закрыта",
      render: (row) => (
        <span className={row.is_closed ? "badge badge-muted" : "badge badge-ok"}>
          {row.is_closed ? "Да" : "Нет"}
        </span>
      ),
    },
    { key: "date_created", label: "Создана", getValue: (row) => fmtDate(row.date_created) },
  ];

  function resetWorkFromTicket(ticket) {
    setWork({
      ...EMPTY_WORK,
      department_id: ticket.department_id || 0,
      description: ticket.description || "",
      contact_user_id: ticket.contact_user_id || 0,
      is_remote: Boolean(ticket.is_remote),
    });
  }

  async function openTicket(row) {
    try {
      const fresh = await api.getTicket(row.ticket_id);
      setSelected(fresh);
      resetWorkFromTicket(fresh);
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function refreshSelected() {
    if (!selected) return null;
    const fresh = await api.getTicket(selected.ticket_id);
    setSelected(fresh);
    setTickets((current) => current.map((x) => (
      x.ticket_id === fresh.ticket_id ? fresh : x
    )));
    return fresh;
  }

  async function perform(fn, success = "Заявка изменена") {
    try {
      await fn();
      await refreshSelected();
      showToast(success, "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function create() {
    try {
      const next = await api.createTicket({
        ...createForm,
        client_id: Number(createForm.client_id),
        user_id: Number(createForm.user_id) || 0,
        contact_user_id: Number(createForm.contact_user_id) || 0,
        department_id: Number(createForm.department_id) || 0,
        urgency_level: Number(createForm.urgency_level) || 0,
      });
      setCreateForm(null);
      await load();
      setSelected(next);
      resetWorkFromTicket(next);
      showToast("Ticket создан", "success");
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  const status = currentStatus(selected);
  const hasExecutor = Number(work.executor_id) > 0;
  const hasPlannedStart = Boolean(work.planned_start_at);
  const hasActualStart = Boolean(work.actual_started_at);
  const hasActualFinish = Boolean(work.actual_finished_at);
  const plannedDatesValid = datesOrdered(work.planned_start_at, work.planned_finish_at);
  const actualDatesValid = datesOrdered(work.actual_started_at, work.actual_finished_at);
  const hasComment = Boolean(work.comment.trim());

  const commentPayload = () => ({ comment: work.comment });
  const executorPayload = () => ({
    executor_id: Number(work.executor_id),
    comment: work.comment,
  });
  const schedulePayload = () => ({
    planned_start_at: toIso(work.planned_start_at),
    planned_finish_at: toIso(work.planned_finish_at),
    comment: work.comment,
  });
  const readyPayload = () => ({
    executor_id: Number(work.executor_id),
    planned_start_at: toIso(work.planned_start_at),
    planned_finish_at: toIso(work.planned_finish_at),
    comment: work.comment,
  });

  const actions = [];
  const addAction = (label, fn, options = {}) => actions.push({ label, fn, ...options });

  if (selected && mayOperate) {
    // CREATED / CREATED_FROM_TICKET_USER -> ACCEPTED / REJECTED.
    // DEFERRED / SCHEDULED / ASSIGNED / READY_TO_WORK -> ACCEPTED.
    if (["created", "created_from_ticket_user", "deferred", "scheduled", "assigned", "ready_to_work"].includes(status) && mayAccept) {
      addAction(
        ["created", "created_from_ticket_user"].includes(status) ? "Принять" : "Вернуть в принято",
        () => api.acceptTicket(selected.ticket_id, commentPayload()),
      );
    }
    if (["created", "created_from_ticket_user"].includes(status)) {
      addAction("Отклонить", () => api.rejectTicket(selected.ticket_id, commentPayload()), {
        danger: true,
        disabled: !hasComment,
        title: "Требуется комментарий",
      });
    }

    // Common management transitions. READY_FOR_REVIEW is intentionally handled by return-to-* below.
    if (["accepted", "scheduled", "assigned", "ready_to_work", "at_work", "paused"].includes(status)) {
      addAction("Отложить", () => api.deferTicket(selected.ticket_id, commentPayload()), {
        disabled: !hasComment,
        title: "Требуется комментарий",
      });
    }
    if (["accepted", "deferred", "scheduled", "assigned", "ready_to_work", "at_work", "paused"].includes(status)) {
      addAction("Планировать", () => api.scheduleTicket(selected.ticket_id, schedulePayload()), {
        disabled: !hasPlannedStart || !plannedDatesValid,
        title: !hasPlannedStart ? "Укажите плановое начало" : !plannedDatesValid ? "Плановое окончание раньше начала" : "",
      });
      addAction("Назначить", () => api.assignTicket(selected.ticket_id, executorPayload()), {
        disabled: !hasExecutor,
        title: "Укажите executor",
      });
      addAction("Готова к работе", () => api.readyToWorkTicket(selected.ticket_id, readyPayload()), {
        disabled: !hasExecutor || !hasPlannedStart || !plannedDatesValid,
        title: !hasExecutor ? "Укажите executor" : !hasPlannedStart ? "Укажите плановое начало" : !plannedDatesValid ? "Плановое окончание раньше начала" : "",
      });
    }

    if (["assigned", "ready_to_work"].includes(status)) {
      addAction("В работу", () => api.startWorkTicket(selected.ticket_id, commentPayload()));
    }
    if (status === "at_work") {
      addAction("Пауза", () => api.pauseTicket(selected.ticket_id, commentPayload()));
      addAction("На проверку", () => api.submitForReviewTicket(selected.ticket_id, commentPayload()));
    }
    if (status === "paused") {
      addAction("Возобновить", () => api.resumeTicket(selected.ticket_id, commentPayload()));
    }

    if (["scheduled", "assigned", "ready_to_work"].includes(status)) {
      addAction(
        "Завершено ретроспективно",
        () => api.recordCompletedTicket(selected.ticket_id, {
          executor_id: Number(work.executor_id),
          actual_started_at: toIso(work.actual_started_at),
          actual_finished_at: toIso(work.actual_finished_at),
          comment: work.comment,
        }),
        {
          disabled: !hasExecutor || !hasActualStart || !hasActualFinish || !actualDatesValid,
          title: !hasExecutor
            ? "Укажите executor"
            : !hasActualStart || !hasActualFinish
              ? "Укажите actual start и finish"
              : !actualDatesValid
                ? "Actual finish раньше actual start"
                : "",
        },
      );
    }

    if (status === "ready_for_review") {
      addAction("Подтвердить выполнение", () => api.confirmExecutionTicket(selected.ticket_id, commentPayload()));
      addAction("Вернуть в работу", () => api.returnToWorkTicket(selected.ticket_id, commentPayload()));
      addAction("Вернуть назначенной", () => api.returnToAssignedTicket(selected.ticket_id, executorPayload()), {
        disabled: !hasExecutor,
        title: "Укажите executor",
      });
      addAction("Вернуть в план", () => api.returnToScheduledTicket(selected.ticket_id, schedulePayload()), {
        disabled: !hasPlannedStart || !plannedDatesValid,
        title: !hasPlannedStart ? "Укажите плановое начало" : !plannedDatesValid ? "Плановое окончание раньше начала" : "",
      });
      addAction("Вернуть готовой", () => api.returnToReadyToWorkTicket(selected.ticket_id, readyPayload()), {
        disabled: !hasExecutor || !hasPlannedStart || !plannedDatesValid,
        title: !hasExecutor ? "Укажите executor" : !hasPlannedStart ? "Укажите плановое начало" : !plannedDatesValid ? "Плановое окончание раньше начала" : "",
      });
      addAction("Вернуть отложенной", () => api.returnToDeferredTicket(selected.ticket_id, commentPayload()), {
        disabled: !hasComment,
        title: "Требуется комментарий",
      });
    }

    // CANCELLED is not allowed directly from CREATED / CREATED_FROM_TICKET_USER.
    if (["accepted", "deferred", "scheduled", "assigned", "ready_to_work", "at_work", "paused", "ready_for_review"].includes(status)) {
      addAction("Отменить", () => api.cancelTicket(selected.ticket_id, commentPayload()), {
        danger: true,
        disabled: !hasComment,
        title: "Требуется комментарий",
      });
    }
  }

  if (!mayView) {
    return <div className="empty-permission">Нет права просмотра заявок.</div>;
  }

  return (
    <div>
      <div className="view-header">
        <div>
          <h1>Заявки Ticket</h1>
          <p>Только внутренний aggregate Ticket. TicketUser намеренно не показывается.</p>
          {lookupWarning && <p className="muted">{lookupWarning}</p>}
        </div>
        <div className="view-actions">
          <button className="btn" onClick={load}>Обновить</button>
          {mayOperate && (
            <button className="btn btn-primary" onClick={() => setCreateForm({ ...EMPTY_CREATE })}>
              Создать Ticket
            </button>
          )}
        </div>
      </div>

      <DataTable
        storageKey="tickets.internal"
        title="Ticket"
        rows={tickets}
        columns={columns}
        getRowId={(row) => row.ticket_id}
        selectedId={selected?.ticket_id}
        onRowClick={openTicket}
      />

      {createForm && (
        <Modal title="Новый Ticket" onClose={() => setCreateForm(null)} wide>
          <div className="form-grid">
            <label>
              <span>Клиент</span>
              {lookupState.clients ? (
                <select value={createForm.client_id} onChange={(e) => setCreateForm({ ...createForm, client_id: Number(e.target.value) })}>
                  <option value="0">—</option>
                  {clients.map((x) => <option key={x.client_id} value={x.client_id}>{x.name}</option>)}
                </select>
              ) : (
                <input type="number" min="1" value={createForm.client_id || ""} onChange={(e) => setCreateForm({ ...createForm, client_id: Number(e.target.value) || 0 })} placeholder="Client ID" />
              )}
            </label>

            <label>
              <span>Отдел</span>
              {lookupState.departments ? (
                <select value={createForm.department_id} onChange={(e) => setCreateForm({ ...createForm, department_id: Number(e.target.value) })}>
                  <option value="0">Без отдела</option>
                  {departments.map((x) => <option key={x.department_id} value={x.department_id}>{x.name}</option>)}
                </select>
              ) : (
                <input type="number" min="0" value={createForm.department_id || ""} onChange={(e) => setCreateForm({ ...createForm, department_id: Number(e.target.value) || 0 })} placeholder="Department ID (0 = none)" />
              )}
            </label>

            <label>
              <span>User</span>
              {lookupState.users ? (
                <select value={createForm.user_id} onChange={(e) => setCreateForm({ ...createForm, user_id: Number(e.target.value) })}>
                  <option value="0">Без User</option>
                  {users.filter((u) => !createForm.client_id || u.client_id === Number(createForm.client_id)).map((x) => (
                    <option key={x.employee_id} value={x.employee_id}>{userMap[x.employee_id]}</option>
                  ))}
                </select>
              ) : (
                <input type="number" min="0" value={createForm.user_id || ""} onChange={(e) => setCreateForm({ ...createForm, user_id: Number(e.target.value) || 0 })} placeholder="User ID (0 = none)" />
              )}
            </label>

            <label>
              <span>Contact User</span>
              {lookupState.users ? (
                <select value={createForm.contact_user_id} onChange={(e) => setCreateForm({ ...createForm, contact_user_id: Number(e.target.value) })}>
                  <option value="0">—</option>
                  {users.filter((u) => !createForm.client_id || u.client_id === Number(createForm.client_id)).map((x) => (
                    <option key={x.employee_id} value={x.employee_id}>{userMap[x.employee_id]}</option>
                  ))}
                </select>
              ) : (
                <input type="number" min="0" value={createForm.contact_user_id || ""} onChange={(e) => setCreateForm({ ...createForm, contact_user_id: Number(e.target.value) || 0 })} placeholder="Contact User ID" />
              )}
            </label>

            <label className="wide-field"><span>Текст заявки</span><input value={createForm.text_of_ticket} onChange={(e) => setCreateForm({ ...createForm, text_of_ticket: e.target.value })} /></label>
            <label className="wide-field"><span>Описание</span><textarea rows="4" value={createForm.description} onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })} /></label>
            <label><span>Срочность</span><input type="number" min="0" value={createForm.urgency_level} onChange={(e) => setCreateForm({ ...createForm, urgency_level: Number(e.target.value) })} /></label>
            <label className="check-row"><input type="checkbox" checked={createForm.is_remote} onChange={(e) => setCreateForm({ ...createForm, is_remote: e.target.checked })} /><span>Удалённо</span></label>
            <label className="wide-field"><span>Начальный комментарий</span><input value={createForm.comment} onChange={(e) => setCreateForm({ ...createForm, comment: e.target.value })} /></label>
          </div>
          <div className="card-actions">
            <button className="btn btn-primary" disabled={!createForm.client_id || !createForm.text_of_ticket.trim()} onClick={create}>Создать</button>
          </div>
        </Modal>
      )}

      {selected && (
        <Modal
          title={`Ticket #${selected.ticket_id}`}
          subtitle={`${STATUS_LABELS[status] || status} · v${selected.version}`}
          onClose={() => setSelected(null)}
          wide
        >
          <div className="ticket-detail-grid">
            <section className="form-panel">
              <h3>Карточка</h3>
              <dl className="mini-dl">
                <dt>Клиент</dt><dd>{clientMap[selected.client_id] || `#${selected.client_id}`}</dd>
                <dt>Создал Admin</dt><dd>{selected.admin_id ? adminMap[selected.admin_id] || `#${selected.admin_id}` : "автоматически"}</dd>
                <dt>User</dt><dd>{selected.user_id ? userMap[selected.user_id] || `#${selected.user_id}` : "—"}</dd>
                <dt>Contact</dt><dd>{selected.contact_user_id ? userMap[selected.contact_user_id] || `#${selected.contact_user_id}` : "—"}</dd>
                <dt>Отдел</dt><dd>{selected.department_id ? departmentMap[selected.department_id] || `#${selected.department_id}` : "—"}</dd>
                <dt>Создана</dt><dd>{fmtDate(selected.date_created)}</dd>
                <dt>Время</dt><dd>{selected.time_spent || 0} сек</dd>
              </dl>
              <h4>{selected.text_of_ticket}</h4>
              <p className="prewrap">{selected.description || "—"}</p>
            </section>

            <section className="form-panel">
              <h3>Параметры операции</h3>
              <div className="form-grid compact">
                <label>
                  <span>Executor</span>
                  {lookupState.admins ? (
                    <select value={work.executor_id} onChange={(e) => setWork({ ...work, executor_id: Number(e.target.value) })}>
                      <option value="0">—</option>
                      {admins.map((x) => <option key={x.employee_id} value={x.employee_id}>{adminMap[x.employee_id]}</option>)}
                    </select>
                  ) : (
                    <input type="number" min="1" value={work.executor_id || ""} onChange={(e) => setWork({ ...work, executor_id: Number(e.target.value) || 0 })} placeholder="Executor ID" />
                  )}
                </label>
                <label><span>План start</span><input type="datetime-local" value={work.planned_start_at} onChange={(e) => setWork({ ...work, planned_start_at: e.target.value })} /></label>
                <label><span>План finish</span><input type="datetime-local" value={work.planned_finish_at} onChange={(e) => setWork({ ...work, planned_finish_at: e.target.value })} /></label>
                <label><span>Actual start</span><input type="datetime-local" value={work.actual_started_at} onChange={(e) => setWork({ ...work, actual_started_at: e.target.value })} /></label>
                <label><span>Actual finish</span><input type="datetime-local" value={work.actual_finished_at} onChange={(e) => setWork({ ...work, actual_finished_at: e.target.value })} /></label>
                <label><span>Комментарий</span><textarea rows="3" value={work.comment} onChange={(e) => setWork({ ...work, comment: e.target.value })} /></label>
              </div>
              <div className="workflow-actions">
                {actions.map((action) => (
                  <button
                    key={action.label}
                    className={action.danger ? "btn btn-danger" : "btn"}
                    disabled={Boolean(action.disabled)}
                    title={action.title || ""}
                    onClick={() => perform(action.fn, action.label)}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </section>
          </div>

          {mayOperate && (
            <section className="form-panel ticket-edit-panel">
              <h3>Детали Ticket</h3>
              <div className="form-grid">
                <label className="wide-field"><span>Описание</span><textarea rows="3" value={work.description} onChange={(e) => setWork({ ...work, description: e.target.value })} /></label>
                <label>
                  <span>Contact User</span>
                  {lookupState.users ? (
                    <select value={work.contact_user_id} onChange={(e) => setWork({ ...work, contact_user_id: Number(e.target.value) })}>
                      <option value="0">—</option>
                      {users.filter((u) => u.client_id === selected.client_id).map((x) => (
                        <option key={x.employee_id} value={x.employee_id}>{userMap[x.employee_id]}</option>
                      ))}
                    </select>
                  ) : (
                    <input type="number" min="0" value={work.contact_user_id || ""} onChange={(e) => setWork({ ...work, contact_user_id: Number(e.target.value) || 0 })} placeholder="Contact User ID" />
                  )}
                </label>
                <label className="check-row"><input type="checkbox" checked={work.is_remote} onChange={(e) => setWork({ ...work, is_remote: e.target.checked })} /><span>Удалённо</span></label>
                <label>
                  <span>Отдел</span>
                  {lookupState.departments ? (
                    <select value={work.department_id} onChange={(e) => setWork({ ...work, department_id: Number(e.target.value) })}>
                      <option value="0">Без отдела</option>
                      {departments.map((x) => <option key={x.department_id} value={x.department_id}>{x.name}</option>)}
                    </select>
                  ) : (
                    <input type="number" min="0" value={work.department_id || ""} onChange={(e) => setWork({ ...work, department_id: Number(e.target.value) || 0 })} placeholder="Department ID" />
                  )}
                </label>
              </div>
              <div className="card-actions">
                <button className="btn" onClick={() => perform(
                  () => api.updateTicketDetails(selected.ticket_id, {
                    description: work.description,
                    contact_user_id: Number(work.contact_user_id) || 0,
                    is_remote: Boolean(work.is_remote),
                  }),
                  "Детали сохранены",
                )}>Сохранить детали</button>
                <button className="btn" onClick={() => perform(
                  () => api.changeTicketDepartment(selected.ticket_id, Number(work.department_id) || 0),
                  "Отдел изменён",
                )}>Сменить отдел</button>
                <button className="btn" disabled={!hasComment} onClick={() => perform(
                  () => api.addTicketComment(selected.ticket_id, work.comment),
                  "Комментарий добавлен",
                )}>Добавить комментарий</button>
                <button className="btn btn-danger" onClick={() => {
                  if (confirm("Удалить Ticket?")) {
                    perform(async () => {
                      await api.deleteTicket(selected.ticket_id);
                      setSelected(null);
                      await load();
                    }, "Ticket удалён");
                  }
                }}>Удалить Ticket</button>
              </div>
            </section>
          )}

          <div className="history-grid">
            <section className="form-panel">
              <h3>История статусов</h3>
              <div className="timeline">
                {(selected.statuses || []).map((item, index) => (
                  <div key={`${item.id}-${index}`} className="timeline-item">
                    <strong>{STATUS_LABELS[item.status] || item.status}</strong>
                    <span>{fmtDate(item.date_created)}</span>
                    <small>actor {item.actor_id || 0} · executor {item.executor_id || 0}</small>
                    {item.comment && <p>{item.comment}</p>}
                  </div>
                ))}
              </div>
            </section>
            <section className="form-panel">
              <h3>Комментарии</h3>
              <div className="timeline">
                {(selected.comments || []).map((item, index) => (
                  <div key={`${item.id}-${index}`} className="timeline-item">
                    <strong>#{item.id}</strong>
                    <span>{fmtDate(item.date_created)}</span>
                    <small>actor {item.actor_id || 0}</small>
                    <p>{item.comment}</p>
                  </div>
                ))}
                {!selected.comments?.length && <span className="muted">Комментариев нет</span>}
              </div>
            </section>
          </div>
        </Modal>
      )}
    </div>
  );
}
