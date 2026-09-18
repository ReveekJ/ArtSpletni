import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import TrackPage from "./pages/TrackPage";
import NotFound from "./pages/NotFound";
import "./styles/admin.css";

const AdminDashboardPage = lazy(() => import("./pages/admin/AdminDashboardPage"));

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/t/:slug" element={<TrackPage />} />
      <Route
        path="/admin"
        element={
          <Suspense fallback={<div className="container"><p className="subtitle">Загрузка…</p></div>}>
            <AdminDashboardPage />
          </Suspense>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
