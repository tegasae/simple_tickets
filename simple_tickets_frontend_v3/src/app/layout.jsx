import { useEffect, useRef } from "react";
import { errorText, t } from "../shared/i18n/messages.js";

export function RouteLink({ href, navigate, onFollow, children, ...props }) {
  function follow(event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.altKey || event.ctrlKey || event.shiftKey) return;
    event.preventDefault();
    if (onFollow) onFollow();
    else navigate(href);
  }
  return <a href={href} onClick={follow} {...props}>{children}</a>;
}

export function Brand({ subtitle = "app.workspace" }) {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">{t("app.mark")}</span>
      <div><strong>{t("app.name")}</strong><span>{t(subtitle)}</span></div>
    </div>
  );
}

export function Shell({ queueHref, navigate, canView, canCreate, storageAvailable, onLogout, children }) {
  return (
    <>
      <a className="skip-link" href="#workspace">{t("app.skip")}</a>
      <header className="top-bar">
        <div className="top-inner">
          <Brand />
          {(canView || canCreate) && (
            <nav aria-label={t("app.navigation")}>
              {canView && <RouteLink href={queueHref} navigate={navigate} className="nav-link">{t("queue.title")}</RouteLink>}
              {canCreate && <RouteLink href="/tickets/new" navigate={navigate} className="nav-link">{t("work.newTicket")}</RouteLink>}
            </nav>
          )}
          <button className="btn logout" type="button" onClick={onLogout}>{t("session.logout")}</button>
        </div>
      </header>
      <main className="workspace" id="workspace" tabIndex={-1}>
        {!storageAvailable && <p className="storage-notice" role="status">{t("session.storageUnavailable")}</p>}
        {children}
      </main>
    </>
  );
}

export function StatePanel({ title, description, children, loading = false, error = false, page = false }) {
  const focusTarget = useRef(null);
  useEffect(() => {
    const active = document.activeElement;
    if (page && (active === document.body || active?.id === "workspace")) focusTarget.current?.focus();
  }, [page]);
  const Tag = loading ? "p" : page ? "h1" : "h2";
  return (
    <section className="state-panel">
      <div role={loading ? "status" : error ? "alert" : undefined}>
        <Tag ref={focusTarget} tabIndex={page ? -1 : undefined}>{title}</Tag>
        {description && <p>{description}</p>}
      </div>
      {children && <div className="state-actions">{children}</div>}
    </section>
  );
}

export function ErrorPanel({ error, retry, back }) {
  if (error?.status === 403) {
    return (
      <StatePanel title={t("error.forbidden")} description={t("error.noTicketsPermission")} error page={Boolean(back)}>
        <button type="button" className="btn" onClick={retry}>{t("common.retry")}</button>
        {back}
      </StatePanel>
    );
  }
  if (error?.status === 404 && back) {
    return <StatePanel title={t("error.notFound")} description={t("error.ticketMissing")} error page>{back}</StatePanel>;
  }
  return (
    <StatePanel title={t("error.title")} description={errorText(error)} error page={Boolean(back)}>
      <button type="button" className="btn" onClick={retry}>{t("common.retry")}</button>
      {back}
    </StatePanel>
  );
}
