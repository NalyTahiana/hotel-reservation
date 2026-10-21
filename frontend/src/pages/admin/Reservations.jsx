import { useState } from "react";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorMessage from "../../components/ErrorMessage";
import Field from "../../components/Field";
import InvoiceModal from "../../components/InvoiceModal";
import Loader from "../../components/Loader";
import Modal from "../../components/Modal";
import Pagination from "../../components/Pagination";
import PaymentBadge from "../../components/PaymentBadge";
import StatusBadge from "../../components/StatusBadge";
import { useToast } from "../../context/ToastContext";
import useFetch from "../../hooks/useFetch";
import { adminInvoice, adminReservations, recordPayment, reservationAction } from "../../services/admin";
import { formatAr, formatDate, formatDateTime, PAYMENT_LABELS, STATUS_LABELS } from "../../utils/format";

const ACTION_TEXT = {
  accept: ["Accepter la demande", "La disponibilité sera revérifiée. Le client règle ensuite en espèces : vous enregistrerez le paiement avec le bouton Encaisser.", "Accepter"],
  refuse: ["Refuser la demande", "Les dates seront libérées pour d'autres clients.", "Refuser"],
  cancel: ["Annuler la réservation", "Les dates seront libérées. Cette action est définitive.", "Annuler la réservation"],
};
const ACTION_LABEL = { accept: "Accepter", refuse: "Refuser", cancel: "Annuler" };
const canCollect = (r) => ["accepted", "completed"].includes(r.status) && r.balance > 0;

