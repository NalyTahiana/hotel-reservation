import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import Field from "../components/Field";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";

const EMPTY = { last_name: "", first_name: "", email: "", phone: "", password: "", password_confirm: "" };

function validate(f) {
  const e = {};
  if (!f.last_name.trim()) e.last_name = "Le nom est obligatoire.";
  if (!f.first_name.trim()) e.first_name = "Le prénom est obligatoire.";
  if (!/^\S+@\S+\.\S+$/.test(f.email)) e.email = "Saisissez une adresse e-mail valide.";
  if (!/^\d{10}$/.test(f.phone)) e.phone = "Le numéro de téléphone doit comporter exactement 10 chiffres.";
  if (f.password.length < 8) e.password = "Le mot de passe doit contenir au moins 8 caractères.";
  if (f.password !== f.password_confirm) e.password_confirm = "Les mots de passe ne correspondent pas.";
  return e;
}

export default function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const from = useLocation().state?.from;
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={from || "/compte"} replace />;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    const local = validate(form);
    setErrors(local);
    if (Object.keys(local).length) return;
    setBusy(true);
    try {
      await register(form);
      navigate(from || "/compte", { replace: true });
    } catch (err) {
      setErrors(err.fields || {}); // erreurs renvoyées par Django (e-mail déjà utilisé, mot de passe trop simple...)
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container narrow">
      <h1>Créer un compte</h1>
      <form className="panel form" onSubmit={submit} noValidate>
        <ErrorMessage message={error} />
        <div className="form-row">
          <Field label="Nom" error={errors.last_name}><input value={form.last_name} onChange={set("last_name")} autoComplete="family-name" /></Field>
          <Field label="Prénom" error={errors.first_name}><input value={form.first_name} onChange={set("first_name")} autoComplete="given-name" /></Field>
        </div>
        <Field label="Adresse e-mail" error={errors.email}><input type="email" value={form.email} onChange={set("email")} autoComplete="email" /></Field>
        <Field label="Téléphone" error={errors.phone} hint="10 chiffres, sans espaces">
          <input inputMode="numeric" maxLength={10} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/\D/g, "") })} autoComplete="tel" />
        </Field>
        <Field label="Mot de passe" error={errors.password}><PasswordInput value={form.password} onChange={set("password")} autoComplete="new-password" /></Field>
        <Field label="Confirmation du mot de passe" error={errors.password_confirm}><PasswordInput value={form.password_confirm} onChange={set("password_confirm")} autoComplete="new-password" /></Field>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Création..." : "Créer mon compte"}</button>
        <p className="muted">Déjà inscrit ? <Link to="/connexion" state={{ from }}>Se connecter</Link></p>
      </form>
    </div>
  );
}
