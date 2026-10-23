import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { MenuIcon } from "../components/Icons";
import NotificationBell from "../components/NotificationBell";
import { HOTEL } from "../utils/hotel";

const LINKS = [
  ["/admin", "Tableau de bord", true],
  ["/admin/reservations", "Réservations"],
  ["/admin/chambres", "Chambres"],
  ["/admin/clients", "Clients"],
  ["/admin/services", "Services et activités"],
  ["/admin/a-propos", "À propos"],
];

export default function AdminLayout() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="admin">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-brand">{HOTEL.name}</div>
        <nav>
          {LINKS.map(([to, label, end]) => (
            <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)}>{label}</NavLink>
          ))}
        </nav>
        <Link className="sidebar-site" to="/">Voir le site public</Link>
      </aside>
      <div className="admin-main">
        <div className="topbar">
          <button className="nav-toggle" onClick={() => setOpen(!open)} aria-label="Menu"><MenuIcon /></button>
          <strong>Administration</strong>
          <div className="topbar-user">
            <span>{user?.first_name} {user?.last_name}</span>
            <NotificationBell />
            <button className="btn btn-sm btn-outline" onClick={async () => { await logout(); navigate("/connexion"); }}>
              Déconnexion
            </button>
          </div>
        </div>
        <div className="admin-content"><Outlet /></div>
      </div>
    </div>
  );
}
