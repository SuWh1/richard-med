import { Navigate, Route, Routes } from "react-router-dom";

import { SearchPage } from "@/pages/SearchPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";

export default function App() {
  return (
    <main className="min-h-screen bg-slate-50">
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  );
}
