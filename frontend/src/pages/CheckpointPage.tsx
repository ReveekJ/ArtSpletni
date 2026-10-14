import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError, fetchCheckpoint, type Checkpoint } from "../api/routeClient";
import LanguageSwitcher from "../components/LanguageSwitcher";
import LocationMap from "../components/LocationMap";
import NotFound from "./NotFound";

export default function CheckpointPage() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const [checkpoint, setCheckpoint] = useState<Checkpoint | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    fetchCheckpoint(slug)
      .then(setCheckpoint)
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

  if (error?.status === 403) {
    return (
      <div className="container">
        <div className="track-header-row">
          <p className="brand">{t("common.brand")}</p>
          <LanguageSwitcher compact />
        </div>
        <div className="card">
          <h1>{t("routes.checkpointLockedTitle")}</h1>
          <p className="subtitle">
            {t("routes.checkpointLockedDesc")}
          </p>
          <Link to="/routes">{t("routes.toRoutes")}</Link>
        </div>
      </div>
    );
  }

  if (error || !checkpoint) {
    return <NotFound />;
  }

  return (
    <div className="container">
      <div className="track-header-row">
        <p className="brand">{t("common.brand")}</p>
        <LanguageSwitcher compact />
      </div>
      <div className="card">
        <h1>{checkpoint.title}</h1>
        {checkpoint.description ? <p>{checkpoint.description}</p> : null}
        {checkpoint.location_name ? (
          <p className="subtitle">{checkpoint.location_name}</p>
        ) : null}

        {checkpoint.content_type === "text" && checkpoint.text_content ? (
          <div className="checkpoint-text">
            <p>{checkpoint.text_content}</p>
          </div>
        ) : null}

        {checkpoint.content_type === "image" && checkpoint.image_url ? (
          <img className="cover" src={checkpoint.image_url} alt={checkpoint.title} />
        ) : null}

        {checkpoint.content_type === "loot" && checkpoint.loot_value ? (
          <div className="checkpoint-loot">
            {checkpoint.loot_type === "promo_code" ? (
              <>
                <p className="subtitle">{t("routes.checkpointPromoCode")}</p>
                <input
                  className="loot-code"
                  readOnly
                  value={checkpoint.loot_value}
                  onClick={(e) => e.currentTarget.select()}
                />
              </>
            ) : checkpoint.loot_type === "link" ? (
              <a href={checkpoint.loot_value} target="_blank" rel="noreferrer" className="loot-link">
                {t("routes.checkpointGoLink")}
              </a>
            ) : (
              <div className="loot-badge">{checkpoint.loot_value}</div>
            )}
          </div>
        ) : null}

        {checkpoint.content_type === "audio" && checkpoint.audio_url ? (
          <audio controls preload="metadata" src={checkpoint.audio_url} />
        ) : null}

        <LocationMap
          latitude={checkpoint.latitude}
          longitude={checkpoint.longitude}
          name={checkpoint.location_name}
        />

        <Link to="/routes" className="route-back-link">{t("routes.checkpointBack")}</Link>
      </div>
    </div>
  );
}
