import { Link } from "react-router-dom";
import { formatAr, ROOM_TYPES } from "../utils/format";
import SafeImage from "./SafeImage";

export default function RoomCard({ room, search }) {
  const qs = search ? `?${new URLSearchParams(search)}` : "";
  return (
    <article className="card room-card">
      <SafeImage src={room.image} alt={room.name} className="room-card-img" />
      <div className="card-body">
        <div className="room-card-head">
          <h3>{room.name}</h3>
          <span className="tag">{ROOM_TYPES[room.room_type] || room.room_type}</span>
        </div>
        <p className="muted">Jusqu'à {room.capacity} personne(s)</p>
        <p>{room.short_description}</p>
        {room.amenities_list?.length > 0 && (
          <ul className="chips">
            {room.amenities_list.slice(0, 4).map((a) => <li key={a}>{a}</li>)}
          </ul>
        )}
        <p className="price"><strong>{formatAr(room.price_per_night)}</strong> <span className="muted">/ nuit</span></p>
        <div className="card-actions">
          <Link className="btn btn-outline" to={`/chambres/${room.id}${qs}`}>Voir les détails</Link>
          <Link className="btn btn-primary" to={`/reservation/${room.id}${qs}`}>Réserver</Link>
        </div>
      </div>
    </article>
  );
}
