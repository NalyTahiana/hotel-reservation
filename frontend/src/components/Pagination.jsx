
const SIBLINGS = 1; 

export function pageItems(page, pages) {
  // Peu de pages : on les affiche toutes.
  if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);

  const start = Math.max(2, Math.min(page - SIBLINGS, pages - 4));
  const end = Math.min(pages - 1, Math.max(page + SIBLINGS, 5));
  const items = [1];
  if (start > 2) items.push("gap-start");
  for (let n = start; n <= end; n++) items.push(n);
  if (end < pages - 1) items.push("gap-end");
  items.push(pages);
  return items;
}

export default function Pagination({ page, count, pageSize = 10, onChange }) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  if (pages <= 1) return null;
  const current = Math.min(Math.max(1, page), pages);
  const go = (n) => { if (n >= 1 && n <= pages && n !== current) onChange(n); };

  return (
    <nav className="pagination" aria-label="Pagination">
      <button type="button" className="page-btn page-nav" disabled={current <= 1} onClick={() => go(current - 1)}>
        Précédent
      </button>
      <ul className="page-list">
        {pageItems(current, pages).map((item) =>
          typeof item === "number" ? (
            <li key={item}>
              <button
                type="button"
                className={`page-btn${item === current ? " active" : ""}`}
                aria-label={`Page ${item}`}
                aria-current={item === current ? "page" : undefined}
                onClick={() => go(item)}
              >
                {item}
              </button>
            </li>
          ) : (
            <li key={item} className="page-gap" aria-hidden="true">…</li>
          )
        )}
      </ul>
      <button type="button" className="page-btn page-nav" disabled={current >= pages} onClick={() => go(current + 1)}>
        Suivant
      </button>
    </nav>
  );
}