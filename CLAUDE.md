# Richard Med — Project Guide (single source of truth)

> **Read this first.** This file is the shared plan for every developer and every AI
> agent (Claude, Codex, Cursor, etc.) working in this repo. One goal, one plan.
> If something here conflicts with an ad-hoc instruction, raise it — don't silently diverge.
>
> Source documents this guide is distilled from:
> - [`docs/CASE.md`](./docs/CASE.md) — the hackathon brief (Case 1, MedPrice).
> - `docs/MedServicePrice_Winning_Blueprint.xlsx` — the 21-sheet execution playbook.
> - `docs/case/` — the original `.docx` brief + `Справочник услуг.xlsx`.

---

## 1. What we are building

**Richard Med** is our entry for Hackathon 2025 Case 1 ("MedServicePrice.kz"): a
price-aggregator for medical services in Kazakhstan — **"Aviasales for medicine."**
A patient searches one service (e.g. ОАК) and instantly compares real clinic prices
across the city, with source proof, freshness, a map, and a route — instead of
manually visiting a dozen clinic sites.

**One-line pitch:** Search one service, compare real clinic prices, see source proof,
freshness, map, and route.

## 2. The winning thesis (do not lose this)

> **Most teams will ship a scraper + a price table. We ship a _trusted price
> intelligence product_:** normalized catalog, source proof, freshness, map UX,
> and operator tooling.

Everything we build must reinforce *trust* and *usability*, because that is what
separates us from a generic LLM-generated scraper demo. The differentiators:

- **Price Passport** — every price is auditable: `source_url`, raw service name,
  normalized service, `parsed_at`, `content_hash`, match confidence, freshness badge.
- **Best-Value ranking** — default sort blends price + freshness + distance + duration,
  not just "cheapest" (user can still pick cheapest).
- **Source Health** — operator view of per-source success/failure, items parsed, errors.
- **Honest normalization** — exact → alias → fuzzy → (optional) semantic → unmatched
  queue, with visible confidence. We never claim "AI matched everything."

## 3. Non-negotiable architectural rules

1. **No live scraping in the user path.** Parsers run offline as a background pipeline,
   store raw evidence, and write to the DB. **User search only ever queries the DB.**
   Target search latency <1s.
2. **One broken source never breaks the run or the demo.** Each source is isolated;
   a failure is logged and the other sources continue. UI keeps prior data, freshness ages.
3. **Never overwrite evidence.** Raw documents + raw price items are retained (≥90 days
   per the brief). Prices are versioned, source-backed facts.
4. **Never show stale data as current.** Anything `parsed_at` >30 days is badged stale
   and hidden from normal results by default.
5. **Public data only.** Respect `robots.txt`, apply per-source rate limits, no patient
   PII, no auth-gated pages. 2GIS business data is **not** scraped (licensed) — use
   external route deep-links only.

## 4. Scope — the agreed 2-person plan

We are **2 people**. The blueprint is written for a 5-role team, so we cut hard to the
highest-scoring core and **one** headline differentiator.

**Headline differentiator decision: Map-first + a light read-only Admin Source Health
page.** (Map = the visual "wow" for UX + extra-features points; the light Admin page
still lets us tell the data-quality / buyability story without building the full console.)

| ✅ Build (scores the most) | ❌ Cut / fake for MVP |
|---|---|
| Search + autocomplete over the 1,281-service catalog | Email price alerts → waitlist button only |
| Price-hero result cards: price, freshness, source proof | Full price-history chart → schema only + "changed/not changed" |
| **Price Passport** modal | Invitro/Helix parsers → "planned source," not demo-critical |
| **2 guaranteed sources: KDL Olymp (labs + branches) + DOQ (visits)** | Distance/geolocation sort → city filter + map pins only |
| Best-Value + Cheapest sort | Clinic branch editor, CSV export, anomaly UI |
| Compare table (top 3) | Semantic/LLM matching → optional; exact+alias+fuzzy is enough |
| Leaflet map: price pins, popup, list↔map sync | Unmatched-queue editing UI → queue exists in DB, no rich UI |
| Catalog import + alias seeding + match waterfall | |
| Freshness rules + light Admin Source Health (KPI cards + Run Parser) | |

**Never cut:** source proof, freshness badges, price cards, the 2 stable sources,
Source Health KPIs. **Invitro** is optional, only if it's stable by mid-build.

**Role split:**
- **Person A — Data/Backend:** DB model, catalog importer, KDL + DOQ adapters,
  normalization waterfall, search/compare/map-pins API, `parse_runs`/`source_health`.
