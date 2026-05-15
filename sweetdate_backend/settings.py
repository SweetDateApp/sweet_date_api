from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---- Security ----
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me-in-production-please")
DEBUG      = os.environ.get("DEBUG", "true") == "true" # f on prod
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ---- Applications ----
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sweetdate_backend.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "sweetdate_backend.wsgi.application"

# ---- BD Postgres ----
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     os.environ.get("DB_NAME",     "sweetdate_db"),
        "USER":     os.environ.get("DB_USER",     "sweetdate_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "sweetdate_pass"),
        "HOST":     os.environ.get("DB_HOST",     "localhost"),
        "PORT":     os.environ.get("DB_PORT",     "5432"),
    }
}

# ---- User customum ----
AUTH_USER_MODEL = "api.User"

# ---- REST Framework ----
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ---- Auth ----
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS":  True,
}

# ---- CORS ----
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ---- Email (Gmail SMTP) ----
EMAIL_BACKEND        = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST           = "smtp.gmail.com"
EMAIL_PORT           = 587
EMAIL_USE_TLS        = True
EMAIL_HOST_USER      = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD  = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL   = os.environ.get("DEFAULT_FROM_EMAIL", "Sweet Date <noreply@sweetdate.app>")

# ---- Internationalisation ----
LANGUAGE_CODE = "fr-fr"
TIME_ZONE     = "Indian/Antananarivo"
USE_I18N      = True
USE_TZ        = True

# ---- Statics Files ----
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- password validation ----
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
