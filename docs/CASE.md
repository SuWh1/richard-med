# Case 1 — MedServicePrice.kz (Hackathon 2025)

Original brief: [`case/ТЗ_Кейс1_MedPrice.docx`](./case/ТЗ_Кейс1_MedPrice.docx)
Service catalog: [`case/Справочник услуг.xlsx`](./case/Справочник%20услуг.xlsx)

## 1. Goal

Build an MVP web platform that aggregates prices for medical services (lab tests,
doctor visits, diagnostics) across Kazakhstan. It scrapes public clinic price
lists, normalizes heterogeneous names to one catalog, and offers a fast
search-and-compare UI — like Aviasales, but for medicine.

**Problem:** patients manually visit dozens of clinic sites to compare the price
of a blood test, a therapist visit, or an ultrasound. The market is opaque and
prices are aggregated nowhere.

## 2. Three core pillars

| Pillar | Requirement | Challenge |
|---|---|---|
| **Scraper** (3.1) | Crawl sites; extract from HTML/PDF/DOCX/Excel; dedupe; log errors; raw-vs-normalized layers; manual + cron runs | Heterogeneous sources, anti-bot, formats |
| **Normalization + catalog** (3.2) | Map "ОАК / Общий анализ крови / CBC" → one canonical service. Catalog = `id, name, synonyms, category`. Unmatched → manual queue | The hard, high-value core |
| **Search UI** (3.3) | Autocomplete, filters (city/category/price/rating/online-booking), sorted results, clinic cards, "last updated", responsive | Speed (<3s) + transparency |

Optional extras (3.4, score points): clinic map (Leaflet/Google), price-change
subscriptions, multi-clinic comparison table, price history, 2GIS/Google routes.

## 3. Data model (flat reference from the spec)

Clinic fields: `clinic_id`, `clinic_name`, `city`, `address`, `phone`,
`working_hours`, `source_url`.
Service fields: `service_id`, `service_name_raw`, `service_name_norm`,
`category` (лаборатория / приём врача / диагностика / процедура), `price_kzt`,
`currency` (KZT/USD→KZT), `duration_days`, `parsed_at`, `is_active`.

> Implementation note: split into `clinics`, `services_catalog`,
> `clinic_service_prices`, and a `raw_scrapes` layer rather than one flat table.

## 4. Suggested sources

- **Labs:** kdl.kz / kdlolymp.kz, invitro.kz, helix.kz
- **Aggregator/clinics:** doq.kz (HTML/JSON API), olymp.kz, medel.kz, mck.kz, aksai-clinic.kz
- **Geo:** 2gis.kz / Google Maps (addresses, hours)

Deliverable floor: ≥3 sources, ≥100 services, ≥50 normalized catalog positions.

## 5. Non-functional requirements

- Freshness ≥1×/day; search response ≤3s
- Show parse date; don't present data >30 days old as current
- Add sources without reworking the core (pluggable scrapers)
- One source down ≠ pipeline stops; raw data kept ≥90 days

## 6. Evaluation criteria

| Criterion | Weight |
|---|---|
| Data quality (freshness, # sources, normalization) | 25% |
| UX / search ease | 25% |
| Technical implementation (code, architecture, errors) | 20% |
| Market coverage (# clinics & cities) | 15% |
| Extra features | 15% |

## 7. The service catalog (`Справочник услуг.xlsx`)

Pre-built canonical dictionary — the target for normalization. **1,281 services,
122 specialty groups.** Columns:

| Column | Example | Meaning |
|---|---|---|
| `ID` | 1 | Specialty group id (repeats — NOT the row PK) |
| `Специальность` | Акушер-гинеколог | Specialty / category group |
| `Code` | 1…1281 | Global running service code (**the PK**) |
| `Name_ru` | Прием акушер-гинеколога | Canonical Russian name |
| `TarificatrCode` | A02.004.000 | KZ tarification code |

Tariff prefixes map to categories: `A0x` приём, `B0x` лаборатория (bulk — B06≈350),
`C0x` диагностика, `D0x`/`D99` процедура.

### Known data-quality issues to handle on import
1. 77 rows have a blank `TarificatrCode` → use `Code` as key, not the tariff code.
2. Cyrillic/Latin homoglyphs in codes (`В06` vs `B06`, `В09` vs `B09`) → normalize alphabet before matching.
3. Header + blank separator rows → filter empties.
4. No `synonyms` column → must be generated (manual/AI); this is our value-add.
5. `ID` repeats per group → `Code` is the real primary key.

## 8. Constraints

Public data only (no auth-gated scraping); respect rate limits / `robots.txt`;
no patient PII.
