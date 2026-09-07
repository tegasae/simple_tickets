import { useState } from "react";

const EMPTY = {
  text_of_ticket: "",
  description: "",
  urgency_level: 0,
  department_id: 0,
  contact_user_id: 0,
  is_remote: false,
  comment: "",
};

export default function NewTicketModal({ clientId, onClose, onCreate }) {
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function set(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (!form.text_of_ticket.trim()) {
      setError("Введите тему заявки");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await onCreate({
        client_id: Number(clientId),
        text_of_ticket: form.text_of_ticket.trim(),
        description: form.description.trim(),
        contact_user_id: Number(form.contact_user_id) || 0,
        department_id: Number(form.department_id) || 0,
        is_remote: Boolean(form.is_remote),
        urgency_level: Math.max(0, Number(form.urgency_level) || 0),
        comment: form.comment.trim(),
      });
      onClose();
    } catch (err) {
      setError(err.message || "Не удалось создать заявку");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="entity-dialog window-animate" onSubmit={submit}>
        <div className="dialog-titlebar">
          <div>
            <h2>Новая заявка</h2>
            <p>Client #{clientId}</p>
          </div>
          <button className="btn btn-icon" type="button" onClick={onClose}>×</button>
        </div>
        <div className="dialog-body">
          <div className="form-grid">
            <label className="wide-field">
              <span>Тема *</span>
              <input value={form.text_of_ticket} onChange={(e) => set("text_of_ticket", e.target.value)} autoFocus />
            </label>
            <label className="wide-field">
              <span>Описание</span>
              <textarea rows="7" value={form.description} onChange={(e) => set("description", e.target.value)} />
            </label>
            <label>
              <span>Срочность</span>
              <input type="number" min="0" value={form.urgency_level} onChange={(e) => set("urgency_level", e.target.value)} />
            </label>
            <label className="check-row create-remote-row">
              <input type="checkbox" checked={form.is_remote} onChange={(e) => set("is_remote", e.target.checked)} />
              <span>Удалённая работа</span>
            </label>
          </div>

          <details className="advanced-fields">
            <summary>Дополнительные поля</summary>
            <div className="form-grid">
              <label>
                <span>Department ID</span>
                <input type="number" min="0" value={form.department_id} onChange={(e) => set("department_id", e.target.value)} />
              </label>
              <label>
                <span>Contact User ID</span>
                <input type="number" min="0" value={form.contact_user_id} onChange={(e) => set("contact_user_id", e.target.value)} />
              </label>
              <label className="wide-field">
                <span>Первичный комментарий</span>
                <textarea rows="3" value={form.comment} onChange={(e) => set("comment", e.target.value)} />
              </label>
            </div>
          </details>

          {error ? <div className="form-error modal-error">{error}</div> : null}
          <div className="dialog-actions">
            <button className="btn" type="button" onClick={onClose}>Отмена</button>
            <button className="btn btn-primary" disabled={busy}>{busy ? "Создание…" : "Создать заявку"}</button>
          </div>
        </div>
      </form>
    </div>
  );
}
