import { useState } from "react";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorMessage from "../../components/ErrorMessage";
import Loader from "../../components/Loader";
import Modal from "../../components/Modal";
import Pagination from "../../components/Pagination";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../context/ToastContext";
import useFetch from "../../hooks/useFetch";
import { adminReservations, reservationAction } from "../../services/admin";
import { formatAr, formatDate, formatDateTime, STATUS_LABELS } from "../../utils/format";

const ACTION_TEXT = {
  accept: ["Accepter la demande", "La disponibilité sera revérifiée avant l'acceptation.", "Accepter"],
  refuse: ["Refuser la demande", "Les dates seront libérées pour d'autres clients.", "Refuser"],
  cancel: ["Annuler la réservation", "Les dates seront libérées. Cette action est définitive.", "Annuler la réservation"],
};
const ACTION_LABEL = { accept: "Accepter", refuse: "Refuser", cancel: "Annuler" };

export default function Reservations() {
  const toast = useToast();
  const [filters, setFilters] = useState({ q: "", status: "", date_from: "", date_to: "" });
  const [page, setPage] = useState(1);
  const [detail, setDetail] = useState(null);
  const [pending, setPending] = useState(null); // { reservation, action }
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useFetch(() => adminReservations({ ...filters, page }), [page, JSON.stringify(filters)]);
  const set = (k) => (e) => { setFilters({ ...filters, [k]: e.target.value }); setPage(1); };

  const run = async () => {
    setBusy(true);
    try {
      await reservationAction(pending.reservation.id, pending.action);
      toast.success("Statut mis à jour.");
      setPending(null);
      setDetail(null);
    } catch (e) {
      toast.error(e.message); // ex. chambre déjà occupée sur cette période
      setPending(null);
    } finally {
      setBusy(false);
      reload();
    }
  };

  return (
    <>
      <h1>Réservations</h1>
      <div className="filters">
        <label>Recherche<input placeholder="Référence ou client" value={filters.q} onChange={set("q")} /></label>
        <label>Statut
          <select value={filters.status} onChange={set("status")}>
            <option value="">Tous</option>
            {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>Du<input type="date" value={filters.date_from} onChange={set("date_from")} /></label>
        <label>Au<input type="date" value={filters.date_to} onChange={set("date_to")} /></label>
      </div>
      {loading && <Loader />}
      <ErrorMessage message={error} onRetry={reload} />
      {data && data.results.length === 0 && <EmptyState title="Aucune réservation" text="Aucune réservation ne correspond à ces critères." />}
      {data && data.results.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Référence</th><th>Client</th><th>Chambre</th><th>Arrivée</th><th>Départ</th><th>Nuits</th><th>Total</th><th>Demandée le</th><th>Statut</th><th>Actions</th></tr></thead>
            <tbody>
              {data.results.map((r) => (
                <tr key={r.id}>
                  <td data-label="Référence">{r.reference}</td>
                  <td data-label="Client">{r.customer.full_name}</td>
                  <td data-label="Chambre">{r.room.number}</td>
                  <td data-label="Arrivée">{formatDate(r.check_in)}</td>
                  <td data-label="Départ">{formatDate(r.check_out)}</td>
                  <td data-label="Nuits">{r.nights}</td>
                  <td data-label="Total">{formatAr(r.total_amount)}</td>
                  <td data-label="Demandée le">{formatDateTime(r.created_at)}</td>
                  <td data-label="Statut"><StatusBadge status={r.status} /></td>
                  <td data-label="Actions" className="actions">
                    <button className="btn btn-sm btn-outline" onClick={() => setDetail(r)}>Détails</button>
                    {r.actions.map((a) => (
                      <button key={a} className={`btn btn-sm ${a === "accept" ? "btn-primary" : "btn-danger"}`} onClick={() => setPending({ reservation: r, action: a })}>
                        {ACTION_LABEL[a]}
                      </button>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pagination page={page} count={data.count} onChange={setPage} />}

      <Modal open={!!detail} title={detail ? `Réservation ${detail.reference}` : ""} onClose={() => setDetail(null)}>
        {detail && (
          <dl className="details">
            <dt>Client</dt><dd>{detail.customer.full_name}</dd>
            <dt>Contact</dt><dd>{detail.customer.email} - {detail.customer.phone}</dd>
            <dt>Chambre</dt><dd>{detail.room.number} - {detail.room.name}</dd>
            <dt>Séjour</dt><dd>{formatDate(detail.check_in)} au {formatDate(detail.check_out)} ({detail.nights} nuit(s))</dd>
            <dt>Personnes</dt><dd>{detail.guests}</dd>
            <dt>Prix par nuit</dt><dd>{formatAr(detail.price_per_night)}</dd>
            <dt>Total</dt><dd><strong>{formatAr(detail.total_amount)}</strong></dd>
            <dt>Statut</dt><dd><StatusBadge status={detail.status} /></dd>
            <dt>Commentaire</dt><dd>{detail.comment || "Aucun"}</dd>
          </dl>
        )}
      </Modal>
      <ConfirmDialog
        open={!!pending} busy={busy} danger={pending?.action !== "accept"}
        title={pending ? ACTION_TEXT[pending.action][0] : ""}
        message={pending ? `Réservation ${pending.reservation.reference} : ${ACTION_TEXT[pending.action][1]}` : ""}
        confirmLabel={pending ? ACTION_TEXT[pending.action][2] : ""} onConfirm={run} onCancel={() => setPending(null)}
      />
    </>
  );
}
