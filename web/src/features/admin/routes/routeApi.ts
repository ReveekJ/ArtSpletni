import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Schemas, unwrap } from "@/api/client";

export type AdminRoute = Schemas["AdminRouteOut"];

export function routeKey(routeId: string) {
  return ["admin", "route", routeId] as const;
}

export function useAdminRoute(routeId: string, enabled: boolean) {
  return useQuery({
    queryKey: routeKey(routeId),
    queryFn: () =>
      unwrap(api.GET("/api/admin/routes/{route_id}", { params: { path: { route_id: routeId } } })),
    enabled,
  });
}

export function useRouteMutation<TInput>(routeId: string, request: (input: TInput) => Promise<AdminRoute>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: (route) => {
      queryClient.setQueryData(routeKey(routeId), route);
      void queryClient.invalidateQueries({ queryKey: ["admin", "routes"] });
    },
  });
}

export function routePath(routeId: string) {
  return { route_id: routeId };
}

export function stopPath(routeId: string, stopId: string) {
  return { route_id: routeId, stop_id: stopId };
}
