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

## Quick start

Each app has its own README with setup steps:

- Backend → [`backend/README.md`](./backend/README.md)
- Frontend → [`frontend/README.md`](./frontend/README.md)

Bring up the database:

```bash
docker compose up -d db
```

## Stack

| Layer    | Choice                                  |
|----------|-----------------------------------------|
| Frontend | Vite, React, TypeScript, Tailwind CSS   |
| Backend  | FastAPI, SQLAlchemy, Pydantic           |
| Database | PostgreSQL                              |
| Scraping | Pluggable scraper interface (per source)|
