import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # /home/wmstf/fincera-leads

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-dev-key-change-in-production-fincera-leads-2026"
)
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"

# Build ALLOWED_HOSTS — always include Railway's injected domain automatically
_allowed = os.environ.get("ALLOWED_HOSTS", "*").split(",")
_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")   # injected by Railway
if _railway_domain and _railway_domain not in _allowed:
    _allowed.append(_railway_domain)
ALLOWED_HOSTS = _allowed

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "leads",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "fincera_project.urls"
WSGI_APPLICATION = "fincera_project.wsgi.application"

# Database — auto-detect writable path for SQLite
# Priority: DB_PATH env var → /data/leads.db (Railway volume) → local project root
def _resolve_db_path():
    from pathlib import Path as _P
    env_path = os.environ.get("DB_PATH")
    if env_path:
        p = _P(env_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p)
    # On Railway, use the persistent volume at /data/
    if os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_ENVIRONMENT"):
        p = _P("/data/leads.db")
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p)
    # Local development
    return str(PROJECT_ROOT / "leads.db")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _resolve_db_path(),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = False  # pipeline stores plain datetime strings, keep consistent

# DRF
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "leads.pagination.StandardPagination",
    "PAGE_SIZE": 50,
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

# Allow all vercel.app preview deployments
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
