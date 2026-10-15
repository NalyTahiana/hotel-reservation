import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { HOTEL } from "../utils/hotel";
import { MenuIcon } from "./Icons";
import NotificationBell from "./NotificationBell";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();
  const close = () => setOpen(false);

  const handleLogout = async () => {
    close();
    await logout();
    navigate("/");
  };

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="brand" onClick={close}>{HOTEL.name}</Link>
        <button className="nav-toggle" aria-expanded={open} aria-label="Ouvrir le menu" onClick={() => setOpen(!open)}>
          <MenuIcon />
        </button>
        <nav className={`nav-links ${open ? "open" : ""}`}>
          <NavLink to="/" end onClick={close}>Accueil</NavLink>
          <NavLink to="/chambres" onClick={close}>Chambres</NavLink>
          <a href="/#services" onClick={close}>Services et activités</a>
          <a href="/#a-propos" onClick={close}>À propos</a>
          <a href="/#contact" onClick={close}>Contact</a>
          <Link className="btn btn-primary" to="/chambres" onClick={close}>Réserver</Link>
          {user ? (
            <>
              {isAdmin && <NavLink to="/admin" onClick={close}>Administration</NavLink>}
              <NavLink to="/compte" onClick={close}>{user.first_name}</NavLink>
              <NotificationBell onNavigate={close} />
              <button className="btn btn-outline" onClick={handleLogout}>Déconnexion</button>
            </>
          ) : (
            <NavLink className="btn btn-outline" to="/connexion" onClick={close}>Connexion</NavLink>
          )}
        </nav>
      </div>
    </header>
  );
}
