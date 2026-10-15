// pageSize doit être identique à la pagination du serveur (10 par défaut, 6 pour Chambres et Clients).
export default function Pagination({ page, count, pageSize = 10, onChange }) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  if (pages <= 1) return null;
  return (
    <nav className="pagination" aria-label="Pagination">
      <button className="btn btn-sm btn-outline" disabled={page <= 1} onClick={() => onChange(page - 1)}>Précédent</button>
      <span>Page {page} sur {pages} ({count} éléments)</span>
      <button className="btn btn-sm btn-outline" disabled={page >= pages} onClick={() => onChange(page + 1)}>Suivant</button>
    </nav>
  );
}