export default function Reservations() {
  const toast = useToast();
  const [filters, setFilters] = useState({ q: "", status: "", payment: "", date_from: "", date_to: "" });
  const [page, setPage] = useState(1);
  const [detail, setDetail] = useState(null);
  const [pending, setPending] = useState(null);
  const [busy, setBusy] = useState(false);
  const [invoiceId, setInvoiceId] = useState(null);
  const [paying, setPaying] = useState(null);
  const [payForm, setPayForm] = useState({ amount: "", note: "" });
  const [payError, setPayError] = useState("");
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
      toast.error(e.message);
      setPending(null);
    } finally {
      setBusy(false);
      reload();
    }
  };

  const openPayment = (r) => {
    setPaying(r);
    setPayForm({ amount: String(r.balance), note: "" });
    setPayError("");
  };

  const submitPayment = async (e) => {
    e.preventDefault();
    const amount = Number(payForm.amount);
    if (!Number.isInteger(amount) || amount < 1) return setPayError("Saisissez un montant entier supérieur à 0.");
    if (amount > paying.balance) return setPayError(`Le montant dépasse le reste à payer (${formatAr(paying.balance)}).`);
    setBusy(true);
    try {
      const updated = await recordPayment(paying.id, { amount, note: payForm.note.trim() });
      toast.success(updated.balance === 0 ? "Paiement enregistré : réservation payée en totalité." : `Paiement enregistré. Reste à payer : ${formatAr(updated.balance)}.`);
      setPaying(null);
      setDetail(null);
      setInvoiceId(updated.id);
    } catch (err) {
      setPayError(err.fields?.amount || err.message);
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
        <label>Paiement
          <select value={filters.payment} onChange={set("payment")}>
            <option value="">Tous</option>
            {Object.entries(PAYMENT_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
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
            <thead><tr><th>Référence</th><th>Client</th><th>Chambre</th><th>Arrivée</th><th>Départ</th><th>Nuits</th><th>Total</th><th>Payé</th><th>Demandée le</th><th>Statut</th><th>Paiement</th><th>Actions</th></tr></thead>
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
                  <td data-label="Payé">{formatAr(r.amount_paid)}</td>
                  <td data-label="Demandée le">{formatDateTime(r.created_at)}</td>
                  <td data-label="Statut"><StatusBadge status={r.status} /></td>
                  <td data-label="Paiement"><PaymentBadge reservation={r} /></td>
                  <td data-label="Actions" className="actions">
                    <button className="btn btn-sm btn-outline" onClick={() => setDetail(r)}>Détails</button>
                    {r.amount_paid > 0 && <button className="btn btn-sm btn-outline" onClick={() => setInvoiceId(r.id)}>Facture</button>}
                    {canCollect(r) && <button className="btn btn-sm btn-primary" onClick={() => openPayment(r)}>Encaisser</button>}
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
      {data && <Pagination page={page} count={data.count} pageSize={5} onChange={setPage} />}

      <Modal open={!!detail} title={detail ? `Réservation ${detail.reference}` : ""} onClose={() => setDetail(null)}>
        {detail && (
          <dl className="details">
            <dt>Client</dt><dd>{detail.customer.full_name}</dd>
            <dt>Contact</dt><dd>{[detail.customer.email, detail.customer.phone].filter(Boolean).join(" - ")}</dd>
            <dt>Chambre</dt><dd>{detail.room.number} - {detail.room.name}</dd>
            <dt>Séjour</dt><dd>{formatDate(detail.check_in)} au {formatDate(detail.check_out)} ({detail.nights} nuit(s))</dd>
            <dt>Personnes</dt><dd>{detail.guests}</dd>
            <dt>Prix par nuit</dt><dd>{formatAr(detail.price_per_night)}</dd>
            <dt>Total</dt><dd><strong>{formatAr(detail.total_amount)}</strong></dd>
            <dt>Statut</dt><dd><StatusBadge status={detail.status} /></dd>
            <dt>Paiement</dt><dd><PaymentBadge reservation={detail} /></dd>
            <dt>Déjà payé</dt><dd>{formatAr(detail.amount_paid)}</dd>
            <dt>Reste à payer</dt><dd><strong>{formatAr(detail.balance)}</strong></dd>
            {detail.payments.length > 0 && (<>
              <dt>Versements</dt>
              <dd><ul className="pay-history">{detail.payments.map((p) => <li key={p.id}>{formatDateTime(p.created_at)} : {formatAr(p.amount)} en espèces{p.note ? ` (${p.note})` : ""}</li>)}</ul></dd>
            </>)}
            <dt>Commentaire</dt><dd>{detail.comment || "Aucun"}</dd>
          </dl>
        )}
        {detail && (
          <div className="actions">
            {canCollect(detail) && <button className="btn btn-primary" onClick={() => openPayment(detail)}>Encaisser un paiement</button>}
            {detail.amount_paid > 0 && <button className="btn btn-outline" onClick={() => { setInvoiceId(detail.id); setDetail(null); }}>Voir la facture</button>}
          </div>
        )}
      </Modal>
      <Modal open={!!paying} title={paying ? `Paiement en espèces - ${paying.reference}` : ""} onClose={() => !busy && setPaying(null)}>
        {paying && (
          <form className="form" onSubmit={submitPayment} noValidate>
            <dl className="details">
              <dt>Client</dt><dd>{paying.customer.full_name}</dd>
              <dt>Total</dt><dd>{formatAr(paying.total_amount)}</dd>
              <dt>Déjà payé</dt><dd>{formatAr(paying.amount_paid)}</dd>
              <dt>Reste à payer</dt><dd><strong>{formatAr(paying.balance)}</strong></dd>
            </dl>
            <Field label="Montant reçu (Ar)" error={payError} hint="Saisissez la somme remise par le client.">
              <input type="number" min="1" max={paying.balance} step="1" inputMode="numeric" value={payForm.amount} autoFocus
                onChange={(e) => { setPayForm({ ...payForm, amount: e.target.value }); setPayError(""); }} />
            </Field>
            <Field label="Note (facultatif)">
              <input maxLength={255} value={payForm.note} onChange={(e) => setPayForm({ ...payForm, note: e.target.value })} placeholder="Acompte, solde, reçu n° ..." />
            </Field>
            <div className="modal-actions">
              <button type="button" className="btn btn-outline" disabled={busy} onClick={() => setPayForm({ ...payForm, amount: String(paying.balance) })}>Solde complet</button>
              <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? "Veuillez patienter..." : "Enregistrer le paiement"}</button>
            </div>
          </form>
        )}
      </Modal>
      <InvoiceModal open={invoiceId !== null} fetcher={() => adminInvoice(invoiceId)} onClose={() => setInvoiceId(null)} />
      <ConfirmDialog
        open={!!pending} busy={busy} danger={pending?.action !== "accept"}
        title={pending ? ACTION_TEXT[pending.action][0] : ""}
        message={pending ? `Réservation ${pending.reservation.reference} : ${ACTION_TEXT[pending.action][1]}` : ""}
        confirmLabel={pending ? ACTION_TEXT[pending.action][2] : ""} onConfirm={run} onCancel={() => setPending(null)}
      />
    </>
  );
}
