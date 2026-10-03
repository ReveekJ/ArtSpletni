export interface Track {
  slug: string;
  title: string;
  description: string | null;
  author: string | null;
  audio_url: string;
  cover_url: string | null;
  latitude: number | null;
  longitude: number | null;
  location_name: string | null;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function fetchTrack(slug: string): Promise<Track> {
  const res = await fetch(`/api/tracks/${encodeURIComponent(slug)}`);
  if (!res.ok) {
    throw new ApiError(res.status, `Failed to fetch track: ${res.status}`);
  }
  return (await res.json()) as Track;
}

export interface AudioSubmission {
  title: string;
  latitude: number;
  longitude: number;
  location_name?: string;
  description?: string;
  author?: string;
  audio_file: File;
}

export async function submitAudioStory(submission: AudioSubmission): Promise<void> {
  const form = new FormData();
  form.set("title", submission.title);
  form.set("latitude", String(submission.latitude));
  form.set("longitude", String(submission.longitude));
  form.set("location_name", submission.location_name ?? "");
  form.set("description", submission.description ?? "");
  form.set("author", submission.author ?? "");
  form.set("audio_file", submission.audio_file);

  const response = await fetch("/api/submissions", { method: "POST", body: form });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new ApiError(response.status, body?.detail ?? `Ошибка отправки: ${response.status}`);
  }
}
