import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import Loader from "../components/Loader";
import SafeImage from "../components/SafeImage";
import useFetch from "../hooks/useFetch";
import { getRoom } from "../services/rooms";
import { addDaysISO, formatAr, nightsBetween, ROOM_TYPES, todayISO } from "../utils/format";

export default function RoomDetail() {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const checkIn = params.get("check_in") || "";
  const checkOut = params.get("check_out") || "";
  const datesOk = checkIn && checkOut && checkIn < checkOut;
  const { data: room, loading, error, reload } = useFetch(
    () => getRoom(id, datesOk ? { check_in: checkIn, check_out: checkOut } : {}),
    [id, checkIn, checkOut]
  );
  const [selected, setSelected] = useState(0);

  const setDate = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next, { replace: true });
  };

  if (loading && !room) return <div className="container"><Loader /></div>;
  if (error) return <div className="container"><ErrorMessage message={error} onRetry={reload} /><Link to="/chambres">Retour aux chambres</Link></div>;
  if (!room) return null;

  const photos = [room.image, ...room.images.map((i) => i.image)].filter(Boolean);
  const gallery = photos.length ? photos : [null];
  const nights = nightsBetween(checkIn, checkOut);
  const bookingQs = new URLSearchParams(Object.fromEntries([...params.entries()].filter(([, v]) => v))).toString();

  return (
    <div className="container">
      <p><Link to="/chambres">&larr; Retour aux chambres</Link></p>
      <div className="two-col room-detail">
        <div>
          <SafeImage src={gallery[selected]} alt={room.name} className="detail-img" />
          {gallery.length > 1 && (
            <div className="thumbs">
              {gallery.map((src, i) => (
                <button key={src} className={i === selected ? "active" : ""} onClick={() => setSelected(i)} aria-label={`Photo ${i + 1}`}>
                  <SafeImage src={src} alt="" />
                </button>
              ))}
            </div>
          )}
        </div>
        <div>
          <span className="tag">{ROOM_TYPES[room.room_type]}</span>
          <h1>{room.name}</h1>
          <p className="muted">Chambre {room.number} - jusqu'à {room.capacity} personne(s)</p>
          <p className="price"><strong>{formatAr(room.price_per_night)}</strong> <span className="muted">/ nuit</span></p>
          <p>{room.description || room.short_description}</p>

          {room.amenities_list.length > 0 && (<><h3>Équipements</h3><ul className="chips">{room.amenities_list.map((a) => <li key={a}>{a}</li>)}</ul></>)}
          {room.services_list.length > 0 && (<><h3>Services inclus</h3><ul className="chips">{room.services_list.map((a) => <li key={a}>{a}</li>)}</ul></>)}

          <div className="panel">
            <h3>Disponibilité</h3>
            <div className="filters">
              <label>Arrivée<input type="date" min={todayISO()} value={checkIn} onChange={(e) => setDate("check_in", e.target.value)} /></label>
              <label>Départ<input type="date" min={checkIn ? addDaysISO(checkIn, 1) : todayISO()} value={checkOut} onChange={(e) => setDate("check_out", e.target.value)} /></label>
            </div>
            {!datesOk && <p className="muted">Choisissez vos dates pour vérifier la disponibilité.</p>}
            {datesOk && room.available === true && (
              <p className="text-ok">Disponible pour {nights} nuit(s) : {formatAr(nights * room.price_per_night)}</p>
            )}
            {datesOk && room.available === false && (
              <p className="text-danger">Cette chambre n'est pas disponible à ces dates. Essayez d'autres dates ou <Link to="/chambres">une autre chambre</Link>.</p>
            )}
            <Link className="btn btn-primary" to={`/reservation/${room.id}${bookingQs ? `?${bookingQs}` : ""}`}>Réserver cette chambre</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
