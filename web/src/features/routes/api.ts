import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Schemas, unwrap } from "@/api/client";
import { useLanguage } from "@/lib/useLanguage";

export function useRoutes() {
  const language = useLanguage();
  return useQuery({ queryKey: ["routes", language], queryFn: () => unwrap(api.GET("/api/routes")) });
}

export function useRouteMap(slug: string) {
  const language = useLanguage();
  return useQuery({
    queryKey: ["routes", slug, language],
    queryFn: () => unwrap(api.GET("/api/routes/{slug}", { params: { path: { slug } } })),
  });
}

export function useMyRuns(enabled: boolean) {
  const language = useLanguage();
  return useQuery({ queryKey: ["runs", language], queryFn: () => unwrap(api.GET("/api/runs")), enabled });
}

export function useEngageRoute() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["StartRunInput"]) => unwrap(api.POST("/api/runs", { body })),
    onSuccess: () => queryClient.invalidateQueries(),
  });
}

export function useAbandonRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) =>
      unwrap(api.POST("/api/runs/{run_id}/abandon", { params: { path: { run_id: runId } } })),
    onSuccess: () => queryClient.invalidateQueries(),
  });
}
