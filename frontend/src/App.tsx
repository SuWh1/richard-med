import { lazy, Suspense } from "react";
import { Route, Routes, useLocation } from "react-router-dom";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ScrollToTop } from "@/components/ScrollToTop";
import { TopProgress } from "@/components/TopProgress";
import { RequireAdmin, RequireAuth } from "@/components/auth/RouteGuards";

const LandingPage = lazy(() =>
  import("@/pages/LandingPage").then((m) => ({ default: m.LandingPage })),
);
const ResultsPage = lazy(() =>
  import("@/pages/ResultsPage").then((m) => ({ default: m.ResultsPage })),
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
const NotFoundPage = lazy(() =>
  import("@/pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })),
);
const LoginPage = lazy(() =>
  import("@/pages/auth/LoginPage").then((m) => ({ default: m.LoginPage })),
);
const SignupPage = lazy(() =>
  import("@/pages/auth/SignupPage").then((m) => ({ default: m.SignupPage })),
);
const CabinetPage = lazy(() =>
  import("@/pages/CabinetPage").then((m) => ({ default: m.CabinetPage })),
);

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <div
      key={location.pathname}
      className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1 motion-safe:duration-300 motion-safe:ease-out"
    >
      <Routes location={location}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/search" element={<ResultsPage />} />
        <Route path="/clinics/:id" element={<ClinicDetailPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route element={<RequireAuth />}>
          <Route path="/cabinet" element={<CabinetPage />} />
        </Route>
        <Route element={<RequireAdmin />}>
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ScrollToTop />
      <TopProgress />
      <Suspense fallback={<div className="min-h-screen bg-background" />}>
        <AnimatedRoutes />
      </Suspense>
    </ErrorBoundary>
  );
}
