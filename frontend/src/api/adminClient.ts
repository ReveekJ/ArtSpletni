export interface DailyPoint {
  day: string;
  plays: number;
  visitors: number;
  listened_seconds: number;
}

export interface BreakdownItem {
  name: string;
  plays: number;
  visitors: number;
}

export interface TopTrack {
  id: number;
  title: string;
  slug: string;
  plays: number;
}

export interface OverviewKpi {
  plays: number;
  visitors: number;
  total_listened_seconds: number;
  avg_completion: number | null;
  completion_rate: number | null;
  plays_today: number;
}

export interface Overview {
  kpi: OverviewKpi;
  daily: DailyPoint[];
  top_tracks: TopTrack[];
  devices: BreakdownItem[];
  referrers: BreakdownItem[];
  languages: BreakdownItem[];
}

export interface TrackRow {
  id: number;
  title: string;
  slug: string;
  is_published: boolean;
  plays: number;
  visitors: number;
  listened_seconds: number;
  avg_completion: number | null;
  median_completion: number | null;
  completion_rate: number | null;
  last_played_at: string | null;
}

export interface HistogramBucket {
  bucket_start: number;
  count: number;
}

export interface RecentSession {
  created_at: string;
  listened_seconds: number;
  completion_ratio: number | null;
  is_completed: boolean;
  device_type: string | null;
  referrer: string | null;
}

export interface TrackDetail {
  id: number;
  title: string;
  slug: string;
  is_published: boolean;
  kpi: OverviewKpi;
  daily: DailyPoint[];
  histogram: HistogramBucket[];
  avg_seek_count: number | null;
  recent: RecentSession[];
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    throw new ApiError(res.status, `Request failed: ${res.status}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export async function checkSession(): Promise<boolean> {
  const data = await request<{ authenticated: boolean }>("/api/admin/session");
  return data.authenticated;
}

export async function login(username: string, password: string): Promise<void> {
  await request<{ authenticated: boolean }>("/api/admin/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export async function logout(): Promise<void> {
  await request<{ authenticated: boolean }>("/api/admin/session", {
    method: "DELETE",
  });
}

export async function fetchOverview(days: number): Promise<Overview> {
  return request<Overview>(`/api/admin/analytics/overview?days=${days}`);
}

export async function fetchTracks(days: number): Promise<{ tracks: TrackRow[] }> {
  return request<{ tracks: TrackRow[] }>(`/api/admin/analytics/tracks?days=${days}`);
}

export async function fetchTrackDetail(
  trackId: number,
  days: number,
): Promise<TrackDetail> {
  return request<TrackDetail>(
    `/api/admin/analytics/tracks/${trackId}?days=${days}`,
  );
}
