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
import { adminCustomer, adminCustomers, createCustomer, setCustomerActive } from "../../services/admin";
import Field from "../../components/Field";
import { formatAr, formatDate } from "../../utils/format";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const EMPTY = { last_name: "", first_name: "", phone: "", email: "" };

function CustomerForm({ onSaved, onCancel }) {
  const toast = useToast();
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    const local = {};
    if (!form.last_name.trim()) local.last_name = "Le nom est obligatoire.";
    if (!form.first_name.trim()) local.first_name = "Le prénom est obligatoire.";
    if (!/^\d{10}$/.test(form.phone)) local.phone = "Le numéro de téléphone doit comporter exactement 10 chiffres.";
    if (form.email.trim() && !EMAIL_RE.test(form.email.trim())) local.email = "Adresse e-mail invalide.";
    setErrors(local);
    setError("");
    if (Object.keys(local).length) return;
    setBusy(true);
    try {
      await createCustomer({ ...form, email: form.email.trim() });
      toast.success("Client ajouté.");
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
      <Field label="E-mail (facultatif)" error={errors.email}>
        <input type="email" value={form.email} onChange={set("email")} />
      </Field>
      <div className="modal-actions">
        <button type="button" className="btn btn-outline" onClick={onCancel}>Annuler</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Enregistrement..." : "Ajouter le client"}</button>
      </div>
    </form>
  );
}

export default function Customers() {
  const toast = useToast();
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [detailId, setDetailId] = useState(null);
  const [toggling, setToggling] = useState(null);
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useFetch(() => adminCustomers({ q, page }), [q, page]);
  const detail = useFetch(() => (detailId ? adminCustomer(detailId) : Promise.resolve(null)), [detailId]);

  const confirmToggle = async () => {
    setBusy(true);
    try {
      await setCustomerActive(toggling.id, !toggling.is_active);
      toast.success(toggling.is_active ? "Compte désactivé." : "Compte réactivé.");
    } catch (e) { toast.error(e.message); }
    finally { setBusy(false); setToggling(null); reload(); }
  };

  return (
    <>
      <div className="page-head">
        <h1>Clients</h1>
        <button className="btn btn-primary" onClick={() => setAdding(true)}>Ajouter un client</button>
      </div>
      <div className="filters"><label>Recherche<input placeholder="Nom, e-mail ou téléphone" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /></label></div>
      {loading && <Loader />}
      <ErrorMessage message={error} onRetry={reload} />
      {data && data.results.length === 0 && <EmptyState title="Aucun client" text="Aucun client ne correspond à cette recherche." />}
      {data && data.results.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Nom</th><th>E-mail</th><th>Téléphone</th><th>Inscrit le</th><th>Réservations</th><th>Compte</th><th>Actions</th></tr></thead>
            <tbody>
              {data.results.map((c) => (
                <tr key={c.id}>
                  <td data-label="Nom">{c.first_name} {c.last_name}</td>
                  <td data-label="E-mail">{c.email || "—"}</td>
                  <td data-label="Téléphone">{c.phone}</td>
                  <td data-label="Inscrit le">{formatDate(c.date_joined)}</td>
                  <td data-label="Réservations">{c.reservations_count}</td>
                  <td data-label="Compte"><span className={`badge ${c.is_active ? "badge-accepted" : "badge-cancelled"}`}>{c.is_active ? "Actif" : "Désactivé"}</span></td>
                  <td data-label="Actions" className="actions">
                    <button className="btn btn-sm btn-outline" onClick={() => setDetailId(c.id)}>Détails</button>
                    <button className={`btn btn-sm ${c.is_active ? "btn-danger" : "btn-primary"}`} onClick={() => setToggling(c)}>{c.is_active ? "Désactiver" : "Réactiver"}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pagination page={page} count={data.count} pageSize={6} onChange={setPage} />}

      <Modal open={adding} title="Ajouter un client" onClose={() => setAdding(false)}>
        {adding && <CustomerForm onCancel={() => setAdding(false)} onSaved={() => { setAdding(false); setPage(1); setQ(""); reload(); }} />}
      </Modal>
      <Modal open={!!detailId} wide title="Détails du client" onClose={() => setDetailId(null)}>
        {detail.loading && <Loader />}
        {detail.data && (
          <>
            <dl className="details">
              <dt>Nom</dt><dd>{detail.data.first_name} {detail.data.last_name}</dd>
              <dt>E-mail</dt><dd>{detail.data.email || "—"}</dd>
              <dt>Téléphone</dt><dd>{detail.data.phone}</dd>
              <dt>Inscrit le</dt><dd>{formatDate(detail.data.date_joined)}</dd>
            </dl>
            <h3>Historique des réservations</h3>
            {detail.data.reservations.length === 0 ? <p className="muted">Aucune réservation.</p> : (
              <div className="table-wrap">
                <table className="table">
                  <thead><tr><th>Référence</th><th>Chambre</th><th>Séjour</th><th>Total</th><th>Payé</th><th>Statut</th></tr></thead>
                  <tbody>
                    {detail.data.reservations.map((r) => (
                      <tr key={r.id}>
                        <td data-label="Référence">{r.reference}</td>
                        <td data-label="Chambre">{r.room.number}</td>
                        <td data-label="Séjour">{formatDate(r.check_in)} - {formatDate(r.check_out)}</td>
                        <td data-label="Total">{formatAr(r.total_amount)}</td>
                        <td data-label="Payé">{formatAr(r.amount_paid)}</td>
                        <td data-label="Statut"><StatusBadge status={r.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </Modal>
      <ConfirmDialog open={!!toggling} danger={toggling?.is_active} busy={busy}
        title={toggling?.is_active ? "Désactiver le compte" : "Réactiver le compte"}
        message={toggling ? (toggling.is_active ? `${toggling.first_name} ${toggling.last_name} ne pourra plus se connecter. L'historique des réservations est conservé.` : `${toggling.first_name} ${toggling.last_name} pourra de nouveau se connecter.`) : ""}
        confirmLabel={toggling?.is_active ? "Désactiver" : "Réactiver"} onConfirm={confirmToggle} onCancel={() => setToggling(null)} />
    </>
  );
}
