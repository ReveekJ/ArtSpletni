import { useMutation, useQuery } from "@tanstack/react-query";

import { api, type Schemas, unwrap } from "@/api/client";
import { useLanguage } from "@/lib/useLanguage";

export function usePointContent(pointId: string) {
  const language = useLanguage();
  return useQuery({
    queryKey: ["points", pointId, language],
    queryFn: () => unwrap(api.GET("/api/points/{point_id}", { params: { path: { point_id: pointId } } })),
  });
}

export function useCollection(enabled: boolean) {
  const language = useLanguage();
  return useQuery({
    queryKey: ["collection", language],
    queryFn: () => unwrap(api.GET("/api/me/collection")),
    enabled,
  });
}

export function useReportPlayback() {
  return useMutation({
    mutationFn: (body: Schemas["PlaybackInput"]) => unwrap(api.POST("/api/analytics/playback", { body })),
  });
}

const IN_PROGRESS: ReadonlySet<string> = new Set(["pending", "processing"]);
const GOSSIP_POLL_MS = 4000;

export function isGossipInProgress(status: string | undefined): boolean {
  return status !== undefined && IN_PROGRESS.has(status);
}

export function usePointGossip(pointId: string) {
  const language = useLanguage();
  return useQuery({
    queryKey: ["points", pointId, "gossip", language],
    queryFn: () =>
      unwrap(api.GET("/api/points/{point_id}/gossip", { params: { path: { point_id: pointId } } })),
    refetchInterval: (query) => (isGossipInProgress(query.state.data?.status) ? GOSSIP_POLL_MS : false),
    retry: false,
  });
}
