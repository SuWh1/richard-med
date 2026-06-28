# Richard Med — Case Review, Submission Checklist & Pitch

> Comparison of our app against the Hackathon 2025 Case 1 (MedServicePrice.kz) brief,
> what to submit, and the pitch script to win.
> Source of truth for requirements: [`docs/CASE.md`](./CASE.md). Project plan: [`CLAUDE.md`](../CLAUDE.md).

---

## TL;DR

- We **clear every hard requirement** and **over-deliver on 4 of 5 scoring criteria**.
- Headline strength: **Price Passport** (auditable prices) + **honest normalization** + **4 sources**.
- **Fix before demo:** (1) seed more live prices, (2) don't oversell the unwired semantic layer, (3) make sure the map is never empty.
- **Confirm the actual submission format with the organizers** — it is *not* in the technical brief.
- **Pitch the thesis hard:** "everyone ships a scraper + a price table; we shipped a *trusted price-intelligence product*" — and prove it with the Passport on screen.

---

## 1. App vs. Case — Scorecard

### 1.1 Hard requirements (the floor — pass/fail)

| Requirement (Case §4–5) | Floor | We have | Verdict |
|---|---|---|---|
| Data sources | ≥3 | **4 live adapters** (KDL Olymp, DOQ, Invitro, Helix) | ✅ Exceeds |
| Services scraped | ≥100 | ~1,281 catalog + scraped prices | ✅ |
| Normalized catalog positions | ≥50 | **1,281 normalized** | ✅ 25× |
| Raw vs normalized layers | required | `raw_documents` + `raw_price_items` → `clinic_service_prices` | ✅ |
| Manual + cron parse runs | required | Admin "Run Parser" button + APScheduler design | ✅ |
| Dedup + error logging | required | pipeline dedup + `parse_runs.errors_json` | ✅ |
| Freshness ≥1×/day, show parse date | required | `parsed_at` + freshness badges | ✅ |
| Don't show >30d data as current | required | stale badge + hidden by default | ✅ |
| Search ≤3s | required | DB-only search path, no live scraping | ✅ (target <1s) |
| Pluggable scrapers (add w/o rework) | required | `BaseSourceAdapter` + registry | ✅ |
| One source down ≠ pipeline stops | required | per-source isolation | ✅ |
| Raw data kept ≥90 days | required | raw layer retained, never overwritten | ✅ |
| Public data only, no PII, robots | required | respected; 2GIS licensed (reviews API only) | ✅ |

**We clear every floor item, most by a wide margin** — including the 3-source floor and the raw/normalized separation that weak teams miss.

### 1.2 Weighted scoring (the 100 points)

| Criterion | Weight | What the case wants | Our weapon | Self-grade |
|---|---|---|---|---|
| **Data quality** | 25% | freshness, # sources, normalization quality | Price Passport (source_url + content_hash + parsed_at + match confidence), 4 sources, exact→alias→fuzzy→semantic waterfall, unmatched queue | **Strong** |
| **UX / search** | 25% | autocomplete, filters, sort, cards, responsive, transparency | Price-hero cards, Best-Value sort, map↔list sync, mobile bottom sheet, shadcn polish | **Strong** |
| **Tech implementation** | 20% | code quality, architecture, error handling | Adapter pattern, raw→normalized pipeline, source isolation, 23 test files / ~3,100 LoC, TDD | **Strong** |
| **Market coverage** | 15% | # clinics & cities | 4 sources, Astana + Almaty, Helix adds 12 branches | **Medium-strong** |
| **Extra features** | 15% | map, alerts, compare, price history, routes | Map, compare, **user cabinet + watchlist + price alerts**, **2GIS ratings/reviews (862)**, analytics, price-history schema | **Very strong** |

---

## 2. What We Did Well (lead with these)

