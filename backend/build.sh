#!/usr/bin/env bash
# Exécuté par Render à chaque déploiement (commande de build : bash build.sh).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Crée le compte administrateur s'il est défini dans les variables d'environnement
# (sans effet s'il existe déjà : l'erreur est ignorée).
if [[ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]]; then
  python manage.py createsuperuser --noinput || true
fi
