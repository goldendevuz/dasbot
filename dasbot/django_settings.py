import os
from urllib.parse import urlparse, unquote
from dasbot.config import settings as dynaconf_settings

# Allow synchronous Django ORM calls from inside aiogram async event loops
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = dynaconf_settings.get("SECRET_KEY", "django-insecure-dasbot-secret-key-default-1234567890")
DEBUG = dynaconf_settings.get("DEBUG", True)

INSTALLED_APPS = [
    "rest_framework",
    "dasbot",
]

TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configure database connection
env_mode = os.environ.get("ENV_FOR_DYNACONF", dynaconf_settings.get("ENV_FOR_DYNACONF", "development")).lower()

if env_mode == "test":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "file:memorydb_test?mode=memory&cache=shared",
            "OPTIONS": {
                "uri": True,
            },
        }
    }
else:
    db_address = dynaconf_settings.get("DB_ADDRESS", "postgresql://dasbot:dasbot@127.0.0.1:5432/dasbot")
    username = dynaconf_settings.get("DB_USERNAME")
    password = dynaconf_settings.get("DB_PASSWORD")
    
    parsed = urlparse(db_address)
    if parsed.scheme.startswith("postgres"):
        db_name = parsed.path.lstrip("/") or dynaconf_settings.get("DB_NAME", "dasbot")
        user = username or unquote(parsed.username) if parsed.username else (username or "dasbot")
        password = password or unquote(parsed.password) if parsed.password else (password or "dasbot")
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5432
        
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": db_name,
                "USER": user,
                "PASSWORD": password,
                "HOST": host,
                "PORT": str(port),
            }
        }
    else:
        # Fallback for local sqlite if someone specifies sqlite://
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
            }
        }
