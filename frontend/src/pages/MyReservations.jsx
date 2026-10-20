import { useState } from "react";
import { Link } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import Loader from "../components/Loader";
import Modal from "../components/Modal";
import Pagination from "../components/Pagination";
import PaymentBadge from "../components/PaymentBadge";
import StatusBadge from "../components/StatusBadge";
import { useToast } from "../context/ToastContext";
import useFetch from "../hooks/useFetch";
import { cancelMyReservation, myReservations } from "../services/reservations";
import { formatAr, formatDate, formatDateTime, STATUS_LABELS } from "../utils/format";

export default function MyReservations() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [detail, setDetail] = useState(null);
  const [toCancel, setToCancel] = useState(null);
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useFetch(() => myReservations({ page, status }), [page, status]);

  const confirmCancel = async () => {
    setBusy(true);
    try {
      await cancelMyReservation(toCancel.id);
      toast.success("Votre réservation a été annulée. Les dates sont libérées.");
      setToCancel(null);
      setDetail(null);
      reload();
    } catch (e) {
      toast.error(e.message);
      setToCancel(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <h1>Mes réservations</h1>
      <div className="filters">
        <label>Statut
          <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
            <option value="">Tous</option>
            {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
      </div>
      {loading && <Loader />}
      <ErrorMessage message={error} onRetry={reload} />
      {data && data.results.length === 0 && (
        <EmptyState title="Aucune réservation" text="Vous n'avez pas encore de demande de réservation.">
          <Link className="btn btn-primary" to="/chambres">Découvrir les chambres</Link>
        </EmptyState>
      )}
      {data && data.results.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Référence</th><th>Chambre</th><th>Arrivée</th><th>Départ</th><th>Nuits</th><th>Total</th><th>Statut</th><th>Paiement</th><th>Actions</th></tr></thead>
            <tbody>
              {data.results.map((r) => (
                <tr key={r.id}>
                  <td data-label="Référence">{r.reference}</td>
                  <td data-label="Chambre">{r.room.name}</td>
                  <td data-label="Arrivée">{formatDate(r.check_in)}</td>
                  <td data-label="Départ">{formatDate(r.check_out)}</td>
                  <td data-label="Nuits">{r.nights}</td>
                  <td data-label="Total">{formatAr(r.total_amount)}</td>
                  <td data-label="Statut"><StatusBadge status={r.status} /></td>
                  <td data-label="Paiement"><PaymentBadge reservation={r} /></td>
                  <td data-label="Actions" className="actions">
                    <button className="btn btn-sm btn-outline" onClick={() => setDetail(r)}>Détails</button>
                    {r.actions.includes("cancel") && <button className="btn btn-sm btn-danger" onClick={() => setToCancel(r)}>Annuler</button>}
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
            <dt>Chambre</dt><dd>{detail.room.number} - {detail.room.name}</dd>
            <dt>Arrivée</dt><dd>{formatDate(detail.check_in)}</dd>
            <dt>Départ</dt><dd>{formatDate(detail.check_out)}</dd>
            <dt>Personnes</dt><dd>{detail.guests}</dd>
            <dt>Prix par nuit</dt><dd>{formatAr(detail.price_per_night)}</dd>
            <dt>Nuits</dt><dd>{detail.nights}</dd>
            <dt>Total</dt><dd><strong>{formatAr(detail.total_amount)}</strong></dd>
            <dt>Statut</dt><dd><StatusBadge status={detail.status} /></dd>
            {["accepted", "completed"].includes(detail.status) && (<>
              <dt>Paiement</dt><dd><PaymentBadge reservation={detail} /></dd>
              <dt>Déjà payé</dt><dd>{formatAr(detail.amount_paid)}</dd>
              <dt>Reste à payer</dt><dd><strong>{formatAr(detail.balance)}</strong> (à régler en espèces à l'hôtel)</dd>
            </>)}
            {detail.payments.length > 0 && (<>
              <dt>Versements</dt>
              <dd><ul className="pay-history">{detail.payments.map((p) => <li key={p.id}>{formatDateTime(p.created_at)} : {formatAr(p.amount)}</li>)}</ul></dd>
            </>)}
            <dt>Demandée le</dt><dd>{formatDateTime(detail.created_at)}</dd>
            {detail.comment && (<><dt>Commentaire</dt><dd>{detail.comment}</dd></>)}
          </dl>
        )}
      </Modal>
      <ConfirmDialog
        open={!!toCancel} danger busy={busy} title="Annuler la réservation"
        message={toCancel ? `Voulez-vous vraiment annuler la réservation ${toCancel.reference} ? Cette action est définitive.` : ""}
        confirmLabel="Annuler la réservation" onConfirm={confirmCancel} onCancel={() => setToCancel(null)}
      />
    </div>
  );
}
