export const formatAr = (n) => `${new Intl.NumberFormat("fr-FR").format(Number(n || 0))} Ar`;

export const formatDate = (iso) => {
  if (!iso) return "";
  const [y, m, d] = String(iso).slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" });
};

export const formatDateTime = (iso) =>
  iso ? new Date(iso).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" }) : "";

const toISO = (date) => new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
export const todayISO = () => toISO(new Date());
export const addDaysISO = (iso, days) => {
  const [y, m, d] = iso.split("-").map(Number);
  return toISO(new Date(y, m - 1, d + days));
};

export const nightsBetween = (a, b) => {
  if (!a || !b) return 0;
  const diff = (new Date(b) - new Date(a)) / 86400000;
  return diff > 0 ? Math.round(diff) : 0;
};

export const STATUS_LABELS = {
  pending: "En attente",
  accepted: "Acceptée",
  refused: "Refusée",
  cancelled: "Annulée",
  completed: "Terminée",
};
export const ROOM_TYPES = { simple: "Simple", double: "Double", familiale: "Familiale", suite: "Suite" };
