export default function ConfirmDialog({ open, title, message, confirmLabel = "Confirmer", danger = false, busy = false, onConfirm, onCancel }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={title}>
      <div className="modal">
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="modal-actions">
          <button className="btn btn-outline" onClick={onCancel} disabled={busy}>Retour</button>
          <button className={`btn ${danger ? "btn-danger" : "btn-primary"}`} onClick={onConfirm} disabled={busy}>
            {busy ? "Veuillez patienter..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