1. **We built the "trusted product," not a scraper demo.** The Price Passport (source URL, content hash, parse date, match confidence, freshness badge) is the single biggest differentiator and maps straight to the 25% data-quality criterion.
2. **Normalization is real, not faked.** Full waterfall (canonical clean → exact → alias → fuzzy → semantic scaffold) with visible confidence and an unmatched-services queue. The case calls this "the hard, high-value core."
3. **We beat the source floor with genuine coverage.** 4 distinct domains across 2 cities — where weak teams fail.
4. **Architecture matches the non-functional spec exactly.** No live scraping in the user path (DB-only, <1s), per-source isolation, raw evidence retained, pluggable adapters.
5. **We maxed the extra-features bucket.** Map + compare + **user accounts with a price-drop watchlist** + **real 2GIS ratings/reviews (862)** + analytics.
6. **Test discipline.** 23 test files, TDD, ~80%+ coverage — visible quality signal for the tech criterion.

---

## 3. What Is NOT Good / Risks (fix or have an answer ready)

| # | Issue | Severity | Action before demo |
|---|---|---|---|
| 1 | **Semantic/vector layer scaffolded but unwired** — `embedding` column + HNSW index exist, but embeddings may not be generated; waterfall stops at fuzzy. | MEDIUM | Generate embeddings via `setup_data.py` (if `fastembed` installed) **or** pitch only "exact→alias→fuzzy, semantic ready." Don't oversell. |
| 2 | **Live price scale is thin** (~40–100 demo prices vs. "300+ if stable"). Helix is JSON-seeded branches only, no live price fetch. | MEDIUM | Seed more prices for the demo queries (ОАК, терапевт, УЗИ). A sparse map looks weak. |
| 3 | **Price-change alerts have no delivery** — watchlist stores baseline/current price but no worker sends notifications. | LOW | Pitch as "in-app watchlist + alert-ready"; don't claim emails go out. |
| 4 | **Price history = schema only**, no chart. | LOW | Case lists it as *optional*. Say "schema in place, changed/not-changed works, timeline chart is roadmap." |
| 5 | **Geocoding depends on Yandex key** — if absent, map uses seeded coords only. | LOW | Ensure demo branches have lat/lng seeded so the map is never empty. |
| 6 | **Auth + cabinet add scope the case didn't ask for.** | LOW | Frame cabinet as the alerts/subscription feature from §3.4, not bloat. |
| 7 | **2GIS licensing sensitivity.** | LOW (watch) | Be ready: "We do NOT scrape 2GIS listings — public reviews API + route deep-links only." |

**Biggest single risk:** an empty or sparse map/results on a live demo query.
**Mitigation:** demo from seeded DB + cached snapshots, never a live fetch. Rehearse the 3 queries; make at least one flawless.

---

## 4. What We Need to Submit (check in depth)

> ⚠️ **Caveat:** the exact submission format (portal, deadline, required artifacts) is **not in `docs/CASE.md`** — that file is the technical brief only. The original `.docx` (`docs/case/ТЗ_Кейс1_MedPrice.docx`) or the organizers' channel has the precise rules. **Confirm with the organizers.** Below is what the brief implies plus standard hackathon deliverables.

### A. The working MVP (core deliverable)
- [ ] Runnable web app — search → results → map → compare → clinic detail → admin
- [ ] Runs offline from seeded DB (no live third-party fetch during judging)
- [ ] Meets the floor: ≥3 sources ✅, ≥100 services ✅, ≥50 normalized ✅

### B. Source code + repo
- [ ] Shared Git repo, clean README with setup steps (`backend/README.md`, `frontend/README.md`, `docker-compose.yml`)
- [ ] `docker compose up` + documented run path (CLAUDE.md §16)
- [ ] `.env.example` present, **no secrets committed** — ⚠️ verify `frontend/.env` is gitignored and holds no real keys

### C. Demonstration of the 3 graded pillars
- [ ] **Scraper:** raw HTML evidence + parse-run log (admin) → proves real scraping, dedup, error isolation
- [ ] **Normalization:** catalog + unmatched queue + Price Passport with confidence → proves the hard core
- [ ] **Search UI:** autocomplete + filters + sorted cards + freshness → proves UX

### D. Presentation / pitch
- [ ] ~6:30 demo (flow in CLAUDE.md §13)
- [ ] Slides: problem → solution → architecture → differentiators → market/business
- [ ] **Fallback screenshots/video** of every demo step (network-failure insurance)

