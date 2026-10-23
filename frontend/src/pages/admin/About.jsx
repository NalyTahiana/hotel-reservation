import { useState } from "react";
import { HOTEL } from "../../utils/hotel";

const MPD_PDF = "/docs/MPD_hotel_vahiny_francais.pdf";

// Colonnes : [propriété, nom technique, type, clé, contraintes / remarques]
const MPD_TABLES = [
  {
    num: "1", label: "Utilisateur", name: "hotel_user",
    desc: "Utilisateurs : clients, personnel et administrateurs.",
    cols: [
      ["identifiant", "id", "BIGINT", "PK", "Auto-incrémenté"],
      ["adresse e-mail", "email", "VARCHAR(254)", "", "Unique"],
      ["mot de passe", "password", "VARCHAR(128)", "", ""],
      ["nom", "last_name", "VARCHAR(100)", "", ""],
      ["prénom", "first_name", "VARCHAR(100)", "", ""],
      ["téléphone", "phone", "VARCHAR(10)", "", "10 chiffres"],
      ["compte actif", "is_active", "BOOLEAN", "", ""],
      ["membre du personnel", "is_staff", "BOOLEAN", "", "Administrateur"],
      ["super-utilisateur", "is_superuser", "BOOLEAN", "", ""],
      ["date d'inscription", "date_joined", "TIMESTAMPTZ", "", ""],
      ["dernière connexion", "last_login", "TIMESTAMPTZ", "", "Valeur nulle permise"],
    ],
  },
  {
    num: "2", label: "Chambre", name: "hotel_room",
    desc: "Chambres de l'hôtel.",
    cols: [
      ["identifiant", "id", "BIGINT", "PK", "Auto-incrémenté"],
      ["numéro", "number", "VARCHAR(20)", "", "Unique"],
      ["nom", "name", "VARCHAR(150)", "", ""],
      ["type de chambre", "room_type", "VARCHAR(20)", "", ""],
      ["description courte", "short_description", "VARCHAR(255)", "", ""],
      ["description", "description", "TEXT", "", ""],
      ["capacité", "capacity", "SMALLINT", "", ">= 1"],
      ["prix par nuit", "price_per_night", "INTEGER", "", ">= 1 (Ar)"],
      ["image", "image", "VARCHAR(100)", "", "Valeur nulle permise"],
      ["équipements", "amenities", "TEXT", "", ""],
      ["services inclus", "included_services", "TEXT", "", ""],
      ["chambre active", "is_active", "BOOLEAN", "", ""],
      ["date de création", "created_at", "TIMESTAMPTZ", "", ""],
      ["date de modification", "updated_at", "TIMESTAMPTZ", "", ""],
    ],
  },
  {
    num: "3", label: "Image de chambre", name: "hotel_roomimage",
    desc: "Images supplémentaires d'une chambre.",
    cols: [
      ["identifiant", "id", "BIGINT", "PK", "Auto-incrémenté"],
      ["chambre", "room_id", "BIGINT", "FK", "→ hotel_room.id"],
      ["image", "image", "VARCHAR(100)", "", ""],
      ["date de création", "created_at", "TIMESTAMPTZ", "", ""],
    ],
  },
  {
    num: "4", label: "Réservation", name: "hotel_reservation",
    desc: "Réservations des clients.",
    cols: [
      ["identifiant", "id", "BIGINT", "PK", "Auto-incrémenté"],
      ["référence", "reference", "VARCHAR(20)", "", "Unique"],
      ["client", "customer_id", "BIGINT", "FK", "→ hotel_user.id"],
      ["chambre", "room_id", "BIGINT", "FK", "→ hotel_room.id"],
      ["date d'arrivée", "check_in", "DATE", "", ""],
      ["date de départ", "check_out", "DATE", "", "Postérieure à la date d'arrivée"],
      ["nombre de personnes", "guests", "SMALLINT", "", ""],
      ["prix par nuit", "price_per_night", "INTEGER", "", "(Ar)"],
      ["nombre de nuits", "nights", "SMALLINT", "", ""],
      ["montant total", "total_amount", "BIGINT", "", "(Ar)"],
      ["statut", "status", "VARCHAR(12)", "", "en attente, acceptée"],
      ["commentaire", "comment", "TEXT", "", ""],
      ["date de création", "created_at", "TIMESTAMPTZ", "", ""],
      ["date de modification", "updated_at", "TIMESTAMPTZ", "", ""],
    ],
  },
  {
    num: "5", label: "Paiement", name: "hotel_payment",
    desc: "Paiements liés à une réservation.",
    cols: [
      ["identifiant", "id", "BIGINT", "PK", "Auto-incrémenté"],
      ["réservation", "reservation_id", "BIGINT", "FK", "→ hotel_reservation.id"],
      ["reçu par", "received_by_id", "BIGINT", "FK", "→ hotel_user.id (valeur nulle permise)"],
      ["montant", "amount", "BIGINT", "", ">= 1 (Ar)"],
      ["note", "note", "VARCHAR(255)", "", ""],
      ["date de création", "created_at", "TIMESTAMPTZ", "", ""],
    ],
  },
  {
    num: "6", label: "Notification", name: "hotel_notification",
    desc: "Notifications envoyées aux utilisateurs.",
    cols: [
      ["identifiant", "id", "BIGINT", "PK", "Auto-incrémenté"],
      ["utilisateur", "user_id", "BIGINT", "FK", "→ hotel_user.id"],
      ["réservation", "reservation_id", "BIGINT", "FK", "→ hotel_reservation.id (valeur nulle permise)"],
      ["type", "kind", "VARCHAR(20)", "", ""],
      ["titre", "title", "VARCHAR(150)", "", ""],
      ["message", "message", "TEXT", "", ""],
      ["lue", "is_read", "BOOLEAN", "", ""],
      ["date de création", "created_at", "TIMESTAMPTZ", "", ""],
    ],
  },
  {
    num: "7", label: "Service de l'hôtel", name: "hotel_hotelservice",
    desc: "Services et activités de l'hôtel (table indépendante, sans lien avec les autres).",
    cols: [
      ["identifiant", "id", "BIGINT", "PK", "Auto-incrémenté"],
      ["type", "kind", "VARCHAR(10)", "", "service ou activité (service / activity)"],
      ["nom", "name", "VARCHAR(150)", "", ""],
      ["description", "description", "TEXT", "", ""],
      ["image", "image", "VARCHAR(100)", "", "Valeur nulle permise"],
      ["actif", "is_active", "BOOLEAN", "", ""],
      ["date de création", "created_at", "TIMESTAMPTZ", "", ""],
    ],
  },
];

