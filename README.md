# Richard Med

Aggregator and price-comparison platform for medical services in Kazakhstan —
"Aviasales for medicine." Scrapes public clinic price lists, normalizes service
names against a single catalog, and lets users search and compare prices.

> Hackathon 2025 — Case 1 (MedPrice / MedServicePrice.kz). Full spec in [`docs/`](./docs).

## Repository layout

```
richard-med/
├── backend/     FastAPI + PostgreSQL — API, scrapers, normalization
├── frontend/    Vite + React + TypeScript + Tailwind — search & compare UI
├── docs/        Case spec, service catalog, architecture notes
└── docker-compose.yml   Local PostgreSQL (and optional services)
```

## Full setup — from clone to running app

Per-app details live in [`backend/README.md`](./backend/README.md) and
[`frontend/README.md`](./frontend/README.md); this is the complete end-to-end runbook.

**Prerequisites:** Docker + Docker Compose, Python 3.11+, Node 20+.

### 1. Database (PostgreSQL + pgvector)

From the repo root:

```bash
docker compose up -d db          # starts pgvector/pgvector:pg16 on localhost:5432
docker compose ps                # confirm "db" is healthy before continuing
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env             # defaults match docker-compose; no edits needed for local

alembic upgrade head             # create schema (runs CREATE EXTENSION vector + indexes)
```

### 3. Load data

Order matters — the catalog must exist before prices can normalize against it.

```bash
# a) Import the 1,281-service catalog + seed aliases (unblocks autocomplete + matching)
python -m app.scripts.import_catalog

# b) Seed demo clinics, branches (with coords), and sample prices for the demo
python -m app.scripts.seed_demo

# c) OPTIONAL — backfill real lat/lng via Yandex Geocoder.
#    Skips automatically if YANDEX_GEOCODER_API_KEY is unset (keeps seeded coords).
python -m app.scripts.geocode_branches
```

### 4. Run the API

```bash
uvicorn app.main:app --reload --port 8001
```

- API docs (Swagger): http://localhost:8001/docs
- Health: http://localhost:8001/health

### 5. Run the parsers (populate live prices from sources)

Parsers run **offline**, via the admin endpoint — never in the user search path. With the
API running, trigger a run in the background (cities: `Астана`, `Алматы`):

```bash
# Run all registered sources (KDL Olymp, DOQ) for Astana
curl -X POST "http://localhost:8001/api/v1/admin/parsers/run?city=Астана"

# Or one source for one city
curl -X POST "http://localhost:8001/api/v1/admin/parsers/run?source=kdl_olymp&city=Алматы"

# Watch results / source health
curl "http://localhost:8001/api/v1/admin/parse-runs"
curl "http://localhost:8001/api/v1/admin/source-health"
```

### 6. Frontend

```bash
cd frontend
npm install
cp .env.example .env             # VITE_API_BASE_URL defaults to http://localhost:8001/api/v1
npm run dev                      # http://localhost:5173
```

### Tests & lint

```bash
cd backend && pytest && ruff check .
cd frontend && npm test && npm run lint
```

### Alternative — everything in Docker

`docker compose up` brings up the DB **and** the backend (the backend container runs
`alembic upgrade head` on start and serves on **http://localhost:8001**). You still run the
data-load scripts (step 3) and the frontend (step 6) yourself.

## Stack

| Layer    | Choice                                  |
|----------|-----------------------------------------|
| Frontend | Vite, React, TypeScript, Tailwind CSS   |
| Backend  | FastAPI, SQLAlchemy, Pydantic           |
| Database | PostgreSQL                              |
| Scraping | Pluggable scraper interface (per source)|
