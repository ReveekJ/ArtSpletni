import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError, fetchRoutes, type RouteListItem } from "../api/routeClient";
import LanguageSwitcher from "../components/LanguageSwitcher";
import "../styles/route.css";

export default function RoutesPage() {
  const { t } = useTranslation();
  const [routes, setRoutes] = useState<RouteListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRoutes()
      .then((data) => setRoutes(data.routes))
      .catch((e: unknown) => {
        if (e instanceof ApiError) setError(e.message);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="container">
        <p className="subtitle">{t("common.loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="track-header-row">
          <p className="brand">{t("common.brand")}</p>
          <LanguageSwitcher compact />
        </div>
        <div className="card">
          <h1>{t("routes.title")}</h1>
          <p className="subtitle">{error}</p>
        </div>
      </div>
    );
  }

  if (routes.length === 0) {
    return (
      <div className="container">
        <div className="track-header-row">
          <p className="brand">{t("common.brand")}</p>
          <LanguageSwitcher compact />
        </div>
        <div className="card">
          <h1>{t("routes.title")}</h1>
          <p className="subtitle">{t("routes.empty")}</p>
          <Link to="/">{t("common.home")}</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="track-header-row">
        <p className="brand">{t("common.brand")}</p>
        <LanguageSwitcher compact />
      </div>
      <div className="card">
        <h1>{t("routes.title")}</h1>
        <p className="subtitle">{t("routes.subtitle")}</p>
        <div className="routes-grid">
          {routes.map((route) => (
            <Link
              key={route.id}
              to={`/routes/${route.slug}`}
              className="route-card"
            >
              {route.cover_url ? (
                <img className="route-cover" src={route.cover_url} alt={route.title} />
              ) : null}
              <div className="route-card-body">
                <h2>{route.title}</h2>
                {route.description ? <p>{route.description}</p> : null}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
