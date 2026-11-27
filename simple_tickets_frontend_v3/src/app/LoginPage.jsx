import { useEffect, useRef, useState } from "react";
import { Brand } from "./layout.jsx";
import { errorText, t } from "../shared/i18n/messages.js";

export default function LoginPage({ snapshot, session, appearance }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [clearedError, setClearedError] = useState(null);
  const loginField = useRef(null);
  const title = `${t("login.title")} · ${t("app.name")}`;
  useEffect(() => { document.title = title; }, [title]);
  useEffect(() => {
    if (document.activeElement === document.body) loginField.current?.focus();
  }, []);

  const pending = submitting || snapshot.phase === "authenticating";
  const problem = snapshot.error !== clearedError ? snapshot.error : null;
  const status = problem?.status;
  let message = "";
  if (problem) {
    if (problem.code === "session_expired") message = t("session.expired");
    else if (status === 401 || status === 403) message = t("login.invalid");
    else if (status === 422) message = t("login.inputError");
    else message = errorText(problem);
  }
  const logoutWarning = snapshot.logoutStatus === "unconfirmed";

  async function submit(event) {
    event.preventDefault();
    if (pending || !username.trim() || !password) return;
    setClearedError(null);
    setSubmitting(true);
    try {
      await session.login(username.trim(), password);
    } finally {
      setSubmitting(false);
      setPassword("");
      setVisible(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <Brand />
        {appearance}
        <h1>{t("login.title")}</h1>
        <form className="login-form" onSubmit={submit}>
          <label htmlFor="username">{t("login.username")}</label>
          <input ref={loginField} id="username" name="username" autoComplete="username" required value={username}
            aria-describedby={message ? "login-error" : undefined}
            onChange={(event) => { setUsername(event.target.value); setClearedError(snapshot.error); }} />
          <label htmlFor="password">{t("login.password")}</label>
          <div className="password-row">
            <input id="password" name="password" autoComplete="current-password" required value={password}
              type={visible ? "text" : "password"} aria-describedby={message ? "login-error" : undefined}
              onChange={(event) => { setPassword(event.target.value); setClearedError(snapshot.error); }} />
            <button className="btn" type="button" onClick={() => setVisible(!visible)}>
              {t(visible ? "login.hidePassword" : "login.showPassword")}
            </button>
          </div>
          {message && <p className="field-error" id="login-error" role="alert">{message}</p>}
          {logoutWarning && <p className="field-error" role="status">{t("session.logoutUnconfirmed")}</p>}
          <button className="btn btn-primary" disabled={pending} aria-busy={pending}>
            {t(pending ? "login.pending" : "login.submit")}
          </button>
        </form>
      </section>
    </main>
  );
}
