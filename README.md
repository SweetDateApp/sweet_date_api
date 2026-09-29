# Sweet Date — Backend Django + PostgreSQL

[![CI](https://github.com/SweetDateApp/sweet_date_api/actions/workflows/ci.yml/badge.svg?branch=preprod)](https://github.com/SweetDateApp/sweet_date_api/actions/workflows/ci.yml) [![CD preprod](https://github.com/SweetDateApp/sweet_date_api/actions/workflows/cd.yml/badge.svg?branch=preprod)](https://github.com/SweetDateApp/sweet_date_api/actions/workflows/cd.yml?query=branch%3Apreprod) [![CD prod](https://github.com/SweetDateApp/sweet_date_api/actions/workflows/cd.yml/badge.svg?branch=prod)](https://github.com/SweetDateApp/sweet_date_api/actions/workflows/cd.yml?query=branch%3Aprod)

## Stack
- **Django 5.2 LTS** + **Django REST Framework** (Python 3.12+)
- **PostgreSQL** (base de données)
- **JWT** (authentification via `djangorestframework-simplejwt`)
- **Gmail SMTP** (envoi des invitations romantiques)

## Installation

### 1. PostgreSQL — Créer la base de données
```sql
CREATE DATABASE sweetdate_db;
CREATE USER sweetdate_user WITH PASSWORD 'sweetdate_pass';
GRANT ALL PRIVILEGES ON DATABASE sweetdate_db TO sweetdate_user;
```

### 2. Environnement Python
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Variables d'environnement
```bash
cp .env.example .env
# Éditez .env avec vos vraies valeurs
```

### 4. Migrations et démarrage
```bash
python manage.py migrate
python manage.py createsuperuser   # optionnel
python manage.py runserver
```

### 5. Tests
```bash
python manage.py test
```
L'utilisateur PostgreSQL doit pouvoir créer la base de test (`ALTER USER sweetdate_user CREATEDB;`).

## Déploiement (Render)

| Réglage | Valeur |
|---------|--------|
| Build command | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| Start command | `gunicorn sweetdate_backend.wsgi:application` |
| Variables | `DEBUG=false`, `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `EMAIL_*` |
| Avatars | `SERVE_MEDIA=true` + `MEDIA_ROOT` sur un disque persistant Render (sinon les fichiers sont perdus à chaque déploiement) |

Le déploiement est déclenché par GitHub Actions (voir `CONTRIBUTING.md`).

## API Endpoints

| Méthode | URL | Description | Auth |
|---------|-----|-------------|------|
| POST | `/api/auth/register/` | Créer un compte | ❌ |
| POST | `/api/auth/login/` | Connexion | ❌ |
| GET/PATCH | `/api/auth/me/` | Profil utilisateur | ✅ |
| POST | `/api/auth/refresh/` | Rafraîchir le token | ❌ |
| GET | `/api/dates/` | Lister ses plans | ✅ |
| POST | `/api/dates/` | Créer un plan | ✅ |
| GET/PATCH/DELETE | `/api/dates/<id>/` | Détail d'un plan | ✅ |
| POST | `/api/dates/<id>/send/` | Envoyer l'invitation email | ✅ |

## Exemple — Créer un compte
```json
POST /api/auth/register/
{
  "username": "Romeo",
  "password": "monMotDePasse123",
  "password_confirm": "monMotDePasse123",
  "email_partner1": "romeo@gmail.com",
  "email_partner2": "juliette@gmail.com"
}
```

## Exemple — Créer un plan de rendez-vous
```json
POST /api/dates/
Authorization: Bearer <access_token>
{
  "date": "2025-02-14",
  "time": "19:30",
  "location": "Restaurant Le Romantique, Antananarivo",
  "excitement": 85,
  "activity_keys": ["meal", "walk", "photos"]
}
```

## Email Gmail — Configuration App Password
1. Aller sur https://myaccount.google.com/apppasswords
2. Créer un "App Password" pour "Mail"
3. Mettre la clé dans `EMAIL_HOST_PASSWORD` dans `.env`

## Structure de la base de données

```
users
├── id, username, password
├── email_partner1  (email du 1er partenaire)
├── email_partner2  (email du 2ème partenaire)
├── avatar          (image, optionnelle)
└── created_at

date_plans
├── id, user_id (FK)
├── date, time, location
├── excitement (0-100, défaut 0)
├── email_sent, email_sent_at
└── created_at, updated_at

date_activities
├── id, date_plan_id (FK)
└── activity (walk|movie|meal|game|other|photos)
```
