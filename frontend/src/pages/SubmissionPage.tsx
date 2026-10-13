import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError, submitAudioStory } from "../api/client";
import LanguageSwitcher from "../components/LanguageSwitcher";
import LocationMap from "../components/LocationMap";
import "../styles/submission.css";

const MAX_AUDIO_BYTES = 10 * 1024 * 1024;
const ACCEPTED_AUDIO = ".mp3,.m4a,.aac,.wav,.ogg,audio/mpeg,audio/mp4,audio/aac,audio/wav,audio/ogg";

export default function SubmissionPage() {
  const { t } = useTranslation();
  const [latitude, setLatitude] = useState(56.8389);
  const [longitude, setLongitude] = useState(60.6057);
  const [locationSelected, setLocationSelected] = useState(false);
  const [mapCenter, setMapCenter] = useState<{ latitude: number; longitude: number }>();
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const useCurrentLocation = () => {
    setError(null);
    if (!navigator.geolocation) {
      setError(t("submission.errorNoGeolocation"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const position = {
          latitude: Number(coords.latitude.toFixed(6)),
          longitude: Number(coords.longitude.toFixed(6)),
        };
        setLatitude(position.latitude);
        setLongitude(position.longitude);
        setMapCenter(position);
        setLocationSelected(true);
      },
      () => setError(t("submission.errorGeolocation")),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    if (!file) {
      setError(t("submission.errorNoFile"));
      return;
    }
    if (!locationSelected) {
      setError(t("submission.errorNoLocation"));
      return;
    }
    if (file.size > MAX_AUDIO_BYTES) {
      setError(t("submission.errorFileTooLarge"));
      return;
    }
    const data = new FormData(event.currentTarget);
    setBusy(true);
    try {
      await submitAudioStory({
        title: String(data.get("title") ?? "").trim(),
        latitude,
        longitude,
        location_name: String(data.get("location_name") ?? "").trim() || undefined,
        description: String(data.get("description") ?? "").trim() || undefined,
        author: String(data.get("author") ?? "").trim() || undefined,
        audio_file: file,
      });
      setMessage(t("submission.success"));
      event.currentTarget.reset();
      setFile(null);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("submission.errorGeneric"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="submission-page">
      <header className="submission-header">
        <Link className="submission-brand" to="/">{t("common.brand")}</Link>
        <div className="submission-header-actions">
          <LanguageSwitcher compact />
          <Link to="/">{t("common.home")} <span aria-hidden="true">↗</span></Link>
        </div>
      </header>
      <section className="submission-layout">
        <div className="submission-intro">
          <p className="submission-kicker">{t("submission.kicker")}</p>
          <h1>{t("submission.title")}<br /><em>{t("submission.titleEm")}</em></h1>
          <p>{t("submission.intro")}</p>
          <span className="submission-index">{t("submission.indexPlaceholder")}</span>
        </div>
        <form className="submission-form" onSubmit={handleSubmit}>
          <label className="submission-field">
            <span>{t("submission.audioLabel")} <b>*</b></span>
            <input
              accept={ACCEPTED_AUDIO}
              name="audio_file"
              onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
              required
              type="file"
            />
            <small>{file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MiB` : t("submission.audioHint")}</small>
          </label>
          <label className="submission-field">
            <span>{t("submission.titleLabel")} <b>*</b></span>
            <input autoComplete="off" maxLength={255} name="title" placeholder={t("submission.titlePlaceholder")} required />
          </label>
          <div className="submission-field">
            <span>{t("submission.locationLabel")} <b>*</b></span>
            <LocationMap
              interactive
              latitude={latitude}
              longitude={longitude}
              center={mapCenter}
              onChange={({ latitude: nextLatitude, longitude: nextLongitude }) => {
                setLatitude(Number(nextLatitude.toFixed(6)));
                setLongitude(Number(nextLongitude.toFixed(6)));
                setMapCenter(undefined);
                setLocationSelected(true);
              }}
            />
            <div className="map-selection-row">
              <small>{locationSelected ? `${t("submission.locationSelected")} · ${latitude.toFixed(6)}, ${longitude.toFixed(6)}` : t("submission.locationNotSelected")}</small>
              <button className="location-button" onClick={useCurrentLocation} type="button" title={t("submission.myLocationAria")}>{t("submission.myLocation")}</button>
            </div>
          </div>
          <label className="submission-field">
            <span>{t("submission.locationNameLabel")}</span>
            <input autoComplete="off" maxLength={255} name="location_name" placeholder={t("submission.locationNamePlaceholder")} />
          </label>
          <label className="submission-field">
            <span>{t("submission.descriptionLabel")}</span>
            <textarea name="description" rows={3} placeholder={t("submission.descriptionPlaceholder")} />
          </label>
          <label className="submission-field">
            <span>{t("submission.authorLabel")}</span>
            <input autoComplete="name" maxLength={255} name="author" placeholder={t("submission.authorPlaceholder")} />
          </label>
          {error ? <p className="submission-alert error" role="alert">{error}</p> : null}
          {message ? <p className="submission-alert success" role="status">{message}</p> : null}
          <button className="submission-submit" disabled={busy} type="submit">
            {busy ? t("submission.submitting") : t("submission.submit")}<span aria-hidden="true">↗</span>
          </button>
          <p className="submission-privacy">{t("submission.privacy")}</p>
        </form>
      </section>
    </main>
  );
}