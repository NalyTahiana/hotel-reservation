# Gestion de réservation d'hôtel (Django, React.js, PostgreSQL)

Application web de réservation d'hôtel : site public, espace client et espace d'administration.
Les montants sont en ariary (Ar). Toutes les données (comptes, chambres, réservations) sont enregistrées dans PostgreSQL.

## Fonctionnalités

- Site public : accueil, liste et détail des chambres (galerie, équipements, disponibilité par dates), services et activités, à propos, contact.
- Inscription et connexion (e-mail + mot de passe, téléphone sur exactement 10 chiffres, vérifié dans React et dans Django).
- Réservation : montant calculé côté serveur, statut initial « En attente », aucune double réservation sur des périodes qui se chevauchent.
- Espace client : profil modifiable, liste et détail des réservations, annulation.
- Administration : tableau de bord (données réelles), chambres, réservations (accepter, refuser, annuler, filtres), clients (désactivation sans perte d'historique), services et activités.
- Pagination serveur de 10 éléments, interface responsive sans dégradés ni emojis.

## Technologies

Python 3.10 à 3.12, Django 5.0, Django REST Framework, django-cors-headers, psycopg2, PostgreSQL 13 ou plus récent,
Node.js 18 ou plus récent, React 18, Vite 5, React Router 6.

## Structure

```
hotel-reservation/
├── backend/
│   ├── config/            settings.py, urls.py, wsgi.py, asgi.py
│   ├── apps/
│   │   ├── accounts/      utilisateur personnalisé, inscription, connexion, gestion des clients
│   │   ├── rooms/         chambres, photos, disponibilité publique, gestion admin
│   │   ├── reservations/  modèle, règles métier (services.py), API client et admin
│   │   ├── services/      services et activités de l'hôtel
│   │   └── dashboard/     statistiques de l'administration
│   ├── media/             photos envoyées (créé automatiquement)
│   ├── requirements.txt, manage.py, .env.example
├── frontend/
│   ├── public/images/     placeholder.svg (+ vos photos : hero.jpg, gallery-1.jpg ... gallery-4.jpg)
│   └── src/               components, layouts, pages (+ pages/admin), services (appels API), hooks, context, utils, styles
└── README.md
```

## Règles métier importantes

- **Chevauchement** : une réservation existante bloque la chambre si `arrivée demandée < départ existant` ET `départ demandé > arrivée existante`.
  Départ le 15 et nouvelle arrivée le 15 : autorisé.
- **Statuts bloquants** : « En attente » et « Acceptée ». « Refusée », « Annulée » et « Terminée » libèrent la période.
- **Transitions** : En attente -> Acceptée / Refusée / Annulée ; Acceptée -> Annulée ou Terminée ; les autres statuts sont finaux.
  Une réservation acceptée passe automatiquement à « Terminée » une fois la date de départ atteinte.
- **Annulation par le client** : une demande en attente à tout moment ; une réservation acceptée jusqu'à la veille de l'arrivée.
- **Concurrence** : la création et l'acceptation s'exécutent dans une transaction avec `SELECT ... FOR UPDATE` sur la chambre ; la disponibilité est revérifiée à la création et à l'acceptation.
- **Chiffre d'affaires** : somme des montants des réservations « Terminées » (séjours réellement effectués).
- **Prix** : le tarif par nuit est copié dans la réservation ; changer le prix d'une chambre ne modifie pas l'historique.
- **Chambre supprimable** seulement sans historique de réservations (sinon la désactiver).

## Installation sous Windows (PowerShell, Visual Studio Code)

### 1. Prérequis

Installer Python (cocher « Add python.exe to PATH »), Node.js LTS et PostgreSQL 13 ou plus récent (avec pgAdmin ou le client `psql`).

### 2. Base de données

Suivez `POSTGRESQL.md` (création de la base `hotel_reservation_db` et de l'utilisateur `hotel_user`), puis renseignez `DB_PASSWORD` dans `backend\.env`.

### 3. Backend (premier terminal)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Si PowerShell refuse d'activer le venv : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Éditer `backend\.env` : renseigner `DB_PASSWORD` (mot de passe de `hotel_user`) et une valeur longue pour `DJANGO_SECRET_KEY`. Puis :

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`createsuperuser` demande l'e-mail, le nom, le prénom, un téléphone de 10 chiffres et le mot de passe : ce compte est l'administrateur.
Les fichiers de migration sont générés par `makemigrations` à partir des modèles (dossiers `migrations/` livrés vides).

### 4. Frontend (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

### 5. Adresses locales

- Site : http://localhost:5173
- Administration de l'hôtel (après connexion avec le compte administrateur) : http://localhost:5173/admin
- API Django : http://127.0.0.1:8000/api/
- Administration Django : http://127.0.0.1:8000/admin/

Le serveur de développement Vite relaie `/api` et `/media` vers Django : cookies de session et jeton CSRF fonctionnent sans réglage supplémentaire.

## Premiers pas : ajouter des chambres et tester une réservation

1. Se connecter sur http://localhost:5173/connexion avec le compte administrateur, ouvrir « Chambres » puis « Ajouter une chambre » (numéro, nom, type, capacité, prix en Ar, photo).
2. Ajouter quelques services et activités dans « Services et activités » (Wi-Fi, piscine, excursion...).
3. Se déconnecter, créer un compte client sur `/inscription`, choisir une chambre et envoyer une demande de réservation.
4. Se reconnecter en administrateur : « Réservations » -> Accepter ou Refuser, puis constater le nouveau statut dans l'espace client.
5. Tester le chevauchement : réserver la même chambre sur des dates qui se croisent avec un second compte -> message de refus.

Photos du site public : déposer `hero.jpg` et `gallery-1.jpg` à `gallery-4.jpg` dans `frontend/public/images/`
(ou modifier les chemins et les coordonnées de l'hôtel dans `frontend/src/utils/hotel.js`). Sans fichier, une image de remplacement s'affiche.

## Tests

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py test
```

L'utilisateur PostgreSQL doit pouvoir créer la base de test (`ALTER USER hotel_user CREATEDB;`, voir `POSTGRESQL.md`).
Pour lancer rapidement les tests sans PostgreSQL : `$env:DB_ENGINE="sqlite"; python manage.py test` (la persistance PostgreSQL se vérifie alors manuellement, ci-dessous).

Les tests couvrent : inscription, connexion, téléphone à 10 chiffres, création et montant, dates invalides, capacité, chevauchement, réservations consécutives,
libération après refus ou annulation, revérification à l'acceptation, accès administrateur interdit aux clients, isolation des réservations, pagination.

**État des résultats** : ces tests ont été écrits mais n'ont pas pu être exécutés dans l'environnement où le projet a été généré (pas d'accès réseau pour installer Django).
Lancez `python manage.py test` et corrigez ou signalez toute erreur avant de vous fier au projet.

### Vérifications manuelles (frontend et persistance PostgreSQL)

- Créer un compte, une réservation, puis arrêter les deux serveurs, les relancer : le compte et la réservation sont toujours là.
- Vérifier dans PostgreSQL : `psql -U hotel_user -d hotel_reservation_db -c "SELECT reference, status, total_amount FROM reservations_reservation;"`
- Réduire la fenêtre du navigateur (< 860 px) : menu mobile et tableaux en cartes.
- Avec un compte client, ouvrir http://localhost:5173/admin : redirection vers l'accueil ; l'API `/api/admin/...` répond 403.

## Résolution des erreurs courantes

| Problème | Solution |
|---|---|
| `password authentication failed for user "hotel_user"` | Vérifier `DB_USER` et `DB_PASSWORD` dans `backend\.env` ; `ALTER USER hotel_user WITH PASSWORD '...';` au besoin. |
| `database "hotel_reservation_db" does not exist` | Créer la base (voir `POSTGRESQL.md`). |
| `connection refused` (port 5432) | Démarrer le service PostgreSQL (services Windows : `postgresql-x64-...`). |
| `no module named psycopg2` | `pip install -r requirements.txt` dans le venv activé. |
| `permission denied to create database` (tests) | `ALTER USER hotel_user CREATEDB;` |
| Erreur CSRF (403) à la connexion | Utiliser http://localhost:5173 (et non 127.0.0.1:5173) ; vérifier `FRONTEND_ORIGIN` dans `.env`. |
| Images qui ne s'affichent pas | Le backend doit tourner (les photos passent par `/media`) ; l'image de remplacement s'affiche sinon. |
| `Impossible de joindre le serveur` | Démarrer `python manage.py runserver` dans le terminal backend. |

## Sécurité

- Sessions Django (cookie HttpOnly) et protection CSRF (en-tête `X-CSRFToken`) ; mots de passe hachés par Django.
- Permissions vérifiées sur chaque endpoint (`IsAdminUser` pour `/api/admin/`) ; masquer un bouton dans React ne sert que de confort.
- CORS limité à `FRONTEND_ORIGIN` ; secrets dans `.env` (non versionné).
- Avant une mise en production : `DJANGO_DEBUG=False`, clé secrète forte, HTTPS, hôtes autorisés, service des fichiers `media` par le serveur web.

## Mise en ligne

Voir `DEPLOIEMENT.md` (dépôt GitHub, puis hébergement gratuit sur Render avec PostgreSQL et Cloudinary).
Après la mise à jour du projet, relancez `pip install -r requirements.txt` dans le backend (nouvelles dépendances).
