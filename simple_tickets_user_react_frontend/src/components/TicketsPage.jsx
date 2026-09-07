import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { statusMeta } from "../status.js";
import NewTicketModal from "./NewTicketModal.jsx";
import TicketDialog from "./TicketDialog.jsx";

function fmt(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function StatusBadge({ status }) {
  const meta = statusMeta(status);
  return <span className={`badge badge-${meta.tone} user-status-${status}`}>{meta.label}</span>;
}

export default function TicketsPage({ clientId, showToast, onSessionInvalid }) {
  const [tickets, setTickets] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  async function loadTickets(silent = false) {
    if (!silent) setLoading(true);
    try {
      const data = await api.getMyTickets(clientId);
      setTickets(Array.isArray(data) ? data : []);
    } catch (error) {
      if (error.status === 401) onSessionInvalid?.();
      showToast(error.message || "Не удалось загрузить заявки", "error");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => { loadTickets(); }, [clientId]);

  async function openTicket(ticketId) {
    setSelectedId(ticketId);
    setBusy(true);
    try {
      setSelected(await api.getTicket(ticketId));
    } catch (error) {
      showToast(error.message || "Не удалось открыть заявку", "error");
    } finally {
      setBusy(false);
    }
  }

  async function reloadSelected() {
    if (!selectedId) return;
    const value = await api.getTicket(selectedId);
    setSelected(value);
    await loadTickets(true);
  }

  async function createTicket(payload) {
    const created = await api.createTicket(payload);
    showToast(`Заявка #${created.ticket_id} создана`, "success");
    await loadTickets(true);
    setSelectedId(created.ticket_id);
    setSelected(created);
  }

  async function performAction(action, successMessage) {
    setBusy(true);
    try {
      const updated = await action();
      setSelected(updated);
      showToast(successMessage, "success");
      await loadTickets(true);
    } catch (error) {
      showToast(error.message || "Операция не выполнена", "error");
      throw error;
    } finally {
      setBusy(false);
    }
  }

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return tickets.filter((ticket) => {
      if (filter === "open" && ticket.is_closed) return false;
      if (filter === "waiting" && ticket.current_status !== "waiting_for_confirmation") return false;
      if (filter === "closed" && !ticket.is_closed) return false;
      if (!needle) return true;
      return [ticket.ticket_id, ticket.text_of_ticket, ticket.description, statusMeta(ticket.current_status).label]
        .some((value) => String(value ?? "").toLowerCase().includes(needle));
    });
  }, [tickets, filter, query]);

  const counters = useMemo(() => ({
    total: tickets.length,
    open: tickets.filter((x) => !x.is_closed).length,
    waiting: tickets.filter((x) => x.current_status === "waiting_for_confirmation").length,
    closed: tickets.filter((x) => x.is_closed).length,
  }), [tickets]);

  return (
    <>
      <div className="view-header">
        <div>
          <h1>Мои заявки</h1>
          <p>Client #{clientId} · {tickets.length} заявок</p>
        </div>
        <div className="view-actions">
          <button className="btn" onClick={() => loadTickets()} disabled={loading}>Обновить</button>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ Новая заявка</button>
        </div>
      </div>

      <div className="user-dashboard">
        <button className={filter === "all" ? "stat-card active" : "stat-card"} onClick={() => setFilter("all")}>
          <span>Всего</span><strong>{counters.total}</strong>
        </button>
        <button className={filter === "open" ? "stat-card active" : "stat-card"} onClick={() => setFilter("open")}>
          <span>Открытые</span><strong>{counters.open}</strong>
        </button>
        <button className={filter === "waiting" ? "stat-card active attention" : "stat-card attention"} onClick={() => setFilter("waiting")}>
          <span>Нужно подтвердить</span><strong>{counters.waiting}</strong>
        </button>
        <button className={filter === "closed" ? "stat-card active" : "stat-card"} onClick={() => setFilter("closed")}>
          <span>Закрытые</span><strong>{counters.closed}</strong>
        </button>
      </div>

      <div className="data-table-card">
        <div className="table-toolbar user-table-toolbar">
          <div>
            <h3>Заявки</h3>
            <span>Показано {filtered.length}</span>
          </div>
          <input className="ticket-search" placeholder="Поиск по теме, описанию, статусу…" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <div className="table-wrap">
          <table className="data-table user-tickets-table">
            <thead>
              <tr><th>ID</th><th>Тема</th><th>Статус</th><th>Срочность</th><th>Создана</th><th>Закрыта</th></tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td className="empty-cell" colSpan="6">Загрузка…</td></tr>
              ) : filtered.length ? filtered.map((ticket) => (
                <tr key={ticket.ticket_id} onDoubleClick={() => openTicket(ticket.ticket_id)} onClick={() => openTicket(ticket.ticket_id)}>
                  <td className="num">{ticket.ticket_id}</td>
                  <td className="ticket-subject-cell"><strong>{ticket.text_of_ticket}</strong><small>{ticket.description || ""}</small></td>
                  <td><StatusBadge status={ticket.current_status} /></td>
                  <td className="num">{ticket.urgency_level}</td>
                  <td>{fmt(ticket.date_created)}</td>
                  <td>{ticket.date_finished ? fmt(ticket.date_finished) : "—"}</td>
                </tr>
              )) : (
                <tr><td className="empty-cell" colSpan="6">Заявок по выбранному фильтру нет</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showCreate ? <NewTicketModal clientId={clientId} onClose={() => setShowCreate(false)} onCreate={createTicket} /> : null}

      {selected ? (
        <TicketDialog
          ticket={selected}
          busy={busy}
          onClose={() => { setSelected(null); setSelectedId(null); }}
          onReload={reloadSelected}
          onCancel={(comment) => performAction(() => api.cancelTicket(selected.ticket_id, comment), "Заявка отменена")}
          onConfirm={(comment) => performAction(() => api.confirmExecution(selected.ticket_id, comment), "Выполнение подтверждено")}
        />
      ) : null}
    </>
  );
}
