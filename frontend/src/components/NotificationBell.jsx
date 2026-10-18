import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { BellIcon } from "./Icons";
import { useToast } from "../context/ToastContext";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "../services/notifications";
import { formatDateTime } from "../utils/format";

const POLL_MS = 30000;

export default function NotificationBell({ onNavigate }) {
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [data, setData] = useState({ unread_count: 0, results: [] });
  const [open, setOpen] = useState(false);
  const seen = useRef(null);
  const box = useRef(null);

  const load = useCallback(async () => {
    try {
      const d = await listNotifications();
      setData(d);
      const ids = new Set(d.results.map((n) => n.id));
      if (seen.current) {
        d.results.filter((n) => !n.is_read && !seen.current.has(n.id)).forEach((n) => toast.success(`${n.title} : ${n.message}`));
      }
      seen.current = ids;
    } catch {
    }
  }, [toast]);

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_MS);
    const onFocus = () => load();
    window.addEventListener("focus", onFocus);
    return () => { clearInterval(timer); window.removeEventListener("focus", onFocus); };
  }, [load]);

  useEffect(() => {
    const close = (e) => { if (box.current && !box.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const target = user?.is_staff ? "/admin/reservations" : "/compte/reservations";

  const openOne = async (n) => {
    if (!n.is_read) {
      try { await markNotificationRead(n.id); } catch { }
      setData((d) => ({ unread_count: Math.max(0, d.unread_count - 1), results: d.results.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)) }));
    }
    setOpen(false);
    onNavigate?.();
    navigate(target);
  };

  const readAll = async () => {
    try {
      await markAllNotificationsRead();
      setData((d) => ({ unread_count: 0, results: d.results.map((x) => ({ ...x, is_read: true })) }));
    } catch { }
  };

  return (
    <div className="bell" ref={box}>
      <button className="btn btn-outline bell-btn icon-btn" title="Notifications" aria-label={`Notifications (${data.unread_count} non lue(s))`} aria-expanded={open} onClick={() => { setOpen(!open); if (!open) load(); }}>
        <BellIcon />
        {data.unread_count > 0 && <span className="bell-count">{data.unread_count > 99 ? "99+" : data.unread_count}</span>}
      </button>
      {open && (
        <div className="bell-panel" role="dialog" aria-label="Notifications">
          <div className="bell-head">
            <strong>Notifications</strong>
            {data.unread_count > 0 && <button className="btn btn-sm btn-outline" onClick={readAll}>Tout marquer comme lu</button>}
          </div>
          {data.results.length === 0 ? (
            <p className="muted bell-empty">Aucune notification pour le moment.</p>
          ) : (
            <ul className="bell-list">
              {data.results.map((n) => (
                <li key={n.id}>
                  <button className={`bell-item ${n.is_read ? "" : "unread"}`} onClick={() => openOne(n)}>
                    <span className="bell-title">{n.title}</span>
                    <span className="bell-msg">{n.message}</span>
                    <span className="muted bell-date">{formatDateTime(n.created_at)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
