# KDL Olymp — `analysis-data` price endpoint

KDL's own frontend loads its price list from this internal JSON API. It's public and
unauthenticated, and it returns the **full** catalog with prices, durations, and codes —
far richer than scraping the rendered HTML page. This is the source our KDL adapter should
use. `robots.txt` does **not** disallow `/api/`.

## Endpoint

```
GET https://kdlolymp.kz/api/analysis-data
```

### Query parameters

| Param        | Required | Example            | Meaning |
|--------------|----------|--------------------|---------|
| `lang`       | yes      | `ru-RU`            | Response language |
| `city_slug`  | yes      | `almaty`, `astana` | City to price for |
| `per-page`   | yes      | `100`              | **Categories** per page (not analyses). `100` returns all 49 in one page |
| `page`       | yes      | `1`                | 1-based page index |
| `ids`        | no       | `37,55,39`         | Filter to specific **category** ids (comma-separated). Omit = all categories |
| `search`     | no       | `глюкоза`          | Free-text filter on analysis name. Must be URL-encoded |

> `per-page` counts **categories**, not services. Each category carries all its analyses in
> one `analysis[]` array, so `per-page=100&page=1` returns the entire catalog in a single call.

## Pagination — read `_meta`

```json
"_meta": { "totalCount": 49, "pageCount": 1, "currentPage": 1, "pageSize": 100 }
```

`totalCount` = number of categories. Loop `page=1..pageCount`, or just set `per-page=100`
(only 49 categories exist) and take page 1.

## Response shape

```jsonc
{
  "data": [
    {
      "id": 55,                                   // category id (use in `ids=`)
      "translation": { "title": "Гематология" }, // category name
      "analysis": [
        {
          "id": 1151,
          "code": "1151",                         // source service code → Price Passport
          "slug": "klinicheskiy-analiz-krovi-oak",// builds the proof URL (below)
          "translation": { "title": "Общий анализ крови (ОАК без СОЭ)" },
          "price": {
            "price": 3980,                        // ₸
            "min_duration": 1,                    // turnaround → duration_min
            "max_duration": 1                     // → duration_max
          }
        }
      ]
    }
  ],
  "_meta": { "totalCount": 49, "pageCount": 1, "currentPage": 1, "pageSize": 100 }
}
```

Per-service proof URL (for `source_url` / Price Passport):
`https://kdlolymp.kz/analysis/<slug>`

## Worked examples

```bash
# Full catalog, Almaty (49 categories, ~1,682 analyses, ~7.8 MB)
curl -s "https://kdlolymp.kz/api/analysis-data?per-page=100&lang=ru-RU&city_slug=almaty&page=1"

# Astana (~1,686 analyses)
curl -s "https://kdlolymp.kz/api/analysis-data?per-page=100&lang=ru-RU&city_slug=astana&page=1"

# Filter to categories Профили(37) + Гематология(55) + Биохимия крови(39)
curl -s "https://kdlolymp.kz/api/analysis-data?per-page=100&lang=ru-RU&city_slug=almaty&ids=37,55,39&page=1"

# Free-text search (URL-encode Cyrillic; use -G --data-urlencode)
curl -s -G "https://kdlolymp.kz/api/analysis-data" \
  --data-urlencode "lang=ru-RU" --data-urlencode "city_slug=almaty" \
  --data-urlencode "per-page=100" --data-urlencode "page=1" \
  --data-urlencode "search=глюкоза"
```

## How we use it (per CLAUDE.md Rule 1)

- Fetch **offline**, once daily, with the polite client — never in the user search path.
- Save each raw JSON response as a `raw_document` (evidence, kept ≥90 days).
- We pull the **full** catalog (no `ids`/`search`) and normalize against our own catalog.
  `ids`/`search` are the site's UI filters — useful for spot-checks, not for our ingest,
  since user search is served from our DB, not a live call to KDL.

## Category id → name (all 49)

| id | name | id | name |
|----|------|----|------|
| 55 | Гематология | 37 | Профили |
| 39 | Биохимия крови | 24 | Гормоны |
| 51 | Диагностика бесплодия | 45 | Мониторинг беременности |
| 49 | Инфекции | 5 | Инфекции ИФА |
| 43 | ПЦР | 22 | ПЦР Гепатиты |
| 10 | Серологические маркеры инфекционных заболеваний | 58 | Серология |

> Full list comes back in the `data[].id` / `translation.title` of any unfiltered call.
