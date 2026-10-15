import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import Field from "../components/Field";
import Loader from "../components/Loader";
import SafeImage from "../components/SafeImage";
import { useAuth } from "../context/AuthContext";
import useFetch from "../hooks/useFetch";
import { createReservation } from "../services/reservations";
import { getRoom } from "../services/rooms";
import { addDaysISO, formatAr, formatDate, nightsBetween, todayISO } from "../utils/format";

export default function Booking() {
  const { roomId } = useParams();
  const [params] = useSearchParams();
  const { user } = useAuth();
  const [form, setForm] = useState({
    check_in: params.get("check_in") || "",
    check_out: params.get("check_out") || "",
    guests: params.get("guests") || 1,
    comment: "",
  });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);

  const { data: room, loading, error: loadError, reload } = useFetch(() => getRoom(roomId), [roomId]);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  if (loading) return <div className="container"><Loader /></div>;
  if (loadError) return <div className="container"><ErrorMessage message={loadError} onRetry={reload} /><Link to="/chambres">Retour aux chambres</Link></div>;

  const nights = nightsBetween(form.check_in, form.check_out);
  const total = nights * room.price_per_night;

  if (done) {
    return (
      <div className="container narrow">
        <div className="panel center">
          <h1>Demande envoyée</h1>
          <p>Votre demande de réservation <strong>{done.reference}</strong> a bien été enregistrée avec le statut « En attente ».</p>
          <p>Elle sera examinée par l'hôtel. Vous pouvez suivre son statut dans votre espace client.</p>
          <p className="price">Montant : <strong>{formatAr(done.total_amount)}</strong> pour {done.nights} nuit(s)</p>
          <Link className="btn btn-primary" to="/compte/reservations">Voir mes réservations</Link>
        </div>
      </div>
    );
  }

  const validate = () => {
    const e = {};
    if (!form.check_in) e.check_in = "Choisissez la date d'arrivée.";
    else if (form.check_in < todayISO()) e.check_in = "La date d'arrivée ne peut pas être dans le passé.";
    if (!form.check_out) e.check_out = "Choisissez la date de départ.";
    else if (form.check_in && form.check_out <= form.check_in) e.check_out = "La date de départ doit être postérieure à la date d'arrivée.";
    if (!form.guests || Number(form.guests) < 1) e.guests = "Indiquez au moins une personne.";
    else if (Number(form.guests) > room.capacity) e.guests = `Cette chambre accueille au maximum ${room.capacity} personne(s).`;
    return e;
  };

  const submit = async (ev) => {
    ev.preventDefault();
    setError(""); setConflict(false);
    const local = validate();
    setErrors(local);
    if (Object.keys(local).length) return;
    setBusy(true);
    try {
      setDone(await createReservation({ room: room.id, check_in: form.check_in, check_out: form.check_out, guests: Number(form.guests), comment: form.comment }));
    } catch (err) {
      setErrors(err.fields || {});
      setError(err.message);
      setConflict(err.status === 409);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <h1>Réserver : {room.name}</h1>
      <div className="two-col">
        <form className="panel form" onSubmit={submit} noValidate>
          <ErrorMessage message={error} />
          {conflict && <p>Vous pouvez <Link to="/chambres">choisir une autre chambre</Link> ou modifier vos dates ci-dessous.</p>}
          <div className="form-row">
            <Field label="Date d'arrivée" error={errors.check_in}><input type="date" min={todayISO()} value={form.check_in} onChange={set("check_in")} /></Field>
            <Field label="Date de départ" error={errors.check_out}><input type="date" min={form.check_in ? addDaysISO(form.check_in, 1) : todayISO()} value={form.check_out} onChange={set("check_out")} /></Field>
          </div>
          <Field label={`Nombre de personnes (maximum ${room.capacity})`} error={errors.guests}>
            <input type="number" min="1" max={room.capacity} value={form.guests} onChange={set("guests")} />
          </Field>
          <div className="readonly">
            <p><strong>Client :</strong> {user.first_name} {user.last_name}</p>
            <p><strong>E-mail :</strong> {user.email} - <strong>Téléphone :</strong> {user.phone}</p>
            <p className="muted">Ces informations proviennent de votre compte. <Link to="/compte">Les modifier</Link></p>
          </div>
          <Field label="Commentaire (facultatif)" error={errors.comment}><textarea rows="3" maxLength={1000} value={form.comment} onChange={set("comment")} /></Field>
          <button className="btn btn-primary" disabled={busy}>{busy ? "Envoi..." : "Envoyer la demande de réservation"}</button>
        </form>

        <aside className="panel summary">
          <SafeImage src={room.image} alt={room.name} className="detail-img" />
          <h3>Récapitulatif</h3>
          <dl>
            <dt>Chambre</dt><dd>{room.number} - {room.name}</dd>
            <dt>Séjour</dt><dd>{nights > 0 ? `${formatDate(form.check_in)} au ${formatDate(form.check_out)}` : "Dates à choisir"}</dd>
            <dt>Prix par nuit</dt><dd>{formatAr(room.price_per_night)}</dd>
            <dt>Nombre de nuits</dt><dd>{nights}</dd>
            <dt>Montant total</dt><dd><strong>{formatAr(total)}</strong></dd>
          </dl>
          <p className="muted">Le montant définitif est recalculé par le serveur lors de l'enregistrement.</p>
        </aside>
      </div>
    </div>
  );
}
