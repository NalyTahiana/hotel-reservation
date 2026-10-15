import { useState } from "react";
import { Link } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import Field from "../components/Field";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { formatDate } from "../utils/format";

export default function Account() {
  const { user, updateProfile } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({ last_name: user.last_name, first_name: user.first_name, phone: user.phone });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!/^\d{10}$/.test(form.phone)) return setErrors({ phone: "Le numéro de téléphone doit comporter exactement 10 chiffres." });
    setErrors({});
    setBusy(true);
    try {
      await updateProfile(form);
      toast.success("Vos informations ont été mises à jour.");
    } catch (err) {
      setErrors(err.fields || {});
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container narrow">
      <h1>Mon espace client</h1>
      <p className="muted">Compte créé le {formatDate(user.date_joined)} - <Link to="/compte/reservations">Voir mes réservations</Link></p>
      <form className="panel form" onSubmit={submit} noValidate>
        <h3>Mes informations</h3>
        <ErrorMessage message={error} />
        <Field label="Adresse e-mail"><input value={user.email} disabled /></Field>
        <div className="form-row">
          <Field label="Nom" error={errors.last_name}><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></Field>
          <Field label="Prénom" error={errors.first_name}><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></Field>
        </div>
        <Field label="Téléphone" error={errors.phone} hint="10 chiffres">
          <input inputMode="numeric" maxLength={10} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/\D/g, "") })} />
        </Field>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Enregistrement..." : "Enregistrer"}</button>
      </form>
    </div>
  );
}
