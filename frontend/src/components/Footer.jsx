import { Link } from "react-router-dom";
import { HOTEL } from "../utils/hotel";

export default function Footer() {
  return (
    <footer className="footer" id="contact">
      <div className="container footer-grid">
        <div>
          <h4>{HOTEL.name}</h4>
          <p>{HOTEL.tagline}</p>
        </div>
        <div>
          <h4>Coordonnées</h4>
          <p>{HOTEL.address}</p>
          <p>Téléphone : {HOTEL.phone}</p>
          <p>E-mail : {HOTEL.email}</p>
          <p>{HOTEL.hours}</p>
        </div>
        <div>
          <h4>Liens utiles</h4>
          <p><Link to="/chambres">Nos chambres</Link></p>
          <p><Link to="/compte/reservations">Mes réservations</Link></p>
          <p><Link to="/connexion">Connexion</Link></p>
        </div>
      </div>
      <div className="container footer-bottom">© {new Date().getFullYear()} {HOTEL.name}. Tous droits réservés.</div>
    </footer>
  );
}
