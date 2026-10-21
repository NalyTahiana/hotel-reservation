import ErrorMessage from "./ErrorMessage";
import Loader from "./Loader";
import Modal from "./Modal";
import useFetch from "../hooks/useFetch";
import { formatAr, formatDate, formatDateTime } from "../utils/format";
import { HOTEL } from "../utils/hotel";

function Invoice({ fetcher, onClose }) {
  const { data: f, loading, error, reload } = useFetch(fetcher, []);
  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  return (
    <>
      <div className="invoice invoice-print">
        <div className="invoice-head">
          <div>
            <h2>{HOTEL.name}</h2>
            <p>{HOTEL.address}</p>
            <p>Téléphone : {HOTEL.phone}</p>
            <p>E-mail : {HOTEL.email}</p>
          </div>
          <div className="invoice-id">
            <h2>FACTURE</h2>
            <p><strong>N° {f.number}</strong></p>
            <p>Date : {formatDateTime(f.issued_at)}</p>
            <p>Réservation : {f.reference}</p>
          </div>
        </div>

        <div className="invoice-block">
          <h4>Client</h4>
          <p><strong>{f.customer.full_name}</strong></p>
          {f.customer.email && <p>{f.customer.email}</p>}
          {f.customer.phone && <p>{f.customer.phone}</p>}
        </div>

        <table className="invoice-table">
          <thead><tr><th>Désignation</th><th>Arrivée</th><th>Départ</th><th>Nuits</th><th>Prix par nuit</th><th>Montant</th></tr></thead>
          <tbody>
            <tr>
              <td>Chambre {f.room.number} - {f.room.name} ({f.room.room_type}), {f.guests} personne(s)</td>
              <td>{formatDate(f.check_in)}</td>
              <td>{formatDate(f.check_out)}</td>
              <td>{f.nights}</td>
              <td>{formatAr(f.price_per_night)}</td>
              <td>{formatAr(f.total_amount)}</td>
            </tr>
          </tbody>
        </table>

        <h4>Paiements reçus (espèces)</h4>
        <table className="invoice-table">
          <thead><tr><th>Reçu n°</th><th>Date</th><th>Mode</th><th>Note</th><th>Montant</th></tr></thead>
          <tbody>
            {f.payments.map((p) => (
              <tr key={p.id}>
                <td>{p.receipt}</td>
                <td>{formatDateTime(p.created_at)}</td>
                <td>{p.method}</td>
                <td>{p.note || "-"}</td>
                <td>{formatAr(p.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <dl className="invoice-totals">
          <dt>Total du séjour</dt><dd>{formatAr(f.total_amount)}</dd>
          <dt>Total payé</dt><dd>{formatAr(f.amount_paid)}</dd>
          <dt>Reste à payer</dt><dd><strong>{formatAr(f.balance)}</strong></dd>
        </dl>
        <p className="invoice-status">
          {f.balance === 0 ? "FACTURE ACQUITTÉE : le séjour est payé en totalité." : "Paiement partiel : le solde reste à régler à l'hôtel."}
        </p>
        <p className="invoice-foot">Montants en ariary (Ar). Document établi par {HOTEL.name}.</p>
      </div>
      <div className="modal-actions no-print">
        <button className="btn btn-outline" onClick={onClose}>Fermer</button>
        <button className="btn btn-primary" onClick={() => window.print()}>Imprimer / Enregistrer en PDF</button>
      </div>
    </>
  );
}

export default function InvoiceModal({ open, fetcher, onClose }) {
  return (
    <Modal open={open} title="Facture de paiement" onClose={onClose} wide>
      {open && <Invoice fetcher={fetcher} onClose={onClose} />}
    </Modal>
  );
}
