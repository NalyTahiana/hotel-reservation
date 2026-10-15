# PostgreSQL pour le projet (local et Render)

PostgreSQL est la base utilisée en ligne sur Render. Utiliser la même base en local évite les différences de comportement.
Les dossiers `migrations/` du projet ne contiennent que `__init__.py` : les migrations sont générées par `makemigrations` (étape 3), à partir des modèles, directement pour PostgreSQL.

## 1. Installer PostgreSQL sous Windows
1. Téléchargez l'installateur sur https://www.postgresql.org/download/windows/ (EDB) et installez-le avec les options par défaut.
2. Choisissez un mot de passe pour l'utilisateur `postgres` (notez-le) ; gardez le port `5432`.

## 2. Créer la base et l'utilisateur
Ouvrez **SQL Shell (psql)** (menu Démarrer), validez les valeurs par défaut, saisissez le mot de passe de `postgres`, puis :

```sql
CREATE USER hotel_user WITH PASSWORD 'VOTRE_MOT_DE_PASSE';
CREATE DATABASE hotel_reservation_db OWNER hotel_user ENCODING 'UTF8';
ALTER USER hotel_user CREATEDB;
\q
```

`CREATEDB` permet à `python manage.py test` de créer sa base de test.

## 3. Configurer le projet (cmd, dossier `backend`, venv activé)
```bat
pip install -r requirements.txt
notepad .env
```
Dans `.env`, mettez :
```
DB_ENGINE=postgres
DB_NAME=hotel_reservation_db
DB_USER=hotel_user
DB_PASSWORD=VOTRE_MOT_DE_PASSE
DB_HOST=127.0.0.1
DB_PORT=5432
```
Puis :
```bat
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
`makemigrations` ne se lance qu'une fois : versionnez ensuite les fichiers créés dans chaque dossier `migrations/` (Git).

## 4. (Facultatif) Récupérer les données de l'ancienne base MySQL
Cette version du projet ne gère plus MySQL : faites l'export **avec l'ancienne copie du projet** (celle qui tourne encore sur MySQL, son `.env` en `DB_ENGINE=mysql`) :
```bat
python -Xutf8 manage.py dumpdata --exclude contenttypes --exclude auth.permission --exclude admin.logentry --exclude sessions --indent 2 -o data.json
```
Copiez `data.json` dans le dossier `backend` de la nouvelle version, puis :
```bat
python manage.py migrate
python -Xutf8 manage.py loaddata data.json
```
`loaddata` remet automatiquement à jour les compteurs d'identifiants (séquences) de PostgreSQL.
Les photos déjà téléversées ne sont pas dans ce fichier : copiez le dossier `media/` ou ajoutez-les de nouveau depuis l'administration.

## Différences de comportement avec MySQL
- **Majuscules et accents** : la recherche (`icontains`) ignore la casse, mais PostgreSQL distingue « René » de « Rene » (MySQL les confondait avec sa collation par défaut).
- **Contrainte de dates** : `check_out > check_in` est appliquée par PostgreSQL au niveau de la base.

## 5. Sur Render
Rien à changer : la variable `DATABASE_URL` (URL de la base Render ou Neon) a priorité sur les variables `DB_*`.
Après chaque `git push`, `build.sh` exécute `migrate` sur la base PostgreSQL en ligne.

## Erreurs courantes
| Message | Solution |
|---|---|
| `password authentication failed for user "hotel_user"` | Le mot de passe de `.env` diffère de celui défini dans `CREATE USER` : `ALTER USER hotel_user WITH PASSWORD '...';` |
| `database "hotel_reservation_db" does not exist` | Créez la base (étape 2). |
| `connection refused` sur le port 5432 | Le service PostgreSQL n'est pas démarré (services Windows : `postgresql-x64-...`). |
| `permission denied to create database` (tests) | `ALTER USER hotel_user CREATEDB;` |
| `no module named psycopg2` | `pip install -r requirements.txt` dans le venv activé. |
