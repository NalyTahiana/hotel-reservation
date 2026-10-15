import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "cle-de-developpement-non-securisee"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY est obligatoire quand DJANGO_DEBUG=False.")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
# Render fournit automatiquement le nom d'hôte public du service.
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)

# Photos des chambres : Cloudinary en ligne (le disque de Render est effacé à chaque redémarrage).
USE_CLOUDINARY = bool(os.getenv("CLOUDINARY_URL"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "apps.accounts",
    "apps.rooms",
    "apps.reservations",
    "apps.services",
    "apps.dashboard",
    "apps.notifications",
]
if USE_CLOUDINARY:
    INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# --- Base de données -------------------------------------------------------
# PostgreSQL uniquement (local et en ligne).
#   - DATABASE_URL (mise en ligne : Render, Neon...) a priorité sur les variables DB_*.
#   - DB_ENGINE=sqlite reste possible pour lancer les tests rapidement, sans PostgreSQL.
# PostgreSQL utilise READ COMMITTED par défaut : la vérification de disponibilité faite après le verrou
# (SELECT ... FOR UPDATE sur la chambre) voit toutes les réservations déjà validées.
DATABASE_URL = os.getenv("DATABASE_URL")
DB_ENGINE = os.getenv("DB_ENGINE", "postgres")
if DATABASE_URL:
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
elif DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "hotel_reservation_db"),
            "USER": os.getenv("DB_USER", "hotel_user"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
elif DB_ENGINE == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    raise RuntimeError("DB_ENGINE doit valoir postgres ou sqlite.")

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Indian/Antananarivo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage" if USE_CLOUDINARY else "django.core.files.storage.FileSystemStorage"
    },
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- API REST ---------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# --- Sessions, CSRF, CORS -----------------------------------------------------
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
CORS_ALLOWED_ORIGINS = [FRONTEND_ORIGIN]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [FRONTEND_ORIGIN]
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")
# Les requêtes /api passent par le site statique (réécriture) : accepter aussi son nom d'hôte.
from urllib.parse import urlparse  # noqa: E402

_front_host = urlparse(FRONTEND_ORIGIN).hostname
if _front_host and _front_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_front_host)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Render termine le HTTPS devant Django
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # React doit lire le jeton pour l'envoyer dans X-CSRFToken
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