- **Person B — Frontend:** home/search, result cards + Price Passport, compare table,
  Leaflet map + popups + list sync, light admin page, Russian copy.

## 5. Judging-weight strategy

| Criterion | Weight | Our weapon |
|---|---|---|
| Data quality | 25% | Price Passport, raw evidence, freshness badges, Source Health |
| UX / search | 25% | Price-hero cards, Best-Value sort, map↔list sync, mobile bottom sheet |
| Tech implementation | 20% | Adapter architecture, raw→normalized pipeline, error isolation |
| Market coverage | 15% | 2 stable sources, Astana + Almaty cities |
| Extra features | 15% | Map, compare, price-history skeleton, alerts waitlist |

**Scoreboard targets:** ≥1,200 normalized services (we import 1,281), 2 stable sources,
300+ price items if stable / 120+ minimum demo seed, Astana + Almaty, <1s search.

## 6. Tech stack

| Layer | Choice |
|---|---|
| Frontend | Vite + React 19 + TypeScript + Tailwind CSS v4 |
| Backend | FastAPI + SQLAlchemy 2.0 + Pydantic |
| Database | PostgreSQL 16 + **pgvector** (semantic search) + `pg_trgm`/full-text (lexical) — image `pgvector/pgvector:pg16` |
| Parsing | Python adapters (`requests`/`httpx` + BeautifulSoup; Playwright only if needed) |
| Matching | RapidFuzz (fuzzy) + **multilingual embeddings** (e.g. `multilingual-e5`, local/no-API) for semantic |
| Map | Leaflet + OpenStreetMap tiles (self-stored coordinates) |

## 7. Repository layout

```
richard-med/
├── CLAUDE.md            ← this file (single source of truth)
├── AGENTS.md            ← pointer to this file for non-Claude agents
├── docker-compose.yml   ← local PostgreSQL
├── backend/             FastAPI — see backend/README.md
│   └── app/
│       ├── main.py         app + /health
│       ├── core/config.py  env-driven settings
│       ├── api/v1/         routers + endpoints
│       ├── db/             Base + session/engine
│       ├── models/         SQLAlchemy ORM (the data model in §8)
│       ├── schemas/        Pydantic request/response
│       ├── services/       business logic (normalization, search, catalog import)
│       └── scrapers/       pluggable source adapters (BaseSourceAdapter)
├── frontend/            Vite + React — see frontend/README.md
│   └── src/{components,pages,hooks,lib,types}
└── docs/               case brief, blueprint, CASE.md
```

## 8. Data model

Prices are versioned, source-backed facts. ~7 tables matter for MVP (rest are
post-hackathon). Generate our own keys — **do not trust the Excel `ID`/`Code`
columns** (they had broken `#REF!` cells; use `Services_Clean.service_key`).

| Table | Key fields | Purpose |
|---|---|---|
| `clinics` | id, name, website_url, source_name | Clinic brand (KDL Olymp, Invitro, DOQ clinic) |
| `clinic_branches` | id, clinic_id, city, address, lat, lng, phone, working_hours | Location for map/route (coords seedable for demo) |
| `services` | id, name_ru, category, specialty, tarificatr_code, **embedding** (pgvector) | Normalized catalog (imported from `Services_Clean`); embedded once at import |
| `service_aliases` | id, service_id, alias, source, confidence | Synonyms + learned aliases — drives autocomplete & match |
| `raw_documents` | id, source_name, source_url, content_hash, raw_html, fetched_at, status_code | Raw page evidence (kept ≥90 days) |
| `raw_price_items` | id, raw_document_id, clinic_raw, service_name_raw, price_raw, duration_raw, metadata_json | Raw extracted rows pre-normalization |
| `clinic_service_prices` | id, clinic_id, branch_id, service_id, price_kzt, duration_min/max, parsed_at, source_url, is_active | Search-ready active prices |
| `price_history` | id, source_key, old_price, new_price, changed_at, percent_change | Change tracking (schema now, chart later) |
| `parse_runs` | id, source_name, city, status, started_at, finished_at, items_found, items_saved, errors | Source Health / admin |
| `unmatched_services` | id, raw_item_id, raw_name, suggested_service_id, confidence, status | Review queue (DB only for MVP) |
| `source_health` | source_name, last_success_at, success_rate_7d, stale_count, last_error | Operator view |

**Category enum (4 values):** `лаборатория`, `приём врача`, `диагностика`, `процедура`.

**Indexes:** GIN/full-text on `services.name_ru` + aliases; `pg_trgm` for fuzzy;
**HNSW (pgvector)** on `services.embedding` for semantic nearest-neighbor;
`clinic_service_prices(service_id, city, price_kzt, parsed_at)` partial where `is_active`;
unique `raw_documents(source_url, content_hash)`. First migration runs `CREATE EXTENSION vector;`.

