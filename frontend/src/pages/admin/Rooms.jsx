import { useState } from "react";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorMessage from "../../components/ErrorMessage";
import Field from "../../components/Field";
import Loader from "../../components/Loader";
import Modal from "../../components/Modal";
import Pagination from "../../components/Pagination";
import SafeImage from "../../components/SafeImage";
import { useToast } from "../../context/ToastContext";
import useFetch from "../../hooks/useFetch";
import { addRoomImages, adminRooms, createRoom, deleteRoom, deleteRoomImage, updateRoom } from "../../services/admin";
import { formatAr, ROOM_TYPES } from "../../utils/format";

const EMPTY = { number: "", name: "", room_type: "double", short_description: "", description: "", capacity: 2, price_per_night: "", amenities: "", included_services: "", is_active: true };

function RoomForm({ room, onSaved, onCancel }) {
  const toast = useToast();
  const [form, setForm] = useState(room ? { ...EMPTY, ...room } : EMPTY);
  const [photo, setPhoto] = useState(null);
  const [gallery, setGallery] = useState([]);
  const [images, setImages] = useState(room?.images || []);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setErrors({}); setBusy(true);
    const fd = new FormData();
    ["number", "name", "room_type", "short_description", "description", "capacity", "price_per_night", "amenities", "included_services"].forEach((k) => fd.append(k, form[k] ?? ""));
    fd.append("is_active", form.is_active ? "true" : "false");
    if (photo) fd.append("image", photo);
    try {
      const saved = room ? await updateRoom(room.id, fd) : await createRoom(fd);
      if (gallery.length) {
        const g = new FormData();
        gallery.forEach((f) => g.append("images", f));
        await addRoomImages(saved.id, g);
      }
      toast.success(room ? "Chambre modifiée." : "Chambre ajoutée.");
      onSaved();
    } catch (err) {
      setErrors(err.fields || {}); setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const removeImage = async (img) => {
    try {
      await deleteRoomImage(room.id, img.id);
      setImages(images.filter((i) => i.id !== img.id));
    } catch (err) { toast.error(err.message); }
  };

  return (
    <form className="form" onSubmit={submit}>
      <ErrorMessage message={error} />
      <div className="form-row">
        <Field label="Numéro" error={errors.number}><input required value={form.number} onChange={set("number")} /></Field>
        <Field label="Nom" error={errors.name}><input required value={form.name} onChange={set("name")} /></Field>
      </div>
      <div className="form-row">
        <Field label="Type" error={errors.room_type}>
          <select value={form.room_type} onChange={set("room_type")}>{Object.entries(ROOM_TYPES).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
        </Field>
        <Field label="Capacité maximale" error={errors.capacity}><input type="number" min="1" required value={form.capacity} onChange={set("capacity")} /></Field>
        <Field label="Prix par nuit (Ar)" error={errors.price_per_night}><input type="number" min="1" required value={form.price_per_night} onChange={set("price_per_night")} /></Field>
      </div>
      <Field label="Description courte" error={errors.short_description}><input maxLength={255} value={form.short_description} onChange={set("short_description")} /></Field>
      <Field label="Description complète" error={errors.description}><textarea rows="3" value={form.description} onChange={set("description")} /></Field>
      <div className="form-row">
        <Field label="Équipements (un par ligne)" error={errors.amenities}><textarea rows="4" value={form.amenities} onChange={set("amenities")} /></Field>
        <Field label="Services inclus (un par ligne)" error={errors.included_services}><textarea rows="4" value={form.included_services} onChange={set("included_services")} /></Field>
      </div>
      <Field label="Photo principale" error={errors.image}><input type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files[0] || null)} /></Field>
      <Field label="Photos supplémentaires (galerie)"><input type="file" accept="image/*" multiple onChange={(e) => setGallery([...e.target.files])} /></Field>
      {images.length > 0 && (
        <div className="thumbs">
          {images.map((img) => (
            <div key={img.id} className="thumb-edit">
              <SafeImage src={img.image} alt="" />
              <button type="button" className="btn btn-sm btn-danger" onClick={() => removeImage(img)}>Retirer</button>
            </div>
          ))}
        </div>
      )}
      <label className="check"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Chambre active (visible et réservable)</label>
      <div className="modal-actions">
        <button type="button" className="btn btn-outline" onClick={onCancel}>Annuler</button>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Enregistrement..." : "Enregistrer"}</button>
      </div>
    </form>
  );
}

