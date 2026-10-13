export interface RouteListItem {
  id: number;
  slug: string;
  title: string;
  description: string | null;
  cover_url: string | null;
}

export interface RouteStop {
  id: number;
  order_index: number;
  stop_type: "track" | "checkpoint";
  track_id: number | null;
  checkpoint_id: number | null;
  completion_criteria: string;
  title: string;
  slug: string;
  latitude: number;
  longitude: number;
  location_name: string | null;
  depends_on: number[];
}

export interface RouteDetail {
  id: number;
  slug: string;
  title: string;
  description: string | null;
  cover_url: string | null;
  is_published: boolean;
  stops: RouteStop[];
}

export interface StopStatus {
  stop_id: number;
  is_unlocked: boolean;
  is_completed: boolean;
}

export interface RouteProgress {
  route_id: number;
  total_stops: number;
  completed_stops: number;
  stop_statuses: StopStatus[];
}

export interface Checkpoint {
  id: number;
  slug: string;
  title: string;
  description: string | null;
  latitude: number;
  longitude: number;
  location_name: string | null;
  content_type: "text" | "image" | "loot" | "audio";
  text_content: string | null;
  image_url: string | null;
  loot_type: "promo_code" | "link" | "badge" | null;
  loot_value: string | null;
  audio_url: string | null;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string): Promise<T> {
  const res = await fetch(path, { credentials: "include" });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new ApiError(res.status, body?.detail ?? `Request failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function fetchRoutes(): Promise<{ routes: RouteListItem[] }> {
  return request<{ routes: RouteListItem[] }>("/api/routes");
}

export async function fetchRoute(slug: string): Promise<RouteDetail> {
  return request<RouteDetail>(`/api/routes/${encodeURIComponent(slug)}`);
}

export async function fetchRouteProgress(slug: string): Promise<RouteProgress> {
  return request<RouteProgress>(`/api/routes/${encodeURIComponent(slug)}/progress`);
}

export async function fetchCheckpoint(slug: string): Promise<Checkpoint> {
  return request<Checkpoint>(`/api/checkpoints/${encodeURIComponent(slug)}`);
}
