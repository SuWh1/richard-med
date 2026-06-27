import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

const SearchPage = lazy(() =>
  import("@/pages/SearchPage").then((m) => ({ default: m.SearchPage })),
);
const ClinicDetailPage = lazy(() =>
  import("@/pages/ClinicDetailPage").then((m) => ({ default: m.ClinicDetailPage })),
);
const ComparePage = lazy(() =>
  import("@/pages/ComparePage").then((m) => ({ default: m.ComparePage })),
);
const AnalyticsPage = lazy(() =>
  import("@/pages/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage })),
);
const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage })),
);

export default function App() {
  return (
    <main className="min-h-screen bg-background">
      <Suspense
        fallback={<div className="p-8 text-sm text-muted-foreground">Загрузка…</div>}
      >
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/clinics/:id" element={<ClinicDetailPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </main>
  );
}
