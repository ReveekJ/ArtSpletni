import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, fetchTrack, type Track } from "../api/client";
import AudioPlayer from "../components/AudioPlayer";
import LocationMap from "../components/LocationMap";
import NotFound from "./NotFound";

export default function TrackPage() {
  const { slug } = useParams<{ slug: string }>();
  const [track, setTrack] = useState<Track | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    fetchTrack(slug)
      .then((t) => setTrack(t))
      .catch((e: unknown) => {
        if (e instanceof ApiError) setError(e);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="container">
        <p className="subtitle">Загрузка…</p>
      </div>
    );
  }

  if (error || !track) {
    return <NotFound />;
  }

  return (
    <div className="container">
      <p className="brand">Арт-сплетни</p>
      <div className="card">
        {track.cover_url ? (
          <img className="cover" src={track.cover_url} alt={track.title} />
        ) : null}
        <h1>{track.title}</h1>
        {track.author ? <p className="subtitle">{track.author}</p> : null}
        {track.description ? <p>{track.description}</p> : null}
        <AudioPlayer src={track.audio_url} slug={track.slug} />
        {track.latitude != null && track.longitude != null ? (
          <LocationMap
            latitude={track.latitude}
            longitude={track.longitude}
            name={track.location_name}
          />
        ) : null}
      </div>
    </div>
  );
}
