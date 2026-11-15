import { useMutation, useQuery } from "@tanstack/react-query";

import { api, unwrap } from "@/api/client";
import { useLanguage } from "@/lib/useLanguage";

export function useMyOffers(enabled: boolean) {
  const language = useLanguage();
  return useQuery({
    queryKey: ["offers", language],
    queryFn: () => unwrap(api.GET("/api/me/offers")),
    enabled,
  });
}

export function useOfferQr() {
  return useMutation({
    mutationFn: (grantId: string) =>
      unwrap(api.POST("/api/me/offers/{grant_id}/qr", { params: { path: { grant_id: grantId } } })),
  });
}

export function useMyAchievements(enabled: boolean) {
  const language = useLanguage();
  return useQuery({
    queryKey: ["achievements", language],
    queryFn: () => unwrap(api.GET("/api/me/achievements")),
    enabled,
  });
}

export function useMySubmissions(enabled: boolean) {
  return useQuery({
    queryKey: ["submissions"],
    queryFn: () => unwrap(api.GET("/api/me/submissions")),
    enabled,
  });
}