## 9. Normalization — the catalog & match waterfall

**Catalog source: `Services_Clean` sheet** in the blueprint (1,281 import-ready rows):
`service_key (svc_0001…svc_1281) | source_ID | specialty | source_Code | name_ru |
tarificatr_code | category | import_note | suggested_alias_seed`.

- Category already mapped to the 4-value enum (лаборатория 525 / приём врача 407 /
  диагностика 276 / процедура 73).
- 43 duplicate `name_ru` groups (94 rows) — dedupe by name for autocomplete, disambiguate
  by `specialty`.
- `suggested_alias_seed` is only filled for 8 rows → **building `service_aliases` is real
  work we own.** Seed from the blueprint's synonym list (sheet `07_Normalization`):
  ОАК/CBC/клинический анализ крови → Общий анализ крови; ОАМ; глюкоза/сахар крови; ТТГ/TSH;
  Витамин D; Ферритин; УЗИ ОБП; ЭКГ/ECG; Прием терапевта/педиатра/гинеколога; etc.

**Match waterfall (raw name → catalog):**
1. Canonical clean (lowercase, ё→е, strip punctuation/dup spaces, Latin/Cyrillic homoglyphs).
2. Exact match on cleaned `name_ru` → confidence 1.00.
3. Alias match via `service_aliases` → 0.95–1.00.
4. Fuzzy (RapidFuzz token_set_ratio): ≥0.88 auto-match, 0.75–0.88 suggest.
5. **Semantic (pgvector):** embed the raw name, nearest-neighbor against `services.embedding`,
   accept above a cosine threshold. Runs **offline in the parser pipeline**, never in the user path.
6. Below threshold → `unmatched_services` queue; once an operator matches, save the alias.

### User-facing search = hybrid (lexical first, vector fallback)
A user search is two steps: **(a) resolve the typed query → a catalog service, (b) fetch prices**
by `service_id` (a plain keyed lookup, never vectors).

For step (a):
- **Autocomplete-as-you-type → lexical only.** Postgres `pg_trgm` + full-text over `name_ru` +
  `service_aliases`. Instant, prefix-aware, deterministic. **Never embed per keystroke.**
- **On submit with no good lexical hit → semantic fallback.** Embed the query **once**, run a
  pgvector nearest-neighbor against the catalog (e.g. "кровь на сахар" → `Глюкоза`). Return the
  best service + confidence; still below threshold → "did you mean…?", never a silent wrong match.
- This stays within Rule 1: embedding runs in **our** backend (local model) against **our** DB —
  no third-party fetch during search.

## 10. Data sources

| Priority | Source | URL | Use |
|---|---|---|---|
| **P0 stable** | KDL Olymp price list | `kdlolymp.kz/pricelist/astana` | Main lab data |
| **P0 stable** | KDL Olymp branches | `kdlolymp.kz/cabinets` | Map / clinic metadata |
| **P0 stable** | DOQ doctor pages | `doq.kz/doctors/astana/terapevt` | Doctor-visit category |
| P1 optional | Invitro KZ | `invitro.kz` | Only if stable by mid-build (dynamic → Playwright) |
| Support | Leaflet + OSM | `leafletjs.com` | Map display |
| Future only | 2GIS | `dev.2gis.com` | Licensed — route deep-links now, integration later |

**Adapter contract** (`app/scrapers`): `fetch(city) → RawDocument[]`,
`parse(raw_doc) → RawPriceItem[]` (**no DB writes in parse**), `clean(raw_item)`,
`identity()`, `test_snapshot()` (parse a saved HTML fixture → expected row count + sample
prices). Pipeline: config → fetch → raw save → extract → validate → normalize → upsert/dedup
→ health log → publish.

### Fetch cadence
- **Production:** once per day per source, **off-peak** (nightly cron/APScheduler), with polite
  per-request delays. Satisfies the brief ("не реже 1 раза в сутки") and keeps prices in the
  green <7-day band. Prices change slowly — daily is plenty; more often just risks blocks.
- **Manual trigger:** admin **"Run Parser"** button hits the same pipeline on demand.
- **During the hackathon:** fetch only a few times to seed the DB + save raw snapshots; the
  **demo runs entirely from the seeded DB + cached snapshots** — never a live third-party fetch.

## 11. API surface