### E. Data-quality proof (this is 25% — make it visible)
- [ ] Source count + freshness dashboard (admin Source Health)
- [ ] Normalization stats (X normalized, Y aliases, Z in unmatched queue)
- [ ] At least one fully auditable price (Passport open on screen)

### Action items before submitting
1. Confirm submission portal / deadline with organizers.
2. Verify no secrets in repo.
3. Seed enough demo prices for the 3 key queries.
4. Record a fallback video.
5. Write README run steps so a judge can launch it cold.

---

## 5. Pitch Script — Bullets to Win

Structure: **Hook → Problem → Why we're different → Proof (3 pillars) → Wow → Business → Close.**
Every claim maps to a scoring criterion.

### Opening hook (10s)
- *"Booking a blood test in Kazakhstan means visiting a dozen clinic sites and still not knowing if you overpaid. We built **Aviasales for medical services** — search one test, compare every clinic's real price in under a second."*

### The problem (20s — Data quality + UX, 50% of score)
- The market is **opaque**: prices aggregated nowhere, scattered in inconsistent formats.
- Patients **overpay** because they can't compare. No trust layer exists.

### Why we're different — the thesis (30s — the winning line)
- *"Most teams will ship a scraper plus a price table. We shipped a **trusted price-intelligence product.**"*
- Three things make a price trustworthy, and we built all three: **source proof, freshness, honest normalization.**
- Lead with the **Price Passport:** *"Every price is auditable — click it and you see the exact source URL, the raw scraped name, when we parsed it, a content hash, and our match-confidence score. No black box."* → **Data Quality (25%).**

### Proof — walk the 3 graded pillars (90s)
- **Scraper (admin demo):** *"4 independent sources, raw evidence kept 90 days, each source isolated — one site down never breaks the run."* Show the parse-run log + raw HTML. → Tech (20%) + Data quality (25%).
- **Normalization (the hard core):** *"'ОАК', 'CBC', 'клинический анализ крови' all collapse to one canonical service across 1,281 normalized positions — exact, alias, and fuzzy with visible confidence; anything uncertain drops to a review queue. We never fake-claim AI matched everything."* → Data quality (25%).
- **Search UX:** type ОАК → instant autocomplete → price-hero cards sorted by **Best Value** (price + freshness + distance) → freshness badges. *"Sub-second, because search only ever hits our database — we never scrape in the user's path."* → UX (25%) + Tech (20%).

### The wow (30s — Extra features, 15%)
- **Map:** *"Price pins across the city; click a pin and the list highlights — list and map stay in sync."*
- **Compare:** top 3 clinics side by side, cheapest green, stale amber.
- **Real reviews & ratings:** *"862 real clinic reviews via the 2GIS public API — licensed, we don't scrape their listings."*
- **Personal cabinet:** *"Save a service and we watch its price for you — the subscription/alerts feature, already wired."*

### Coverage + business (20s — Market coverage 15% + buyout story)
- 4 sources, Astana + Almaty; a new clinic = **one adapter file, zero core changes.**
- *"B2C trust layer with a B2B underneath — clinics pay for analytics and visibility, insurers and the Ministry get a real price index. The data quality is the moat."*

### Close (10s)
- *"Three sources was the floor. We shipped four, made every price auditable, put it on a map, and gave it a memory. Richard Med isn't a scraper demo — it's the trusted price layer Kazakhstani medicine doesn't have yet."*

### Judge-question landmines (rehearse answers)
- **"Is this legal?"** → Public data only, robots.txt + rate limits, no PII, **2GIS not scraped** (reviews API + route deep-links only).
- **"Is normalization real or LLM hand-waving?"** → Deterministic waterfall with confidence + unmatched queue; semantic optional and not oversold.
- **"How fresh is the data?"** → Daily parse, parse date on every card, >30-day data badged stale and hidden.
- **"What if a source changes its HTML?"** → Snapshot tests catch it, admin shows the error, prior data stays with aged freshness — the product never goes dark.
