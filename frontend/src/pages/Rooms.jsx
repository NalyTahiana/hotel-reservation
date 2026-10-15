import { useSearchParams } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import Loader from "../components/Loader";
import Pagination from "../components/Pagination";
import RoomCard from "../components/RoomCard";
import useFetch from "../hooks/useFetch";
import { listRooms } from "../services/rooms";
import { addDaysISO, ROOM_TYPES, todayISO } from "../utils/format";

export default function Rooms() {
  const [params, setParams] = useSearchParams();
  const p = Object.fromEntries(params.entries());
  const page = Number(p.page || 1);
  const { data, loading, error, reload } = useFetch(
    () => listRooms({ check_in: p.check_in, check_out: p.check_out, guests: p.guests, room_type: p.room_type, page }),
    [params.toString()]
  );
  const update = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    if (key !== "page") next.delete("page");
    setParams(next);
  };
  const search = { check_in: p.check_in, check_out: p.check_out, guests: p.guests };
  const cleanSearch = Object.fromEntries(Object.entries(search).filter(([, v]) => v));
  const invalidDates = p.check_in && p.check_out && p.check_in >= p.check_out;

  return (
    <div className="container">
      <h1>Nos chambres</h1>
      <div className="filters">
        <label>Arrivée<input type="date" min={todayISO()} value={p.check_in || ""} onChange={(e) => update("check_in", e.target.value)} /></label>
        <label>Départ<input type="date" min={p.check_in ? addDaysISO(p.check_in, 1) : todayISO()} value={p.check_out || ""} onChange={(e) => update("check_out", e.target.value)} /></label>
        <label>Personnes<input type="number" min="1" value={p.guests || ""} onChange={(e) => update("guests", e.target.value)} /></label>
        <label>Type
          <select value={p.room_type || ""} onChange={(e) => update("room_type", e.target.value)}>
            <option value="">Tous</option>
            {Object.entries(ROOM_TYPES).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <button className="btn btn-outline" onClick={() => setParams({})}>Réinitialiser</button>
      </div>
      {invalidDates && <div className="alert alert-error">La date d'arrivée doit être antérieure à la date de départ.</div>}
      {p.check_in && p.check_out && !invalidDates && <p className="muted">Chambres disponibles pour la période choisie.</p>}
      {loading && <Loader />}
      <ErrorMessage message={error} onRetry={reload} />
      {data && data.results.length === 0 && (
        <EmptyState title="Aucune chambre disponible" text="Essayez d'autres dates, un autre type de chambre ou un nombre de personnes différent." />
      )}
      <div className="grid grid-3">
        {data?.results.map((r) => <RoomCard key={r.id} room={r} search={cleanSearch} />)}
      </div>
      {data && <Pagination page={page} count={data.count} pageSize={6} onChange={(n) => update("page", String(n))} />}
    </div>
  );
}
