import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";

export function useAdminPoints(search = "", kind: "gossip" | "partner" | null = null) {
  return useQuery({
    queryKey: ["admin", "points", search, kind],
    queryFn: () =>
      unwrap(api.GET("/api/admin/points", { params: { query: { search: search || null, kind } } })),
  });
}

export function useAdminPartners() {
  return useQuery({ queryKey: ["admin", "partners"], queryFn: () => unwrap(api.GET("/api/admin/partners")) });
}

export function useAdminRoutes() {
  return useQuery({ queryKey: ["admin", "routes"], queryFn: () => unwrap(api.GET("/api/admin/routes")) });
}

export function useAdminOffers(partnerId: string | null = null) {
  return useQuery({
    queryKey: ["admin", "offers", partnerId],
    queryFn: () => unwrap(api.GET("/api/admin/offers", { params: { query: { partner_id: partnerId } } })),
  });
}

export function titleOf(value: Record<string, { text: string }> | undefined): string {
  return value?.ru?.text ?? Object.values(value ?? {})[0]?.text ?? "—";
}
