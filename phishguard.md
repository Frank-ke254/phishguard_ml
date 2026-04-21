# PhishGuard

PhishGuard is a Django web app with a machine-learning backend for phishing URL detection.
It supports single URL scans and batch scans, with a browser UI and REST API endpoints.

## Current Stack

- Backend: Django + Django REST Framework
- Model: scikit-learn `RandomForestClassifier`
- Frontend: static HTML/CSS/JS served by Django
- Artifacts: `joblib` model + feature columns

## Project Structure

```text
phishguard/
├── backend/
│   ├── detector/                  # API views, serializers, prediction logic
│   ├── phishguard/                # Django settings and URL config
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                      # UI assets (served by Django templates/static)
├── model/
│   ├── train_model.py             # Training script
│   └── artifacts/                 # Generated model files (after training)
├── phishing_dataset.csv           # Training dataset
└── README_1.md
```

## API Endpoints

Base path: `/api/`

- `GET /api/health/` - service health and model artifact availability
- `POST /api/predict/` - single URL prediction
- `POST /api/batch-predict/` - batch URL prediction (up to 200 URLs)

Root route:

- `GET /` - frontend UI (`frontend/index.html`)

## Local Setup

1) Create and activate a virtual environment.
2) Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3) Configure environment variables:

```bash
cp .env.example .env
```

Then update `.env` values as needed.

4) Train the model artifacts:

```bash
cd ..
python model/train_model.py
```

This generates:

- `model/artifacts/phishing_model.pkl`
- `model/artifacts/feature_columns.pkl`

5) Run the app:

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

## Environment Variables

Required:

- `DJANGO_SECRET_KEY`

Common:

- `DJANGO_DEBUG` (default recommended: `false` in production)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated)

Security controls:

- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SESSION_COOKIE_SECURE`
- `DJANGO_CSRF_COOKIE_SECURE`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`

See `backend/.env.example` for a production-safe baseline.

## Important Notes

- Predictions are not persisted to the database yet. Responses are returned in-memory per request.
- If model artifacts are missing, prediction endpoints return `503 model_unavailable`.
- Keep `backend/.env` private. Commit only `backend/.env.example`.

## Deployment Readiness Checklist

- [ ] Set `DJANGO_DEBUG=false`
- [ ] Set a strong `DJANGO_SECRET_KEY`
- [ ] Set production `DJANGO_ALLOWED_HOSTS`
- [ ] Set production `DJANGO_CSRF_TRUSTED_ORIGINS`
- [ ] Ensure model artifacts are available at runtime
- [ ] Run `python manage.py migrate` on deploy
- [ ] Use a production WSGI server (for example, `gunicorn`)

