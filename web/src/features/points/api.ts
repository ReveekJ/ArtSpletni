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
