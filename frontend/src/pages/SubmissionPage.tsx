import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, submitAudioStory } from "../api/client";
import LocationMap from "../components/LocationMap";
import "../styles/submission.css";

const MAX_AUDIO_BYTES = 10 * 1024 * 1024;
const ACCEPTED_AUDIO = ".mp3,.m4a,.aac,.wav,.ogg,audio/mpeg,audio/mp4,audio/aac,audio/wav,audio/ogg";

export default function SubmissionPage() {
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
      setError("Браузер не поддерживает определение геопозиции. Введите координаты вручную.");
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
      () => setError("Не удалось получить геопозицию. Проверьте разрешение браузера или введите координаты вручную."),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    if (!file) {
      setError("Выберите аудиозапись.");
      return;
    }
    if (!locationSelected) {
      setError("Отметьте место истории на карте.");
      return;
    }
    if (file.size > MAX_AUDIO_BYTES) {
      setError("Размер файла не должен превышать 10 MiB.");
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
      setMessage("Спасибо. Запись отправлена на проверку.");
      event.currentTarget.reset();
      setFile(null);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Не удалось отправить запись. Попробуйте ещё раз.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="submission-page">
      <header className="submission-header">
        <Link className="submission-brand" to="/">Арт-сплетни</Link>
        <Link to="/">На главную <span aria-hidden="true">↗</span></Link>
      </header>
      <section className="submission-layout">
        <div className="submission-intro">
          <p className="submission-kicker">ГОРОД ГОВОРИТ</p>
          <h1>У тебя есть<br /><em>своя история?</em></h1>
          <p>Запиши её и отметь место, с которым она связана. После проверки история появится в городском архиве.</p>
          <span className="submission-index">ПРЕДЛОЖЕНИЕ № ———</span>
        </div>
        <form className="submission-form" onSubmit={handleSubmit}>
          <label className="submission-field">
            <span>Аудиозапись <b>*</b></span>
            <input
              accept={ACCEPTED_AUDIO}
              name="audio_file"
              onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
              required
              type="file"
            />
            <small>{file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MiB` : "MP3, M4A, AAC, WAV или OGG · до 10 MiB"}</small>
          </label>
          <label className="submission-field">
            <span>Название истории <b>*</b></span>
            <input autoComplete="off" maxLength={255} name="title" placeholder="Например, что случилось у старого вокзала" required />
          </label>
          <div className="submission-field">
            <span>Где это произошло <b>*</b></span>
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
              <small>{locationSelected ? `Точка выбрана · ${latitude.toFixed(6)}, ${longitude.toFixed(6)}` : "Точка ещё не выбрана"}</small>
              <button className="location-button" onClick={useCurrentLocation} type="button" title="Определить моё местоположение">◎ Моё место</button>
            </div>
          </div>
          <label className="submission-field">
            <span>Название места</span>
            <input autoComplete="off" maxLength={255} name="location_name" placeholder="Улица, здание или ориентир" />
          </label>
          <label className="submission-field">
            <span>О чём эта история</span>
            <textarea name="description" rows={3} placeholder="Пара слов для редактора" />
          </label>
          <label className="submission-field">
            <span>Как к тебе обращаться</span>
            <input autoComplete="name" maxLength={255} name="author" placeholder="Можно оставить пустым" />
          </label>
          {error ? <p className="submission-alert error" role="alert">{error}</p> : null}
          {message ? <p className="submission-alert success" role="status">{message}</p> : null}
          <button className="submission-submit" disabled={busy} type="submit">
            {busy ? "Отправляем…" : "Отправить на проверку"}<span aria-hidden="true">↗</span>
          </button>
          <p className="submission-privacy">Отправленная запись не появится на сайте, пока редактор её не проверит.</p>
        </form>
      </section>
    </main>
  );
}