const RULES = [
  "L'identifiant (id) de chaque table est la clé primaire (PK) : un entier BIGINT auto-incrémenté.",
  "L'e-mail d'un compte (hotel_user.email), le numéro d'une chambre (hotel_room.number) et la référence d'une réservation (hotel_reservation.reference) sont uniques.",
  "La date de départ est toujours postérieure à la date d'arrivée.",
  "La capacité d'une chambre, son prix par nuit et le montant d'un paiement valent au moins 1. Les montants sont en ariary (Ar).",
  "Le prix par nuit, le nombre de nuits et le montant total sont enregistrés dans la réservation elle-même.",
  "Le statut d'une réservation prend les valeurs « en attente » ou « acceptée ».",
  "Le téléphone d'un utilisateur compte 10 chiffres ; is_staff identifie les administrateurs.",
  "Relations facultatives (valeur nulle permise) : Paiement > reçu par et Notification > réservation. Les autres clés étrangères sont obligatoires.",
  "La table hotel_hotelservice est indépendante : aucun lien avec les autres tables.",
];

const CLIENT_STEPS = [
  ["Créer un compte", "Page Inscription : e-mail, nom, prénom, téléphone de 10 chiffres et mot de passe."],
  ["Choisir une chambre", "Page Chambres : filtrez par dates, nombre de personnes ou type, puis ouvrez le détail d'une chambre."],
  ["Réserver", "Choisissez les dates et le nombre de personnes. Le montant est calculé automatiquement et la demande passe au statut « En attente »."],
  ["Suivre sa demande", "Dans « Mes réservations » et dans la cloche : une notification annonce si l'administrateur accepte ou refuse."],
  ["Payer à l'hôtel", "Le paiement se fait en espèces à l'hôtel. L'administrateur enregistre le montant reçu : le statut passe à « Partiel » puis « Payée »."],
  ["Obtenir sa facture", "Dès qu'un paiement existe, le bouton Facture apparaît : imprimer ou enregistrer en PDF. L'annulation en ligne n'est plus possible après un paiement."],
];

const ADMIN_STEPS = [
  ["Tableau de bord", "Chambres libres et occupées, réservations par statut, montant encaissé et reste à encaisser."],
  ["Traiter les demandes", "La cloche signale chaque nouvelle demande. Dans Réservations : Accepter (la disponibilité est revérifiée), Refuser ou Annuler."],
  ["Encaisser un paiement", "Sur une réservation acceptée ou terminée, bouton Encaisser : saisissez le montant reçu (acompte ou Solde complet). Le client est notifié."],
  ["Remettre la facture", "Bouton Facture sur la réservation : à imprimer ou à enregistrer en PDF. Elle montre chaque reçu, le total payé et le reste à payer."],
  ["Client venu à l'hôtel", "Clients > Ajouter un client : nom, prénom, téléphone, dates et chambre libre. La réservation est acceptée directement ; encaissez ensuite comme pour une réservation en ligne."],
  ["Gérer le catalogue", "Chambres (ajout, modification, photos, désactivation) et Services et activités. Clients : activer ou désactiver un compte."],
];

