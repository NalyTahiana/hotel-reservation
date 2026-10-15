import BarChart from "../../components/BarChart";
import ErrorMessage from "../../components/ErrorMessage";
import Loader from "../../components/Loader";
import useFetch from "../../hooks/useFetch";
import { getStats } from "../../services/admin";
import { formatAr } from "../../utils/format";

const Card = ({ label, value, note }) => (
  <div className="stat">
    <span className="stat-label">{label}</span>
    <strong className="stat-value">{value}</strong>
    {note && <span className="muted">{note}</span>}
  </div>
);

export default function Dashboard() {
  const { data: s, loading, error, reload } = useFetch(getStats, []);
  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} onRetry={reload} />;
  return (
    <>
      <h1>Tableau de bord</h1>
      <div className="stats">
        <Card label="Chambres" value={s.total_rooms} note={`${s.active_rooms} active(s)`} />
        <Card label="Chambres disponibles" value={s.available_rooms} note="actives et libres aujourd'hui" />
        <Card label="Chambres occupées" value={s.occupied_rooms} note="séjour en cours aujourd'hui" />
        <Card label="Clients inscrits" value={s.customers} />
        <Card label="Réservations en attente" value={s.pending} />
        <Card label="Réservations acceptées" value={s.accepted} />
        <Card label="Réservations refusées" value={s.refused} />
        <Card label="Chiffre d'affaires" value={formatAr(s.revenue)} note="séjours terminés uniquement" />
      </div>
      <div className="grid grid-2">
        <div className="panel"><BarChart title="Réservations par mois d'arrivée (hors refusées et annulées)" data={s.monthly} valueKey="count" /></div>
        <div className="panel"><BarChart title="Revenus par mois d'arrivée (séjours terminés)" data={s.monthly} valueKey="revenue" format={(v) => (v >= 1000 ? `${Math.round(v / 1000)} k` : v)} /></div>
      </div>
    </>
  );
}
