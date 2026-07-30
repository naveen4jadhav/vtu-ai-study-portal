# VTU AI Study Portal — Backend (Module 1 + Module 2)

Production-grade FastAPI backend foundation, extended with authentication
and user management (Module 2).

## Run locally (without Docker)

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run with Docker

```bash
cd backend
cp .env.example .env
docker compose up --build
docker compose exec backend alembic upgrade head
```

## Endpoints

- `GET /` — project metadata
- `GET /health` — liveness health check
- `GET /api/v1/version` — version + environment info
- `GET /api/v1/health` — versioned health check
- `GET /api/v1/health/db` — database connectivity check
- `GET /api/v1/docs` — Swagger UI

### Authentication (Module 2)

- `POST /api/v1/auth/register` — create a new (STUDENT) account
- `POST /api/v1/auth/login` — authenticate, returns access + refresh tokens
- `POST /api/v1/auth/refresh` — rotate a refresh token for a new token pair
- `POST /api/v1/auth/logout` — revoke the current access token (and optional refresh token)
- `GET /api/v1/auth/me` — current authenticated user's profile
- `POST /api/v1/auth/change-password` — change the current user's password

## Alembic

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## Tests

Auth tests are integration tests and require a reachable PostgreSQL
instance matching `DATABASE_URL` in `.env`:

```bash
docker compose up -d db
pytest -v
```