const STATUTS = [
  ["En attente", "demande envoyée, en attente de décision"],
  ["Acceptée", "chambre bloquée pour les dates demandées"],
  ["Terminée", "automatique à la date de départ"],
  ["Refusée / Annulée", "les dates sont libérées pour d'autres clients"],
];

function Steps({ title, items }) {
  return (
    <div className="panel">
      <h3>{title}</h3>
      <ol className="steps">
        {items.map(([t, text]) => (<li key={t}><strong>{t}.</strong> {text}</li>))}
      </ol>
    </div>
  );
}

function MpdTable({ t }) {
  return (
    <div className="panel">
      <h3>{t.num}. {t.label} (<code>{t.name}</code>)</h3>
      <p className="muted">{t.desc}</p>
      <div className="table-wrap">
        <table className="table mpd-table">
          <thead>
            <tr><th>Propriété</th><th>Nom technique</th><th>Type</th><th>Clé</th><th>Contraintes / Remarques</th></tr>
          </thead>
          <tbody>
            {t.cols.map(([prop, tech, type, key, note]) => (
              <tr key={tech} className={key === "PK" ? "mpd-pk" : key === "FK" ? "mpd-fk" : ""}>
                <td data-label="Propriété">{prop}</td>
                <td data-label="Nom technique"><code>{tech}</code></td>
                <td data-label="Type">{type}</td>
                <td data-label="Clé">{key && <strong>{key}</strong>}</td>
                <td data-label="Remarques">{note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Mpd() {
  return (
    <>
      <div className="panel">
        <div className="about-bar">
          <div>
            <h3>MPD (Merise) de la base de données</h3>
            <p className="muted">Modèle physique de données : 7 tables PostgreSQL. Légende : PK = clé primaire (ligne jaune) ; FK = clé étrangère (ligne bleue) ; (Ar) = montant en ariary.</p>
          </div>
          <div className="actions">
            <a className="btn btn-primary" href={MPD_PDF} download="MPD_hotel_vahiny_francais.pdf">Télécharger le PDF</a>
            <a className="btn btn-outline" href={MPD_PDF} target="_blank" rel="noreferrer">Ouvrir le PDF</a>
          </div>
        </div>
      </div>
      {MPD_TABLES.map((t) => <MpdTable key={t.name} t={t} />)}
      <div className="panel">
        <h3>Règles et contraintes</h3>
        <ul className="steps">{RULES.map((r) => <li key={r}>{r}</li>)}</ul>
      </div>
    </>
  );
}

function Usage() {
  return (
    <>
      <div className="grid grid-2">
        <Steps title="Parcours du client" items={CLIENT_STEPS} />
        <Steps title="Parcours de l'administrateur" items={ADMIN_STEPS} />
      </div>
      <div className="panel">
        <h3>Statuts d'une réservation</h3>
        <ul className="steps">
          {STATUTS.map(([s, t]) => (<li key={s}><strong>{s}</strong> : {t}</li>))}
        </ul>
        <h3>Statuts de paiement</h3>
        <ul className="steps">
          <li><strong>Non payée</strong> : aucun versement enregistré.</li>
          <li><strong>Partiel</strong> : un acompte a été reçu, il reste un solde.</li>
          <li><strong>Payée</strong> : le total du séjour est réglé (facture acquittée).</li>
        </ul>
      </div>
    </>
  );
}

export default function About() {
  const [tab, setTab] = useState("mpd");
  return (
    <>
      <h1>À propos</h1>
      <div className="panel">
        <h3>{HOTEL.name} : application de gestion de réservation</h3>
        <p>
          Site public, espace client et administration pour réserver une chambre, suivre les demandes, encaisser les paiements en espèces
          et remettre une facture. Les montants sont en ariary (Ar).
        </p>
        <p className="muted">Technologies : Django 5, React 18 avec Vite, PostgreSQL.</p>
      </div>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "mpd"} className={`tab ${tab === "mpd" ? "active" : ""}`} onClick={() => setTab("mpd")}>Schéma MPD (Merise)</button>
        <button role="tab" aria-selected={tab === "usage"} className={`tab ${tab === "usage" ? "active" : ""}`} onClick={() => setTab("usage")}>Utilisation de l'application</button>
      </div>
      {tab === "mpd" ? <Mpd /> : <Usage />}
    </>
  );
}
