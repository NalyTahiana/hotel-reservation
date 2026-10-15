import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="container center page-empty">
      <h1>Page introuvable</h1>
      <p>La page demandée n'existe pas ou a été déplacée.</p>
      <Link className="btn btn-primary" to="/">Retour à l'accueil</Link>
    </div>
  );
}
