import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import PasswordInput from "../components/PasswordInput";
import Field from "../components/Field";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from;
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={from || (user.is_staff ? "/admin" : "/compte")} replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const u = await login(form.email, form.password);
      navigate(from || (u.is_staff ? "/admin" : "/compte"), { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container narrow">
      <h1>Connexion</h1>
      {from && <div className="alert alert-info">Connectez-vous pour continuer votre réservation.</div>}
      <form className="panel form" onSubmit={submit} noValidate>
        <ErrorMessage message={error} />
        <Field label="Adresse e-mail">
          <input type="email" autoComplete="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <Field label="Mot de passe">
          <PasswordInput autoComplete="current-password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </Field>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Connexion..." : "Se connecter"}</button>
        <p className="muted">Pas encore de compte ? <Link to="/inscription" state={{ from }}>Créer un compte</Link></p>
      </form>
    </div>
  );
}
