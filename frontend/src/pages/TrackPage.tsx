import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError, fetchTrack, type Track } from "../api/client";
import AudioPlayer from "../components/AudioPlayer";
import LanguageSwitcher from "../components/LanguageSwitcher";
import LocationMap from "../components/LocationMap";
import { useLanguage } from "../i18n/useLanguage";
import NotFound from "./NotFound";

export default function TrackPage() {
  const { t } = useTranslation();
  const { language } = useLanguage();
  const { slug } = useParams<{ slug: string }>();
  const [track, setTrack] = useState<Track | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    fetchTrack(slug, language)
      .then((t) => setTrack(t))
      .catch((e: unknown) => {
        if (e instanceof ApiError) setError(e);
      })
      .finally(() => setLoading(false));
  }, [slug, language]);

  if (loading) {
    return (
      <div className="container">
        <p className="subtitle">{t("common.loading")}</p>
      </div>
    );
  }

  if (error || !track) {
    if (error?.status === 401) {
      return (
        <div className="container">
          <p className="brand">{t("common.brand")}</p>
          <div className="card">
            <h1>{t("track.nfcRequired")}</h1>
            <p className="subtitle">
              {t("track.nfcRequiredDescription")}
            </p>
          </div>
        </div>
      );
    }
    return <NotFound />;
  }

  return (
    <div className="container">
      <div className="track-header-row">
        <p className="brand">{t("common.brand")}</p>
        <LanguageSwitcher compact />
      </div>
      <div className="card">
        {track.cover_url ? (
          <img className="cover" src={track.cover_url} alt={track.title} />
        ) : null}
        <h1>{track.title}</h1>
        {track.author ? <p className="subtitle">{track.author}</p> : null}
        {track.description ? <p>{track.description}</p> : null}
        <AudioPlayer src={track.audio_url} slug={track.slug} />
        <LocationMap
          latitude={track.latitude}
          longitude={track.longitude}
          name={track.location_name}
        />
      </div>
    </div>
  );
}
