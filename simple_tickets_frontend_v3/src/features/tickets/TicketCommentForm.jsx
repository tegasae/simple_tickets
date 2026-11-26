import { useId, useRef, useState } from "react";
import { t } from "../../shared/i18n/messages.js";
import "./fields.css";

const MAX_COMMENT_LENGTH = 1000;

export default function TicketCommentForm({
  value = "",
  onChange,
  onSubmit,
  busy = false,
  error = "",
  disabled = false,
  locked = false,
  submitLabel,
}) {
  const inputId = useId();
  const errorId = `${inputId}-error`;
  const field = useRef(null);
  const [validation, setValidation] = useState("");
  const problem = validation || error;

  function submit(event) {
    event.preventDefault();
    if (busy || disabled) return;
    const comment = value.trim();
    if (!comment || Array.from(comment).length > MAX_COMMENT_LENGTH) {
      setValidation(!comment
        ? t("ticketForm.commentRequired")
        : t("ticketForm.commentLength", { max: MAX_COMMENT_LENGTH }));
      field.current?.focus();
      return;
    }
    setValidation("");
    onSubmit(comment);
  }

  return (
    <form className="ticket-comment-form" aria-label={t("ticketForm.commentSubmit")}
      aria-busy={busy} onSubmit={submit} noValidate>
      <div className="ticket-form-field">
        <label htmlFor={inputId}>{t("ticketForm.comment")}</label>
        <textarea id={inputId} ref={field} name="comment" value={value} rows={3} required
          disabled={disabled} readOnly={busy || locked} aria-invalid={Boolean(problem)}
          aria-describedby={problem ? errorId : undefined}
          onChange={(event) => {
            setValidation("");
            onChange(event.target.value);
          }} />
        {problem && <p id={errorId} className="field-error" role="alert">{problem}</p>}
      </div>
      <button type="submit" className="btn btn-primary" disabled={disabled} aria-disabled={busy}>
        {busy ? t("ticketForm.commentSubmitting") : submitLabel ?? t("ticketForm.commentSubmit")}
      </button>
    </form>
  );
}
