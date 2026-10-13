import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../../api/adminClient";
import {
  createAdminTrack,
  updateAdminTrack,
  type TrackAdminDetail,
} from "../../api/adminRouteClient";
import LocationMap from "../LocationMap";

interface TrackFormModalProps {
  track?: TrackAdminDetail | null;
  onSaved: () => void;
  onClose: () => void;
}

export default function TrackFormModal({
  track,
  onSaved,
  onClose,
}: TrackFormModalProps) {
  const { t } = useTranslation();
  const isEdit = track != null;

  const [title, setTitle] = useState(track?.title ?? "");
  const [description, setDescription] = useState(track?.description ?? "");
  const [author, setAuthor] = useState(track?.author ?? "");
  const [latitude, setLatitude] = useState(track?.latitude ?? 56.8389);
  const [longitude, setLongitude] = useState(track?.longitude ?? 60.6057);
  const [mapCenter, setMapCenter] = useState<{ latitude: number; longitude: number }>();
  const [locationName, setLocationName] = useState(track?.location_name ?? "");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverPreview, setCoverPreview] = useState<string | null>(
    track?.cover_url ?? null,
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const audioInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const handleCoverChange = useCallback(
    (file: File | null) => {
      setCoverFile(file);
      if (file) {
        const reader = new FileReader();
        reader.onload = () => setCoverPreview(reader.result as string);
        reader.readAsDataURL(file);
      } else {
        setCoverPreview(track?.cover_url ?? null);
      }
    },
    [track],
  );

  const handleSubmit = async () => {
    setError(null);
    if (!title.trim()) {
      setError(t("admin.trackTitleRequired"));
      return;
    }
    if (!isEdit && !audioFile) {
      setError(t("admin.trackAudioRequired"));
      return;
    }

    const formData = new FormData();
    formData.append("title", title.trim());
    if (description) formData.append("description", description);
    if (author) formData.append("author", author);
    if (latitude) formData.append("latitude", String(latitude));
    if (longitude) formData.append("longitude", String(longitude));
    if (locationName) formData.append("location_name", locationName);
    if (audioFile) formData.append("audio_file", audioFile);
    if (coverFile) formData.append("cover_file", coverFile);

    setSubmitting(true);
    try {
      if (isEdit && track) {
        await updateAdminTrack(track.id, formData);
      } else {
        await createAdminTrack(formData);
      }
      onSaved();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("admin.loadError"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="track-modal-overlay" onClick={onClose}>
      <div
        className="track-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="track-modal-header">
          <h2>{isEdit ? t("admin.editTrack") : t("admin.createTrack")}</h2>
          <button className="track-modal-close" onClick={onClose}>×</button>
        </div>

        {error ? <p className="admin-error">{error}</p> : null}

        <div className="track-modal-body">
          <label className="track-form-label">
            {t("admin.trackTitle")}
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={255}
            />
          </label>

          <label className="track-form-label">
            {t("admin.trackDescription")}
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </label>

          <label className="track-form-label">
            {t("admin.trackAuthor")}
            <input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              maxLength={255}
            />
          </label>

          <div className="track-form-row">
            <label className="track-form-label">
              {t("admin.trackLocationMap")}
              <LocationMap
                interactive
                latitude={latitude}
                longitude={longitude}
                center={mapCenter}
                onChange={({ latitude: nextLat, longitude: nextLng }) => {
                  setLatitude(Number(nextLat.toFixed(6)));
                  setLongitude(Number(nextLng.toFixed(6)));
                  setMapCenter(undefined);
                }}
              />
              <div className="map-selection-row">
                <small>{latitude.toFixed(6)}, {longitude.toFixed(6)}</small>
                <button
                  className="location-button"
                  type="button"
                  onClick={() => {
                    if (!navigator.geolocation) return;
                    navigator.geolocation.getCurrentPosition(
                      ({ coords }) => {
                        const pos = {
                          latitude: Number(coords.latitude.toFixed(6)),
                          longitude: Number(coords.longitude.toFixed(6)),
                        };
                        setLatitude(pos.latitude);
                        setLongitude(pos.longitude);
                        setMapCenter(pos);
                      },
                      undefined,
                      { enableHighAccuracy: true, timeout: 10000 },
                    );
                  }}
                >
                  {t("admin.trackMyLocation")}
                </button>
              </div>
            </label>
          </div>

          <label className="track-form-label">
            {t("admin.trackLocationName")}
            <input
              value={locationName}
              onChange={(e) => setLocationName(e.target.value)}
              maxLength={255}
            />
          </label>

          <div className="track-upload-section">
            <label className="track-form-label">
              {t("admin.trackAudioFile")}
              {!isEdit ? " *" : ""}
            </label>
            <input
              ref={audioInputRef}
              type="file"
              accept=".aac,.m4a,.mp3,.ogg,.wav,audio/*"
              onChange={(e) => setAudioFile(e.target.files?.[0] ?? null)}
            />
            {isEdit && track?.audio_url ? (
              <audio
                controls
                preload="none"
                src={track.audio_url}
                className="track-audio-preview"
              />
            ) : null}
          </div>

          <div className="track-upload-section">
            <label className="track-form-label">
              {t("admin.trackCoverFile")}
            </label>
            <input
              ref={coverInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.webp,image/*"
              onChange={(e) => handleCoverChange(e.target.files?.[0] ?? null)}
            />
            {coverPreview ? (
              <img
                src={coverPreview}
                alt="cover preview"
                className="track-cover-preview"
              />
            ) : null}
          </div>
        </div>

        <div className="track-modal-footer">
          <button className="admin-btn ghost" onClick={onClose}>
            {t("admin.trackCancel")}
          </button>
          <button
            className="admin-btn"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting
              ? t("common.loading")
              : isEdit
                ? t("admin.trackSave")
                : t("admin.createTrack")}
          </button>
        </div>
      </div>
    </div>
  );
}
