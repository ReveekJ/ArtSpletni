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
