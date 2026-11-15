import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import { Layout } from "@/components/Layout";
import { Loader } from "@/components/Loader";
import LoginPage from "@/features/auth/LoginPage";
import RegisterPage from "@/features/auth/RegisterPage";
import ResetPasswordPage from "@/features/auth/ResetPasswordPage";
import ProfilePage from "@/features/me/ProfilePage";
import SuggestPage from "@/features/me/SuggestPage";
import PointPage from "@/features/points/PointPage";
import RouteMapPage from "@/features/routes/RouteMapPage";
import RoutesPage from "@/features/routes/RoutesPage";
import ScanPage from "@/features/scan/ScanPage";
import Landing from "@/pages/Landing";
import NotFound from "@/pages/NotFound";

const PartnerPage = lazy(() => import("@/features/partner/PartnerPage"));
const AdminLayout = lazy(() => import("@/features/admin/AdminLayout"));
const PointsListPage = lazy(() => import("@/features/admin/points/PointsListPage"));
const PointEditorPage = lazy(() => import("@/features/admin/points/PointEditorPage"));
const RoutesListPage = lazy(() =>
  import("@/features/admin/routes/RouteBuilderPage").then((module) => ({ default: module.RoutesListPage })),
);
const RouteBuilderPage = lazy(() => import("@/features/admin/routes/RouteBuilderPage"));
const PartnersListPage = lazy(() =>
  import("@/features/admin/partners/PartnersPage").then((module) => ({ default: module.PartnersListPage })),
);
const PartnerDetailPage = lazy(() => import("@/features/admin/partners/PartnersPage"));
const AchievementsPage = lazy(() => import("@/features/admin/achievements/AchievementsPage"));
const ModerationPage = lazy(() => import("@/features/admin/ModerationPage"));
const AnalyticsPage = lazy(() => import("@/features/admin/AnalyticsPage"));

export default function App() {
  return (
    <Suspense fallback={<Loader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<PointsListPage />} />
          <Route path="points" element={<PointsListPage />} />
          <Route path="points/:pointId" element={<PointEditorPage />} />
          <Route path="routes" element={<RoutesListPage />} />
          <Route path="routes/:routeId" element={<RouteBuilderPage />} />
          <Route path="partners" element={<PartnersListPage />} />
          <Route path="partners/:partnerId" element={<PartnerDetailPage />} />
          <Route path="achievements" element={<AchievementsPage />} />
          <Route path="moderation" element={<ModerationPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
        </Route>
        <Route element={<Layout />}>
          <Route path="/s/:token" element={<ScanPage />} />
          <Route path="/points/:pointId" element={<PointPage />} />
          <Route path="/routes" element={<RoutesPage />} />
          <Route path="/routes/:slug" element={<RouteMapPage />} />
          <Route path="/me" element={<ProfilePage />} />
          <Route path="/suggest" element={<SuggestPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/partner" element={<PartnerPage />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
