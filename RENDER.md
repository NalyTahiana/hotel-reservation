# Mise en ligne de test sur Render (gratuit)

Architecture : **3 éléments** sur Render + Cloudinary pour les photos.

| Élément | Type Render | Rôle |
|---|---|---|
| Base | PostgreSQL (Free) | données |
| Backend | Web Service (Free), dossier `backend` | Django + API |
| Frontend | Static Site, dossier `frontend` | React, relaie `/api` vers le backend |

Limites du plan gratuit (à vérifier sur render.com/pricing) :
- le backend **s'endort après 15 min sans visite** ; le réveil prend environ 1 minute ;
- la base PostgreSQL gratuite **expire environ 30 jours après sa création** (puis suppression) ;
- le disque est **effacé à chaque redémarrage** : sans Cloudinary, les photos téléversées disparaissent.

## 0. Préparer le code
1. Vérifiez que `backend/hotel/migrations/` contient bien `0001_initial.py` (créé par `python manage.py makemigrations`). **Il doit être envoyé sur GitHub.**
   Si vous aviez déjà mis en ligne l'ancienne version du projet (applications `accounts`, `rooms`...), supprimez sur Render l'ancienne base de données et le backend, puis recréez-les (étapes 2 et 3) : les tables ont changé.
2. Ne versionnez jamais `backend/.env` (déjà dans `.gitignore`).
3. Envoyez le projet sur GitHub (dépôt dont la racine contient `backend/` et `frontend/`) :
```bat
git init
git add .
git commit -m "Projet hotel-reservation"
git branch -M main
git remote add origin https://github.com/VOTRE_COMPTE/hotel-reservation.git
git push -u origin main
```

## 1. Cloudinary (photos)
Créez un compte gratuit sur cloudinary.com, puis copiez la valeur **API Environment variable** du tableau de bord :
`cloudinary://CLE_API:SECRET_API@NOM_DU_CLOUD`

## 2. Base PostgreSQL sur Render
*New + > PostgreSQL* : nom `hotel-db`, plan **Free**, puis *Create*.
Quand elle est prête, copiez **Internal Database URL**.

## 3. Backend (Web Service)
*New + > Web Service*, dépôt GitHub, puis :

| Champ | Valeur |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn projet.wsgi:application` |
| Instance Type | Free |
| Région | la même que la base |

Variables d'environnement :

| Nom | Valeur |
|---|---|
| `PYTHON_VERSION` | `3.12.3` |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | une longue valeur aléatoire (50 caractères ou plus) |
| `DATABASE_URL` | l'Internal Database URL de l'étape 2 |
| `CLOUDINARY_URL` | la valeur de l'étape 1 |
| `FRONTEND_ORIGIN` | provisoire : `https://exemple.onrender.com` (corrigée à l'étape 5) |
| `DJANGO_SUPERUSER_EMAIL` | l'e-mail de l'administrateur |
| `DJANGO_SUPERUSER_PASSWORD` | son mot de passe |
| `DJANGO_SUPERUSER_LAST_NAME` | nom |
| `DJANGO_SUPERUSER_FIRST_NAME` | prénom |
| `DJANGO_SUPERUSER_PHONE` | 10 chiffres |

Lancez le déploiement. Notez l'adresse du backend : `https://NOM-BACKEND.onrender.com`.
Vérification : `https://NOM-BACKEND.onrender.com/api/rooms/` doit répondre (liste vide ou JSON, sans erreur 500).

## 4. Frontend (Static Site)
*New + > Static Site*, même dépôt :

| Champ | Valeur |
|---|---|
| Root Directory | `frontend` |
| Build Command | `npm install && npm run build` |
| Publish Directory | `dist` |

Laissez `VITE_API_URL` vide. Puis, dans *Redirects/Rewrites* du site, ajoutez **dans cet ordre** :

| Type | Source | Destination |
|---|---|---|
| Rewrite | `/api/*` | `https://NOM-BACKEND.onrender.com/api/*` |
| Rewrite | `/*` | `/index.html` |

Le premier rewrite fait passer les appels `/api` par le site : cookies de session et CSRF fonctionnent comme en local.

## 5. Corriger FRONTEND_ORIGIN
Copiez l'adresse du site statique (`https://NOM-SITE.onrender.com`), mettez-la dans `FRONTEND_ORIGIN` du backend (sans `/` final), puis *Manual Deploy > Deploy latest commit*.

## 6. Tester
Ouvrez l'adresse du site statique, connectez-vous avec le compte administrateur (`/connexion`), ajoutez une chambre avec photo, puis testez une réservation avec un compte client.

## Erreurs courantes
| Symptôme | Cause / solution |
|---|---|
| Première page très lente | Le backend se réveille (environ 1 min). Réessayez. |
| `Bad Request (400)` / `DisallowedHost` | Hôte absent de `DJANGO_ALLOWED_HOSTS` : vérifiez `FRONTEND_ORIGIN` (avec `https://`) et redéployez. |
| 403 CSRF à la connexion | `FRONTEND_ORIGIN` ne correspond pas exactement à l'adresse du site statique. |
| Erreur 404 sur `/api/...` depuis le site | Règle `/api/*` absente ou placée après `/*`. |
| `relation ... does not exist` | Migrations non envoyées sur GitHub : `git add backend/hotel/migrations` puis push. |
| Photos disparues | `CLOUDINARY_URL` manquant ou incorrect. |
| Erreur de build Python | Vérifiez `PYTHON_VERSION=3.12.3` (Django 5.0 n'est pas prévu pour les versions de Python les plus récentes). |
