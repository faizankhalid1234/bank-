import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "alybank-dev-change-in-production-use-env")

# Production: set DEBUG=0 or DEBUG=false in environment.
_debug_raw = (os.environ.get("DEBUG", "") or "").strip().lower()
if _debug_raw in ("0", "false", "no", "off"):
    DEBUG = False
elif _debug_raw in ("1", "true", "yes", "on"):
    DEBUG = True
else:
    DEBUG = True  # default: local dev

# Production app URL (Railway). Override with PUBLIC_APP_URL=https://your-host.up.railway.app
_railway_public_domain = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or "").strip()
_default_railway_host = "bank-production-f72a.up.railway.app"
_public_app_url = (os.environ.get("PUBLIC_APP_URL") or "").strip().rstrip("/")
if not _public_app_url:
    _host_for_origin = _railway_public_domain or _default_railway_host
    _public_app_url = f"https://{_host_for_origin}"

_allowed = (os.environ.get("ALLOWED_HOSTS", "") or "").strip()
if _allowed:
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    _hosts: list[str] = []
    for h in (_railway_public_domain, _default_railway_host):
        if h and h not in _hosts:
            _hosts.append(h)
    ALLOWED_HOSTS = _hosts

# Behind Railway / reverse proxy: HTTPS at edge, HTTP internally.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "banking",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "alybank.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "banking.context_processors.bank_branding",
            ],
        },
    },
]

WSGI_APPLICATION = "alybank.wsgi.application"

if (os.environ.get("DATABASE_URL") or "").strip():
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=600,
            ssl_require=os.environ.get("DATABASE_SSL_REQUIRE", "").lower()
            in ("1", "true", "yes", "require"),
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
    ],
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
# Railway production (https://bank-production-f72a.up.railway.app/) — same SPA + API origin
if _public_app_url.startswith("http") and _public_app_url not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(_public_app_url)
if _public_app_url.startswith("http") and _public_app_url not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(_public_app_url)
_extra_cors = (os.environ.get("DEPLOYMENT_CORS_ORIGINS", "") or "").strip()
if _extra_cors:
    for origin in _extra_cors.split(","):
        o = origin.strip()
        if o and o not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(o)
_extra_csrf = (os.environ.get("DEPLOYMENT_CSRF_TRUSTED_ORIGINS", "") or "").strip()
if _extra_csrf:
    for origin in _extra_csrf.split(","):
        o = origin.strip()
        if o and o not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(o)

LOGIN_REDIRECT_URL = "banking:dashboard"
LOGOUT_REDIRECT_URL = "banking:login"
LOGIN_URL = "banking:login"

# Optional: real SMS OTP via Twilio (https://www.twilio.com/). If unset, OTP is only logged on the server.
# Account SID always starts with AC... (Console dashboard). API Key SID starts with SK... (optional auth method).
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_API_KEY_SID = os.environ.get("TWILIO_API_KEY_SID", "").strip()
TWILIO_API_KEY_SECRET = os.environ.get("TWILIO_API_KEY_SECRET", "").strip()
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "").strip()

# Twilio trial: OTP is verified E.164 par bhejo. Agar .env mein OTP_FIXED_PHONE_E164 key hi na ho,
# default +923219655330 (Twilio Verified Caller ID). Key ho aur value khali ho to form wala number use hoga.
if "OTP_FIXED_PHONE_E164" in os.environ:
    OTP_FIXED_PHONE_E164 = (os.environ.get("OTP_FIXED_PHONE_E164") or "").strip()
else:
    OTP_FIXED_PHONE_E164 = "+923219655330"

# --- Email (Brevo SMTP or any provider) — registration email OTP ---
# Brevo: https://app.brevo.com/settings/keys/smtp — Login = your Brevo account email, Password = xsmtpsib-... key
BREVO_SMTP_LOGIN = os.environ.get("BREVO_SMTP_LOGIN", "").strip()
BREVO_SMTP_KEY = os.environ.get("BREVO_SMTP_KEY", "").strip()
# Real inbox address verified in Brevo → Senders (Gmail etc.). Required when SMTP login is *@smtp-brevo.com.
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "").strip()
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp-relay.brevo.com").strip()
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1").lower() not in ("0", "false", "no")
EMAIL_HOST_USER = (os.environ.get("EMAIL_HOST_USER", "").strip() or BREVO_SMTP_LOGIN)
EMAIL_HOST_PASSWORD = (os.environ.get("EMAIL_HOST_PASSWORD", "").strip() or BREVO_SMTP_KEY)

_default_from_env = os.environ.get("DEFAULT_FROM_EMAIL", "").strip()
if _default_from_env:
    DEFAULT_FROM_EMAIL = _default_from_env
elif BREVO_SENDER_EMAIL:
    DEFAULT_FROM_EMAIL = f"AlyBank <{BREVO_SENDER_EMAIL}>"
elif EMAIL_HOST_USER and "@smtp-brevo.com" not in EMAIL_HOST_USER.lower():
    DEFAULT_FROM_EMAIL = f"AlyBank <{EMAIL_HOST_USER}>"
else:
    # SMTP user is like xxxx@smtp-brevo.com — Gmail needs a normal verified From; set BREVO_SENDER_EMAIL.
    DEFAULT_FROM_EMAIL = ""

BANK_NAME_EMAIL = os.environ.get("BANK_NAME_EMAIL", "AlyBank").strip() or "AlyBank"

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND",
        "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
    )
