# Frontend Port Plan — Figma shadcn UI → wired frontend

> Status: **planned (awaiting execution)**. Source design: `frontFIgma/` (Figma Make
> export — design reference only, gitignored). Target: `frontend/` (our wired app).

## Goal
Graft the Figma **design system + screens** (shadcn/ui, Tailwind v4, brand `#0E9F8E`)
onto our **existing wired frontend** (react-query, `api.ts`, types, real Leaflet map,
all endpoints). Keep the real data layer + real map; discard the export's mock data,
fake SVG map, and manual page-state navigation.

## Approach — port, don't replace
Our frontend is the skeleton (working data/map/endpoints); the Figma export is the skin
(shadcn components + theme + layouts). Graft skin onto skeleton, screen by screen.

The Figma `components/ui/*` use **standard imports** (no version-suffix quirk) — they port
directly. `cn` lives in `components/ui/utils.ts`.

## Phases

### Phase 0 — Foundation & setup
- `gitignore frontFIgma/` (keep locally as reference).
- Copy `components/ui/*` + `utils.ts` → `frontend/src/components/ui/`.
- Merge `theme.css` tokens (`:root` vars + `@theme inline` + `@layer base` + Inter) into
  `frontend/src/index.css` so `bg-primary` / `text-muted-foreground` / `rounded-xl` work.
- Add shadcn deps **surgically**: used Radix primitives, `class-variance-authority`,
  `clsx`, `tailwind-merge`, `lucide-react`, `cmdk`, `vaul`, `sonner` (+ `recharts` if
  restyling analytics). Skip MUI / react-slick / react-dnd / confetti / day-picker.
- Gate: `tsc -b && vite build` green.

### Phase 1 — App shell & shared atoms
- `Header` (sticky wordmark + city `Select` + nav), `Footer` (disclaimer) via react-router.
- shadcn atoms: `FreshBadge`, `ClinicAvatar`, `StatusBadge`, `Skeleton` — reuse `format.ts`.

### Phase 2 — SearchPage (Home + Results) — core, biggest win
- Home: hero, `Command` (cmdk) autocomplete → `fetchSuggestions`, city `Select`, popular
  chips, trust mini-cards.
- Results: filter bar (`Select`s city/category/price/sort), count, `ClinicCard`
  (shadcn `Card`) → `fetchSearch`, `PricePassport` (shadcn `Dialog`) from card data.
- **Map stays our Leaflet `ClinicMap`** — restyle pin pill + popup to match Figma; keep
  list↔map sync; mobile Список/Карта tabs + `vaul` bottom sheet. Discard Figma `MapBg`.
- Gate: build green; smoke vs live backend.

### Phase 3 — Admin (DashboardPage)
- Port `AdminPage`: KPI cards, `SourceHealthCard` + `StatusBadge`, Run-Parser button +
  `Select`, recent-runs `Table` → `fetchSourceHealth` / `fetchParseRuns` / `triggerRun`.

### Phase 4 — Analytics restyle (lower priority)
- Restyle `AnalyticsPage` to shadcn cards (+ `recharts`) → existing analytics endpoints.

### Phase 5 — Compare + Clinic detail (backend dependency)
- Backend (TDD): `GET /clinics/{id}`, `GET /clinics/{id}/services`,
  `GET /compare?service_id&clinic_ids` — service + schema + endpoint + tests.
- Frontend: `ComparePage` (shadcn `Table`, auto top-3, cheapest/stale highlight) →
  `/compare`; `ClinicDetailPage` → `/clinics/{id}`; add routes.

### Phase 6 — Cleanup & polish
- Remove superseded hand-rolled components once replaced; prune unused deps; responsive +
  a11y pass; optional eslint + a few vitest tests; final build green.

## Order & dependencies
0 → 1 → **2** → 3 → (4) → 5 → 6. Phases 2–3 = most demo value; Phase 5 gated on its backend.

## Risks
- **Tailwind v4 token merge** [MED] — absorb `@theme inline` + `:root` cleanly; watch teal
  class collisions. Mitigate: semantic tokens, build per phase.
- **React 18→19** [LOW] — Radix/shadcn fine on 19; add deps at 19-compatible versions.
- **Map restyle** [MED] — replicate pin/popup look on real Leaflet `divIcon`s.
- **New backend endpoints** [LOW] — small, TDD'd.
- **No frontend test harness** [LOW] — gate on `tsc -b` + `vite build`; vitest optional in P6.
- **Scope** [HIGH surface, LOW uncertainty] — large but mechanical.

## Open decisions
- Start with Phase 0+1+2 (design system + SearchPage)?
- Build Compare/Clinic-detail backend now (Phase 5) or defer?
- Restyle Analytics (Phase 4) or leave plain for now?
