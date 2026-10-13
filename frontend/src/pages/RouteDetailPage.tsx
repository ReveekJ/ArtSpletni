import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ApiError,
  fetchRoute,
  fetchRouteProgress,
  type RouteDetail,
  type RouteProgress,
} from "../api/routeClient";
import LanguageSwitcher from "../components/LanguageSwitcher";
import LocationMap from "../components/LocationMap";
import "../styles/route.css";

export default function RouteDetailPage() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const [route, setRoute] = useState<RouteDetail | null>(null);
  const [progress, setProgress] = useState<RouteProgress | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    Promise.all([fetchRoute(slug), fetchRouteProgress(slug)])
      .then(([r, p]) => {
        setRoute(r);
        setProgress(p);
      })
      .catch((e: unknown) => {
        if (e instanceof ApiError) setError(e);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="container">
        <p className="subtitle">{t("common.loading")}</p>
      </div>
    );
  }

  if (error || !route) {
    return (
      <div className="container">
        <div className="track-header-row">
          <p className="brand">{t("common.brand")}</p>
          <LanguageSwitcher compact />
        </div>
        <div className="card">
          <h1>{t("routes.notFound")}</h1>
          <Link to="/routes">{t("routes.backToList")}</Link>
        </div>
      </div>
    );
  }

  const completedCount = progress?.completed_stops ?? 0;
  const totalCount = progress?.total_stops ?? route.stops.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const statusMap = new Map(progress?.stop_statuses.map((s) => [s.stop_id, s]));

  return (
    <div className="container">
      <div className="track-header-row">
        <p className="brand">{t("common.brand")}</p>
        <LanguageSwitcher compact />
      </div>
      <div className="card">
        {route.cover_url ? (
          <img className="cover" src={route.cover_url} alt={route.title} />
        ) : null}
        <h1>{route.title}</h1>
        {route.description ? <p>{route.description}</p> : null}

        {route.stops.length > 0 ? (
          <LocationMap
            markers={route.stops.map((stop) => ({
              latitude: stop.latitude,
              longitude: stop.longitude,
              name: stop.location_name ?? stop.title,
            }))}
            polyline
          />
        ) : null}

        <div className="route-progress-bar">
          <div className="route-progress-fill" style={{ width: `${progressPercent}%` }} />
          <span className="route-progress-text">
            {completedCount} / {totalCount} {t("routes.progressStops")}
          </span>
        </div>

        <div className="route-stops-list">
          {route.stops.map((stop) => {
            const status = statusMap.get(stop.id);
            const isLocked = status ? !status.is_unlocked : false;
            const isCompleted = status?.is_completed ?? false;
            const link = stop.stop_type === "track" ? `/t/${stop.slug}` : `/c/${stop.slug}`;

            return (
              <div
                key={stop.id}
                className={`route-stop-row ${isLocked ? "locked" : ""} ${isCompleted ? "completed" : ""}`}
              >
                <span className="route-stop-index">
                  {String(stop.order_index + 1).padStart(2, "0")}
                </span>
                <div className="route-stop-info">
                  <h3>{stop.title}</h3>
                  {stop.location_name ? <span className="route-stop-location">{stop.location_name}</span> : null}
                  <span className="route-stop-type">
                    {stop.stop_type === "track" ? t("routes.stopTrack") : t("routes.stopCheckpoint")}
                  </span>
                </div>
                {isLocked ? (
                  <span className="route-stop-status locked">{t("routes.locked")}</span>
                ) : isCompleted ? (
                  <span className="route-stop-status completed">{t("routes.completed")}</span>
                ) : (
                  <Link to={link} className="route-stop-link">{t("routes.open")}</Link>
                )}
              </div>
            );
          })}
        </div>

        <Link to="/routes" className="route-back-link">{t("routes.allRoutes")}</Link>
      </div>
    </div>
  );
}
