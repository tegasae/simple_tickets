import { useState } from "react";
import { canCancelByUser, canConfirmByUser, statusMeta } from "../status.js";

function fmt(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function StatusBadge({ status }) {
  const meta = statusMeta(status);
  return <span className={`badge badge-${meta.tone} user-status-${status}`}>{meta.label}</span>;
}

export default function TicketDialog({ ticket, busy, onClose, onReload, onCancel, onConfirm }) {
  const [comment, setComment] = useState("");
  const [tab, setTab] = useState("details");

  if (!ticket) return null;

  async function action(fn) {
    try {
      await fn(comment.trim());
      setComment("");
    } catch {
      // Error is already surfaced by TicketsPage via toast.
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="client-dialog user-ticket-dialog window-animate">
        <div className="dialog-titlebar">
          <div>
            <h2>Заявка #{ticket.ticket_id}</h2>
            <p>{ticket.text_of_ticket}</p>
          </div>
          <div className="window-controls">
            <button className="btn btn-small" type="button" onClick={onReload} disabled={busy}>Обновить</button>
            <button className="btn btn-icon" type="button" onClick={onClose}>×</button>
          </div>
        </div>

        <div className="dialog-tabs">
          <button className={tab === "details" ? "active" : ""} onClick={() => setTab("details")}>Карточка</button>
          <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>История ({ticket.statuses?.length || 0})</button>
          <button className={tab === "comments" ? "active" : ""} onClick={() => setTab("comments")}>Комментарии ({ticket.comments?.length || 0})</button>
        </div>

        <div className="dialog-body">
          {tab === "details" ? (
            <div className="ticket-detail-grid">
              <div className="form-panel">
                <div className="ticket-title-row">
                  <StatusBadge status={ticket.current_status} />
                  {ticket.is_closed ? <span className="badge badge-muted">Закрыта</span> : <span className="badge badge-ok">Открыта</span>}
                </div>
                <h3>{ticket.text_of_ticket}</h3>
                <p className="prewrap ticket-description">{ticket.description || "Описание не указано"}</p>

                <dl className="mini-dl ticket-meta">
                  <dt>Создана</dt><dd>{fmt(ticket.date_created)}</dd>
                  <dt>Закрыта</dt><dd>{fmt(ticket.date_finished)}</dd>
                  <dt>Срочность</dt><dd>{ticket.urgency_level}</dd>
                  <dt>User</dt><dd>#{ticket.user_id}</dd>
                  <dt>Контакт</dt><dd>{ticket.contact_user_id ? `#${ticket.contact_user_id}` : "—"}</dd>
                </dl>
              </div>

              <div className="meta-panel action-panel">
                <h3>Действия</h3>
                {canCancelByUser(ticket) || canConfirmByUser(ticket) ? (
                  <>
                    <label>
                      <span className="field-caption">Комментарий к действию</span>
                      <textarea rows="5" value={comment} onChange={(e) => setComment(e.target.value)} />
                    </label>
                    <div className="vertical-actions">
                      {canCancelByUser(ticket) ? (
                        <button className="btn btn-danger" disabled={busy} onClick={() => action(onCancel)}>
                          Отменить заявку
                        </button>
                      ) : null}
                      {canConfirmByUser(ticket) ? (
                        <button className="btn btn-primary" disabled={busy} onClick={() => action(onConfirm)}>
                          Подтвердить выполнение
                        </button>
                      ) : null}
                    </div>
                  </>
                ) : (
                  <p className="muted">Для текущего состояния действий пользователя нет.</p>
                )}
              </div>
            </div>
          ) : null}

          {tab === "history" ? (
            <div className="timeline user-timeline">
              {(ticket.statuses || []).length ? ticket.statuses.map((item, index) => (
                <div className="timeline-item" key={item.id ?? `${item.status}-${index}`}>
                  <strong><StatusBadge status={item.status} /></strong>
                  <span>{fmt(item.date_created || item.date)}</span>
                  {item.actor_id ? <small>Исполнитель действия: #{item.actor_id}</small> : null}
                  {item.status_comment || item.comment ? <p>{item.status_comment || item.comment}</p> : null}
                </div>
              )) : <div className="empty-permission">История отсутствует</div>}
            </div>
          ) : null}

          {tab === "comments" ? (
            <div className="timeline">
              {(ticket.comments || []).length ? ticket.comments.map((item, index) => (
                <div className="timeline-item" key={item.id ?? index}>
                  <strong>{item.actor_id ? `User/Admin #${item.actor_id}` : "Комментарий"}</strong>
                  <span>{fmt(item.date_created || item.date)}</span>
                  <p>{item.comment || ""}</p>
                </div>
              )) : <div className="empty-permission">Комментариев нет</div>}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
