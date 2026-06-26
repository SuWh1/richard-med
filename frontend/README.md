# Frontend — MedServicePrice.kz

Vite + React + TypeScript + Tailwind CSS (v4).

## Setup

```bash
cd frontend
npm install
cp .env.example .env
```

## Run

```bash
npm run dev      # http://localhost:5173
npm run build    # type-check + production build
npm run preview
```

## Layout

```
src/
├── main.tsx        App entry
├── App.tsx         Root component
├── index.css       Tailwind entry (@import "tailwindcss")
├── components/     Reusable UI
├── pages/          Route-level views (search, clinic card, compare)
├── hooks/          Custom React hooks
├── lib/            API client, helpers
└── types/          Shared TypeScript types
```

Path alias `@/` → `src/` (configured in `vite.config.ts` and `tsconfig.app.json`).
