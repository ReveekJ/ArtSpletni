import { request } from "./adminClient";

export interface AdminRoute {
  id: number;
  slug: string;
  title: string;
  description: string | null;
  is_published: boolean;
}

export interface AdminStop {
  id: number;
  route_id: number;
  order_index: number;
  stop_type: "track" | "checkpoint";
  track_id: number | null;
  checkpoint_id: number | null;
  completion_criteria: string;
  depends_on: number[];
}

export interface AdminCheckpoint {
  id: number;
  slug: string;
  title: string;
  content_type: "text" | "image" | "loot" | "audio";
  description: string | null;
  latitude: number;
  longitude: number;
  location_name: string | null;
  text_content: string | null;
  loot_type: string | null;
  loot_value: string | null;
  is_published: boolean;
}

export interface AdminTrack {
  id: number;
  slug: string;
  title: string;
  description: string | null;
  author: string | null;
  latitude: number;
  longitude: number;
  location_name: string | null;
  is_published: boolean;
  moderation_status: string;
}

export interface TrackAdminDetail {
  id: number;
  slug: string;
  title: string;
  description: string | null;
  author: string | null;
  latitude: number;
  longitude: number;
  location_name: string | null;
  is_published: boolean;
  moderation_status: string;
  audio_url: string;
  cover_url: string | null;
  created_at: string;
  published_at: string | null;
}

export async function fetchAdminRoutes(): Promise<{ routes: AdminRoute[] }> {
  return request<{ routes: AdminRoute[] }>("/api/admin/routes");
}

export async function createAdminRoute(
  title: string,
  description: string | null,
): Promise<AdminRoute> {
  return request<AdminRoute>("/api/admin/routes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description }),
  });
}

export async function updateAdminRoute(
  routeId: number,
  data: {
    title?: string;
    description?: string | null;
    is_published?: boolean;
  },
): Promise<AdminRoute> {
  return request<AdminRoute>(`/api/admin/routes/${routeId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteAdminRoute(routeId: number): Promise<void> {
  await request<void>(`/api/admin/routes/${routeId}`, { method: "DELETE" });
}

export async function fetchAdminStops(routeId: number): Promise<AdminStop[]> {
  return request<AdminStop[]>(`/api/admin/routes/${routeId}/stops`);
}

export async function addAdminStop(
  routeId: number,
  data: {
    stop_type: "track" | "checkpoint";
    track_id?: number;
    checkpoint_id?: number;
    completion_criteria: string;
  },
): Promise<AdminStop> {
  return request<AdminStop>(`/api/admin/routes/${routeId}/stops`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function updateAdminStop(
  routeId: number,
  stopId: number,
  data: {
    completion_criteria?: string;
    order_index?: number;
  },
): Promise<AdminStop> {
  return request<AdminStop>(`/api/admin/routes/${routeId}/stops/${stopId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteAdminStop(routeId: number, stopId: number): Promise<void> {
  await request<void>(`/api/admin/routes/${routeId}/stops/${stopId}`, { method: "DELETE" });
}

export async function addAdminDependency(
  routeId: number,
  stopId: number,
  dependsOnStopId: number,
): Promise<void> {
  await request<{ status: string }>(
    `/api/admin/routes/${routeId}/stops/${stopId}/dependencies`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ depends_on_stop_id: dependsOnStopId }),
    },
  );
}

export async function removeAdminDependency(
  routeId: number,
  stopId: number,
  dependsOnStopId: number,
): Promise<void> {
  await request<void>(
    `/api/admin/routes/${routeId}/stops/${stopId}/dependencies/${dependsOnStopId}`,
    { method: "DELETE" },
  );
}

export async function reorderAdminStops(
  routeId: number,
  stopIds: number[],
): Promise<void> {
  await request<{ status: string }>(`/api/admin/routes/${routeId}/reorder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stop_ids: stopIds }),
  });
}

export async function fetchAdminCheckpoints(): Promise<{ checkpoints: AdminCheckpoint[] }> {
  return request<{ checkpoints: AdminCheckpoint[] }>("/api/admin/checkpoints");
}

export async function createAdminCheckpoint(data: {
  title: string;
  content_type: "text" | "image" | "loot" | "audio";
  description?: string;
  latitude: number;
  longitude: number;
  location_name?: string;
  text_content?: string;
  loot_type?: "promo_code" | "link" | "badge";
  loot_value?: string;
  is_published?: boolean;
}): Promise<AdminCheckpoint> {
  return request<AdminCheckpoint>("/api/admin/checkpoints", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function updateAdminCheckpoint(
  checkpointId: number,
  data: Record<string, unknown>,
): Promise<AdminCheckpoint> {
  return request<AdminCheckpoint>(`/api/admin/checkpoints/${checkpointId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteAdminCheckpoint(checkpointId: number): Promise<void> {
  await request<void>(`/api/admin/checkpoints/${checkpointId}`, { method: "DELETE" });
}

export async function fetchAdminTracks(): Promise<{ tracks: AdminTrack[] }> {
  return request<{ tracks: AdminTrack[] }>("/api/admin/tracks");
}

export async function fetchAdminTrackDetail(
  trackId: number,
): Promise<TrackAdminDetail> {
  return request<TrackAdminDetail>(`/api/admin/tracks/${trackId}`);
}

export async function createAdminTrack(
  formData: FormData,
): Promise<TrackAdminDetail> {
  return request<TrackAdminDetail>("/api/admin/tracks", {
    method: "POST",
    body: formData,
  });
}

export async function updateAdminTrack(
  trackId: number,
  formData: FormData,
): Promise<TrackAdminDetail> {
  return request<TrackAdminDetail>(`/api/admin/tracks/${trackId}`, {
    method: "PATCH",
    body: formData,
  });
}

export async function deleteAdminTrack(trackId: number): Promise<void> {
  await request<void>(`/api/admin/tracks/${trackId}`, { method: "DELETE" });
}
