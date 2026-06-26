# Backend — Richard Med

FastAPI + SQLAlchemy + PostgreSQL.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Start PostgreSQL (from repo root):

```bash
docker compose up -d db
```

## Run

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health:   http://localhost:8000/health

## Test & lint

```bash
pytest
ruff check .
```

## Layout

```
app/
├── main.py          FastAPI app + health endpoint
├── core/config.py   Settings (env-driven)
├── api/v1/          Versioned routers and endpoints
├── db/              Declarative Base + session/engine
├── models/          SQLAlchemy ORM models
├── schemas/         Pydantic request/response schemas
├── services/        Business logic (normalization, catalog, search)
└── scrapers/        Pluggable per-source scrapers (BaseScraper interface)
```