```
GET  /services?q=             autocomplete from catalog + aliases
GET  /search                  q, city, category, price_min/max, sort, lat, lng → cards + pins
GET  /services/{id}/prices    all active prices for one service
GET  /clinics/{id}            clinic/branch details
GET  /clinics/{id}/services   all active services for a clinic
GET  /compare                 service_id + clinic_ids → comparison table
GET  /map/prices              service_id + city/bounds → pins w/ price + freshness
POST /admin/parsers/run       run a selected parser/city
GET  /admin/source-health     last run, success rate, errors, stale count
```

## 12. Frontend / UX rules

- **Price is the hero** — largest element on every card; first visual anchor.
- **Freshness badges:** green `Обновлено сегодня` (≤7d), neutral (≤30d), amber
  `Цена требует обновления` (>30d, hidden by default).
- **Sorts:** Best Value (default) = `price 45% + freshness 25% + distance 15% +
  duration 10% + source_conf 5%`; Cheapest; Newest.
- **Map:** price pins (`1 880 ₸`), clusters (`5 from 1 880 ₸`), click → popup with price /
  trust / actions and highlights the matching list row. Mobile → draggable bottom sheet.
- **Compare:** auto-select top 3; green = cheapest, amber = stale, grey = unknown.
- **Russian copy is pre-written** in the blueprint sheet `17_UI_Copy` — use it verbatim.
- **No medical advice.** Disclaimer: *Информация о ценах носит справочный характер.
  Перед лечением обратитесь к врачу.*

## 13. Build order (milestones)

1. **Import `Services_Clean` → `services` + seed `service_aliases`** (do first; unblocks
   autocomplete + matching).
2. Spike KDL + DOQ; save raw HTML snapshots; confirm `robots.txt`.
3. Backend: data model + 2 adapters writing raw + normalized rows. Frontend: home + cards
   against seeded data.
4. Search / compare / map-pins API ↔ map + compare UI.
5. Price Passport + freshness + light Source Health page.
6. Seed DB, rehearse the ~6:30 demo, prepare fallback screenshots.

**Demo flow (≈6:30):** Problem → Search ОАК → Results (Best Value) → Map → Compare top 3 →
Clinic detail → Admin Source Health / Run Parser → Price Passport / matching → Business close.
Prep 3 queries (ОАК, терапевт, УЗИ брюшной полости); at least one must be flawless. Always
demo from seeded DB + cached snapshots, never live third-party fetches.

## 14. Top risks (and the fallback story)

- **Source HTML changes/blocks** → cached snapshots + adapter snapshot tests; admin shows
  the error, prior data stays with aged freshness.
- **Normalization mismatch** → confidence thresholds + unmatched queue; low-confidence rows
  are never shown as exact matches.
- **Missing map coordinates** → seed lat/lng for demo branches; address-only card otherwise.
- **Live-demo network issues** → seeded DB + screenshots/video backup; demo runs locally.
- **Legality questions** → public data, robots/rate limits, source attribution, no PII,
  2GIS not scraped.

## 15. Engineering conventions (every agent follows these)

- **Immutability:** never mutate inputs in place; return new objects/copies.
- **Small, focused files:** 200–400 lines typical, 800 hard max; functions <50 lines;
  organize by feature/domain. Extract utilities rather than growing a module.
- **Comments:** default to none. Only a single-line comment when the *why* can't be
  recovered from the code itself (external quirk, cross-module invariant). No section
  banners, no narration of what code does.
- **Errors:** handle explicitly at every layer; user-friendly messages in UI; detailed
  context in server logs; never silently swallow. Validate all external input at boundaries
  (Pydantic on the API, parse-time validation in adapters).
- **Security:** no hardcoded secrets (env only); parameterized queries; rate-limit scrapers;
  never leak internals in error messages.
- **Tests (TDD):** write the test first (red → green → refactor). Target 80%+ coverage.
  `it()`/test names start with **"should"**. Don't mock the DB into hiding real behavior.
- **Git:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `test:`, `docs:`).
  **Subject line only** unless asked for a body. **Never `git push` without explicit
  permission** — commit, then ask. Default branch is `main`.
- Run a code review (and security review for auth/input/DB/scraper code) before merging.

## 16. Setup & run

```bash
docker compose up -d db                         # PostgreSQL

cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && cp .env.example .env
uvicorn app.main:app --reload                   # http://localhost:8000/docs

cd frontend && npm install && cp .env.example .env
npm run dev                                      # http://localhost:5173
```

---

**Open decisions (change here if the team agrees):**
- Differentiator = Map-first + light Admin (alt: Admin-heavy for a stronger buyout story).
- Guaranteed sources = KDL + DOQ; Invitro optional-if-stable.
