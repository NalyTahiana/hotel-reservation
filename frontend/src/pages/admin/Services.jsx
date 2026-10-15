import { useState } from "react";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorMessage from "../../components/ErrorMessage";
import Field from "../../components/Field";
import Loader from "../../components/Loader";
import Modal from "../../components/Modal";
import Pagination from "../../components/Pagination";
import { useToast } from "../../context/ToastContext";
import useFetch from "../../hooks/useFetch";
import { adminServices, createService, deleteService, updateService } from "../../services/admin";

const EMPTY = { kind: "service", name: "", description: "", is_active: true };

function ServiceForm({ item, onSaved, onCancel }) {
  const toast = useToast();
  const [form, setForm] = useState(item ? { ...EMPTY, ...item } : EMPTY);
  const [photo, setPhoto] = useState(null);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError(""); setErrors({});
    const fd = new FormData();
    ["kind", "name", "description"].forEach((k) => fd.append(k, form[k] ?? ""));
    fd.append("is_active", form.is_active ? "true" : "false");
    if (photo) fd.append("image", photo);
    try {
      await (item ? updateService(item.id, fd) : createService(fd));
      toast.success(item ? "Élément modifié." : "Élément ajouté.");
      onSaved();
    } catch (err) { setErrors(err.fields || {}); setError(err.message); }
    finally { setBusy(false); }
  };

  return (
    <form className="form" onSubmit={submit}>
      <ErrorMessage message={error} />
      <Field label="Catégorie" error={errors.kind}>
        <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
          <option value="service">Service</option><option value="activity">Activité</option>
        </select>
      </Field>
      <Field label="Nom" error={errors.name}><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
      <Field label="Description" error={errors.description}><textarea rows="3" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
      <Field label="Photo (facultative)" error={errors.image}><input type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files[0] || null)} /></Field>
      <label className="check"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Actif (affiché sur le site public)</label>
      <div className="modal-actions">
        <button type="button" className="btn btn-outline" onClick={onCancel}>Annuler</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Enregistrement..." : "Enregistrer"}</button>
      </div>
    </form>
  );
}

export default function Services() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useFetch(() => adminServices({ page }), [page]);

  const toggle = async (s) => {
    try {
      const fd = new FormData();
      fd.append("is_active", s.is_active ? "false" : "true");
      await updateService(s.id, fd);
      reload();
    } catch (e) { toast.error(e.message); }
  };
  const remove = async () => {
    setBusy(true);
    try { await deleteService(toDelete.id); toast.success("Élément supprimé."); }
    catch (e) { toast.error(e.message); }
    finally { setBusy(false); setToDelete(null); reload(); }
  };

  return (
    <>
      <div className="page-head">
        <h1>Services et activités</h1>
        <button className="btn btn-primary" onClick={() => setEditing("new")}>Ajouter</button>
      </div>
      {loading && <Loader />}
      <ErrorMessage message={error} onRetry={reload} />
      {data && data.results.length === 0 && <EmptyState title="Aucun service ni activité" text="Ajoutez le Wi-Fi, le restaurant, la piscine, des excursions..." />}
      {data && data.results.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Nom</th><th>Catégorie</th><th>Description</th><th>État</th><th>Actions</th></tr></thead>
            <tbody>
              {data.results.map((s) => (
                <tr key={s.id}>
                  <td data-label="Nom">{s.name}</td>
                  <td data-label="Catégorie">{s.kind_display}</td>
                  <td data-label="Description">{s.description}</td>
                  <td data-label="État"><span className={`badge ${s.is_active ? "badge-accepted" : "badge-cancelled"}`}>{s.is_active ? "Actif" : "Inactif"}</span></td>
                  <td data-label="Actions" className="actions">
                    <button className="btn btn-sm btn-outline" onClick={() => setEditing(s)}>Modifier</button>
                    <button className="btn btn-sm btn-outline" onClick={() => toggle(s)}>{s.is_active ? "Désactiver" : "Activer"}</button>
                    <button className="btn btn-sm btn-danger" onClick={() => setToDelete(s)}>Supprimer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pagination page={page} count={data.count} onChange={setPage} />}
      <Modal open={!!editing} title={editing === "new" ? "Ajouter" : "Modifier"} onClose={() => setEditing(null)}>
        {editing && <ServiceForm key={editing === "new" ? "new" : editing.id} item={editing === "new" ? null : editing} onCancel={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); }} />}
      </Modal>
      <ConfirmDialog open={!!toDelete} danger busy={busy} title="Supprimer" message={toDelete ? `Supprimer « ${toDelete.name} » ?` : ""} confirmLabel="Supprimer" onConfirm={remove} onCancel={() => setToDelete(null)} />
    </>
  );
}
