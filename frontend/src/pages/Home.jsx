import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import Loader from "../components/Loader";
import RoomCard from "../components/RoomCard";
import SafeImage from "../components/SafeImage";
import useFetch from "../hooks/useFetch";
import { listCatalog, listRooms } from "../services/rooms";
import { addDaysISO, todayISO } from "../utils/format";
import { HOTEL } from "../utils/hotel";

function SearchForm() {
  const navigate = useNavigate();
  const [f, setF] = useState({ check_in: "", check_out: "", guests: 2 });
  const [error, setError] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    if (!f.check_in || !f.check_out) return setError("Choisissez une date d'arrivée et une date de départ.");
    if (f.check_in >= f.check_out) return setError("La date d'arrivée doit être antérieure à la date de départ.");
    navigate(`/chambres?${new URLSearchParams(f)}`);
  };

  return (
    <form className="search-form" onSubmit={submit}>
      <label>Arrivée<input type="date" min={todayISO()} value={f.check_in} onChange={set("check_in")} /></label>
      <label>Départ<input type="date" min={f.check_in ? addDaysISO(f.check_in, 1) : todayISO()} value={f.check_out} onChange={set("check_out")} /></label>
      <label>Personnes<input type="number" min="1" max="12" value={f.guests} onChange={set("guests")} /></label>
      <button className="btn btn-primary" type="submit">Rechercher</button>
      {error && <p className="field-error search-error">{error}</p>}
    </form>
  );
}

function CatalogSection({ id, title, kind }) {
  const { data, loading, error, reload } = useFetch(() => listCatalog(kind), [kind]);
  return (
    <section className="section" id={id}>
      <div className="container">
        <h2>{title}</h2>
        {loading && <Loader />}
        <ErrorMessage message={error} onRetry={reload} />
        {data && data.length === 0 && <EmptyState title="Aucun élément pour le moment" text="L'hôtel n'a pas encore publié cette rubrique." />}
        <div className="grid grid-3">
          {data?.map((s) => (
            <article className="card" key={s.id}>
              {s.image && <SafeImage src={s.image} alt={s.name} className="card-img-sm" />}
              <div className="card-body"><h3>{s.name}</h3><p>{s.description}</p></div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const rooms = useFetch(() => listRooms({ page: 1 }), []);
  return (
    <>
      <section className="hero">
        <SafeImage src={HOTEL.heroImage} alt={HOTEL.name} className="hero-img" />
        <div className="hero-overlay">
          <div className="container hero-content">
            <h1>{HOTEL.name}</h1>
            <p>{HOTEL.tagline}</p>
            <Link className="btn btn-primary btn-lg" to="/chambres">Découvrir nos chambres</Link>
            <SearchForm />
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>Nos chambres</h2>
          {rooms.loading && <Loader />}
          <ErrorMessage message={rooms.error} onRetry={rooms.reload} />
          {rooms.data && rooms.data.results.length === 0 && (
            <EmptyState title="Aucune chambre publiée" text="Les chambres apparaîtront ici dès que l'administrateur les aura ajoutées." />
          )}
          <div className="grid grid-3">
            {rooms.data?.results.slice(0, 3).map((r) => <RoomCard key={r.id} room={r} />)}
          </div>
          {rooms.data?.count > 3 && <p className="center section-cta"><Link className="btn btn-outline" to="/chambres">Voir toutes les chambres</Link></p>}
        </div>
      </section>

      <CatalogSection id="services" title="Services" kind="service" />
      <CatalogSection id="activites" title="Activités" kind="activity" />

      <section className="section alt" id="a-propos">
        <div className="container two-col">
          <div>
            <h2>À propos de l'hôtel</h2>
            <p>{HOTEL.about}</p>
          </div>
          <div className="gallery">
            {HOTEL.galleryImages.map((src) => <SafeImage key={src} src={src} alt="Photo de l'hôtel" />)}
          </div>
        </div>
      </section>
    </>
  );
}