export default function Rooms() {
  const toast = useToast();
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [busy, setBusy] = useState(false);
  const { data, loading, error, reload } = useFetch(() => adminRooms({ q, page }), [q, page]);

  const toggle = async (room) => {
    try {
      const fd = new FormData();
      fd.append("is_active", room.is_active ? "false" : "true");
      await updateRoom(room.id, fd);
      toast.success(room.is_active ? "Chambre désactivée." : "Chambre activée.");
      reload();
    } catch (e) { toast.error(e.message); }
  };
  const remove = async () => {
    setBusy(true);
    try { await deleteRoom(toDelete.id); toast.success("Chambre supprimée."); }
    catch (e) { toast.error(e.message); }
    finally { setBusy(false); setToDelete(null); reload(); }
  };

  return (
    <>
      <div className="page-head">
        <h1>Chambres</h1>
        <button className="btn btn-primary" onClick={() => setEditing("new")}>Ajouter une chambre</button>
      </div>
      <div className="filters"><label>Recherche<input placeholder="Nom ou numéro" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /></label></div>
      {loading && <Loader />}
      <ErrorMessage message={error} onRetry={reload} />
      {data && data.results.length === 0 && <EmptyState title="Aucune chambre" text="Ajoutez votre première chambre pour l'afficher sur le site public." />}
      {data && data.results.length > 0 && (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Photo</th><th>Numéro</th><th>Nom</th><th>Type</th><th>Capacité</th><th>Prix / nuit</th><th>État</th><th>Actions</th></tr></thead>
            <tbody>
              {data.results.map((r) => (
                <tr key={r.id}>
                  <td data-label="Photo"><SafeImage src={r.image} alt="" className="thumb" /></td>
                  <td data-label="Numéro">{r.number}</td>
                  <td data-label="Nom">{r.name}</td>
                  <td data-label="Type">{ROOM_TYPES[r.room_type]}</td>
                  <td data-label="Capacité">{r.capacity}</td>
                  <td data-label="Prix / nuit">{formatAr(r.price_per_night)}</td>
                  <td data-label="État"><span className={`badge ${r.is_active ? "badge-accepted" : "badge-cancelled"}`}>{r.is_active ? "Active" : "Inactive"}</span></td>
                  <td data-label="Actions" className="actions">
                    <button className="btn btn-sm btn-outline" onClick={() => setEditing(r)}>Modifier</button>
                    <button className="btn btn-sm btn-outline" onClick={() => toggle(r)}>{r.is_active ? "Désactiver" : "Activer"}</button>
                    <button className="btn btn-sm btn-danger" onClick={() => setToDelete(r)}>Supprimer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pagination page={page} count={data.count} pageSize={6} onChange={setPage} />}
      <Modal open={!!editing} wide title={editing === "new" ? "Ajouter une chambre" : "Modifier la chambre"} onClose={() => setEditing(null)}>
        {editing && <RoomForm key={editing === "new" ? "new" : editing.id} room={editing === "new" ? null : editing} onCancel={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); }} />}
      </Modal>
      <ConfirmDialog open={!!toDelete} danger busy={busy} title="Supprimer la chambre"
        message={toDelete ? `Supprimer la chambre ${toDelete.number} ? Impossible si elle a un historique de réservations (désactivez-la alors).` : ""}
        confirmLabel="Supprimer" onConfirm={remove} onCancel={() => setToDelete(null)} />
    </>
  );
}
