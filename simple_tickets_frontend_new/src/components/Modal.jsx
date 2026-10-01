export default function Modal({ title, subtitle = "", onClose, children, wide = false }) {
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}>
      <section className={`entity-dialog window-animate ${wide ? "entity-dialog-wide" : ""}`}>
        <header className="dialog-titlebar">
          <div>
            <h2>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <button className="btn btn-icon" onClick={onClose}>×</button>
        </header>
        <div className="dialog-body">{children}</div>
      </section>
    </div>
  );
}
