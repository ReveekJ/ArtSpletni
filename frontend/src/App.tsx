import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AuthProvider } from "./context/AuthContext";
import Landing from "./pages/Landing";
import TrackPage from "./pages/TrackPage";
import NotFound from "./pages/NotFound";
import SubmissionPage from "./pages/SubmissionPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import RoutesPage from "./pages/RoutesPage";
import RouteDetailPage from "./pages/RouteDetailPage";
import CheckpointPage from "./pages/CheckpointPage";
import "./styles/admin.css";
import "./styles/admin-route.css";
import "./styles/admin-tracks.css";

const AdminDashboardPage = lazy(() => import("./pages/admin/AdminDashboardPage"));
const AdminRouteBuilderPage = lazy(() => import("./pages/admin/AdminRouteBuilderPage"));

export default function App() {
  const { t } = useTranslation();
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/t/:slug" element={<TrackPage />} />
        <Route path="/c/:slug" element={<CheckpointPage />} />
        <Route path="/routes" element={<RoutesPage />} />
        <Route path="/routes/:slug" element={<RouteDetailPage />} />
        <Route path="/predlozhenie" element={<SubmissionPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/admin"
          element={
            <Suspense fallback={<div className="container"><p className="subtitle">{t("common.loading")}</p></div>}>
              <AdminDashboardPage />
            </Suspense>
          }
        />
        <Route
          path="/admin/routes/:id"
          element={
            <Suspense fallback={<div className="container"><p className="subtitle">{t("common.loading")}</p></div>}>
              <AdminRouteBuilderPage />
            </Suspense>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}
