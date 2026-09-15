import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Real deployments set SECRET_KEY in the ox Environment editor.
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-secret-key")

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

# ox injects the deploy domain as DJANGO_ALLOWED_HOSTS (comma-separated).
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "greetings",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = []

WSGI_APPLICATION = "config.wsgi.application"

# ox autowires a local postgres role + database and injects DATABASE_URL.
# The sqlite fallback is local-dev convenience only: it exists just when
# DATABASE_URL is unset, and ox always sets it.
if os.environ.get("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"])}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Broker and result backend ride the same local redis that ox autowires
# (REDIS_URL). CELERY_BROKER_URL overrides for custom setups; the 127.0.0.1
# default covers running a worker on a dev machine without env.
_broker_url = (
    os.environ.get("CELERY_BROKER_URL")
    or os.environ.get("REDIS_URL")
    or "redis://127.0.0.1:6379/0"
)
CELERY_BROKER_URL = _broker_url
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", _broker_url)

CELERY_TASK_ALWAYS_EAGER = False

# One timer to prove beat runs: the worker journal repeats this line every 60s.
# Modern spelling (CELERY_BEAT_SCHEDULE); the old CELERYBEAT_SCHEDULE name is
# ignored under the namespace="CELERY" bootstrap above.
CELERY_BEAT_SCHEDULE = {
    "heartbeat-every-60s": {
        "task": "greetings.tasks.heartbeat",
        "schedule": 60.0,
    },
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
