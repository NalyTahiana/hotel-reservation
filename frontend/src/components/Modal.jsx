export default function Modal({ open, title, onClose, wide = false, children }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={title}>
      <div className={`modal ${wide ? "modal-wide" : ""}`}>
        <div className="modal-head">
          <h3>{title}</h3>
          <button className="btn btn-sm btn-outline" onClick={onClose} aria-label="Fermer">Fermer</button>
        </div>
        {children}
      </div>
    </div>
  );
}
