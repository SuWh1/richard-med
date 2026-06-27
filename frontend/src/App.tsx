import { Navigate, Route, Routes } from "react-router-dom";

import { SearchPage } from "@/pages/SearchPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { ClinicDetailPage } from "@/pages/ClinicDetailPage";
import { ComparePage } from "@/pages/ComparePage";

export default function App() {
  return (
    <main className="min-h-screen bg-background">
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/clinics/:id" element={<ClinicDetailPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  );
}
