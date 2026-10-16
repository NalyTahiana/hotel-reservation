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
import Field from "../../components/Field";
import { adminReservations, availableRooms, createAdminReservation, reservationAction, setReservationPayment } from "../../services/admin";
import { addDaysISO, formatAr, formatDate, formatDateTime, nightsBetween, STATUS_LABELS, todayISO } from "../../utils/format";

const ACTION_TEXT = {
  accept: ["Accepter la demande", "La disponibilité sera revérifiée avant l'acceptation.", "Accepter"],
  refuse: ["Refuser la demande", "Les dates seront libérées pour d'autres clients.", "Refuser"],
  cancel: ["Annuler la réservation", "Les dates seront libérées. Cette action est définitive.", "Annuler la réservation"],
};
const ACTION_LABEL = { accept: "Accepter", refuse: "Refuser", cancel: "Annuler" };

// Réservation saisie à la réception : client présent, donc ni e-mail ni mot de passe.
function NewReservationForm({ onSaved, onCancel }) {
  const toast = useToast();
  const [form, setForm] = useState({
    last_name: "", first_name: "", phone: "",
    check_in: todayISO(), check_out: addDaysISO(todayISO(), 1),
    guests: 1, room: null, amount_paid: "", comment: "",
  });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const nights = nightsBetween(form.check_in, form.check_out);
  const datesOk = form.check_in >= todayISO() && nights > 0 && Number(form.guests) >= 1;
  // Liste des chambres libres, recalculée dès que les dates ou le nombre de personnes changent.
  const rooms = useFetch(
    () => (datesOk ? availableRooms({ check_in: form.check_in, check_out: form.check_out, guests: form.guests }) : Promise.resolve([])),
    [form.check_in, form.check_out, form.guests]
  );
  const list = rooms.data || [];
  const selected = list.find((r) => r.id === form.room) || null;
  const total = selected ? nights * selected.price_per_night : 0;
  const paid = Number(form.amount_paid || 0);

  // Si la chambre choisie n'est plus libre après un changement de dates, on la désélectionne.
  if (form.room && !rooms.loading && rooms.data && !selected) setForm({ ...form, room: null });

  const submit = async (e) => {
    e.preventDefault();
    const local = {};
    if (!form.last_name.trim()) local.last_name = "Le nom est obligatoire.";
    if (!form.first_name.trim()) local.first_name = "Le prénom est obligatoire.";
    if (!/^\d{10}$/.test(form.phone)) local.phone = "Le numéro de téléphone doit comporter exactement 10 chiffres.";
    if (form.check_in < todayISO()) local.check_in = "La date d'arrivée ne peut pas être dans le passé.";
    if (nights <= 0) local.check_out = "La date de départ doit être postérieure à la date d'arrivée.";
    if (!form.room) local.room = "Choisissez une chambre disponible.";
    if (selected && Number(form.guests) > selected.capacity) local.guests = `Maximum ${selected.capacity} personne(s) pour cette chambre.`;
    if (paid < 0 || !Number.isInteger(paid)) local.amount_paid = "Saisissez un montant valide.";
    else if (selected && paid > total) local.amount_paid = `Le montant payé ne peut pas dépasser ${formatAr(total)}.`;
    setErrors(local);
    setError("");
    if (Object.keys(local).length) return;
    setBusy(true);
    try {
      await createAdminReservation({
        last_name: form.last_name.trim(), first_name: form.first_name.trim(), phone: form.phone,
        room: form.room, check_in: form.check_in, check_out: form.check_out,
        guests: Number(form.guests), amount_paid: paid, comment: form.comment,
      });
      toast.success("Réservation enregistrée.");
      onSaved();
    } catch (err) {
      setErrors(err.fields || {});
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="form" onSubmit={submit} noValidate>
      <ErrorMessage message={error} />
      <div className="form-row">
        <Field label="Nom" error={errors.last_name}><input value={form.last_name} onChange={set("last_name")} /></Field>
        <Field label="Prénom" error={errors.first_name}><input value={form.first_name} onChange={set("first_name")} /></Field>
      </div>
      <Field label="Téléphone" error={errors.phone} hint="10 chiffres, sans espaces">
        <input inputMode="numeric" maxLength={10} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/\D/g, "") })} />
      </Field>
      <div className="form-row">
        <Field label="Début de la réservation" error={errors.check_in}>
          <input type="date" min={todayISO()} value={form.check_in} onChange={(e) => {
            const check_in = e.target.value;
            setForm({ ...form, check_in, check_out: form.check_out <= check_in ? addDaysISO(check_in, 1) : form.check_out });
          }} />
        </Field>
        <Field label="Fin de la réservation" error={errors.check_out}>
          <input type="date" min={addDaysISO(form.check_in || todayISO(), 1)} value={form.check_out} onChange={set("check_out")} />
        </Field>
        <Field label="Personnes" error={errors.guests}>
          <input type="number" min={1} value={form.guests} onChange={set("guests")} />
        </Field>
      </div>

      <Field label={`Chambres disponibles${datesOk ? ` (${nights} nuit${nights > 1 ? "s" : ""})` : ""}`} error={errors.room}>
        <div>
          {!datesOk && <p className="muted">Choisissez des dates valides pour voir les chambres libres.</p>}
          {datesOk && rooms.loading && <Loader />}
          <ErrorMessage message={rooms.error} onRetry={rooms.reload} />
          {datesOk && !rooms.loading && rooms.data && list.length === 0 && (
            <p className="muted">Aucune chambre disponible sur cette période pour {form.guests} personne(s).</p>
          )}
          {list.length > 0 && (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th></th><th>N°</th><th>Chambre</th><th>Type</th><th>Capacité</th><th>Prix / nuit</th><th>Total séjour</th></tr></thead>
                <tbody>
                  {list.map((r) => (
                    <tr key={r.id} onClick={() => setForm({ ...form, room: r.id })} style={{ cursor: "pointer" }}>
                      <td><input type="radio" name="room" checked={form.room === r.id} onChange={() => setForm({ ...form, room: r.id })} aria-label={`Chambre ${r.number}`} /></td>
                      <td data-label="N°">{r.number}</td>
                      <td data-label="Chambre">{r.name}</td>
                      <td data-label="Type">{r.room_type_display}</td>
                      <td data-label="Capacité">{r.capacity}</td>
                      <td data-label="Prix / nuit">{formatAr(r.price_per_night)}</td>
                      <td data-label="Total séjour">{formatAr(nights * r.price_per_night)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Field>

      <div className="form-row">
        <Field label="Montant total à payer"><input value={selected ? formatAr(total) : "—"} readOnly /></Field>
        <Field label="Montant payé (Ar)" error={errors.amount_paid} hint={selected ? `Reste à payer : ${formatAr(Math.max(total - paid, 0))}` : "Choisissez d'abord une chambre"}>
          <input type="number" inputMode="numeric" min={0} max={selected ? total : undefined} value={form.amount_paid} onChange={set("amount_paid")} placeholder="0" />
        </Field>
      </div>
      <Field label="Commentaire (facultatif)"><textarea rows={2} maxLength={1000} value={form.comment} onChange={set("comment")} /></Field>
      <div className="modal-actions">
        <button type="button" className="btn btn-outline" onClick={onCancel}>Annuler</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Enregistrement..." : "Enregistrer la réservation"}</button>
      </div>
    </form>
  );
}

export default function Reservations() {
  const toast = useToast();
  const [filters, setFilters] = useState({ q: "", status: "", date_from: "", date_to: "" });
  const [page, setPage] = useState(1);
  const [detail, setDetail] = useState(null);
  const [pending, setPending] = useState(null); // { reservation, action }
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);
  const [payment, setPayment] = useState(null); // { reservation, value }
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

  const savePayment = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const updated = await setReservationPayment(payment.reservation.id, Number(payment.value || 0));
      toast.success("Paiement enregistré.");
      setDetail(updated);
      setPayment(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
      reload();
    }
  };

  return (
    <>
      <div className="page-head">
        <h1>Réservations</h1>
        <button className="btn btn-primary" onClick={() => setAdding(true)}>Nouvelle réservation</button>
      </div>
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
            <thead><tr><th>Référence</th><th>Client</th><th>Chambre</th><th>Arrivée</th><th>Départ</th><th>Nuits</th><th>Total</th><th>Payé</th><th>Demandée le</th><th>Statut</th><th>Actions</th></tr></thead>
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
            <dt>Contact</dt><dd>{[detail.customer.email, detail.customer.phone].filter(Boolean).join(" - ")}</dd>
            <dt>Chambre</dt><dd>{detail.room.number} - {detail.room.name}</dd>
            <dt>Séjour</dt><dd>{formatDate(detail.check_in)} au {formatDate(detail.check_out)} ({detail.nights} nuit(s))</dd>
            <dt>Personnes</dt><dd>{detail.guests}</dd>
            <dt>Prix par nuit</dt><dd>{formatAr(detail.price_per_night)}</dd>
            <dt>Total</dt><dd><strong>{formatAr(detail.total_amount)}</strong></dd>
            <dt>Montant payé</dt><dd>{formatAr(detail.amount_paid)}</dd>
            <dt>Reste à payer</dt><dd>{formatAr(detail.balance_due)}</dd>
            <dt>Statut</dt><dd><StatusBadge status={detail.status} /></dd>
            <dt>Commentaire</dt><dd>{detail.comment || "Aucun"}</dd>
          </dl>
        )}
        {detail && !["refused", "cancelled"].includes(detail.status) && (
          <div className="modal-actions">
            <button className="btn btn-outline" onClick={() => setPayment({ reservation: detail, value: String(detail.amount_paid) })}>Enregistrer un paiement</button>
          </div>
        )}
      </Modal>
      <Modal open={adding} wide title="Nouvelle réservation (client à l'hôtel)" onClose={() => setAdding(false)}>
        {adding && <NewReservationForm onCancel={() => setAdding(false)} onSaved={() => { setAdding(false); setPage(1); reload(); }} />}
      </Modal>
      <Modal open={!!payment} title={payment ? `Paiement - ${payment.reservation.reference}` : ""} onClose={() => setPayment(null)}>
        {payment && (
          <form className="form" onSubmit={savePayment}>
            <Field label="Montant total payé (Ar)" hint={`Total de la réservation : ${formatAr(payment.reservation.total_amount)}`}>
              <input type="number" min={0} max={payment.reservation.total_amount} value={payment.value} onChange={(e) => setPayment({ ...payment, value: e.target.value })} />
            </Field>
            <div className="modal-actions">
              <button type="button" className="btn btn-outline" onClick={() => setPayment(null)}>Annuler</button>
              <button className="btn btn-primary" disabled={busy}>{busy ? "Enregistrement..." : "Enregistrer"}</button>
            </div>
          </form>
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
