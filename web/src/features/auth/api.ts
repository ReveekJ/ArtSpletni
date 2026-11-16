import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Schemas, unwrap } from "@/api/client";

export const sessionKey = ["session"] as const;

export function useSession() {
  return useQuery({
    queryKey: sessionKey,
    queryFn: () => unwrap(api.GET("/api/auth/session")),
    staleTime: 60_000,
  });
}

export function useAuthOptions() {
  return useQuery({
    queryKey: ["auth-options"],
    queryFn: () => unwrap(api.GET("/api/auth/options")),
    staleTime: 5 * 60_000,
  });
}

export function useCurrentUser(): Schemas["UserProfile"] | null {
  return useSession().data?.user ?? null;
}

function useInvalidateAll() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries();
}

export function useLogin() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (body: Schemas["LoginPayload"]) => unwrap(api.POST("/api/auth/login", { body })),
    onSuccess: invalidate,
  });
}

export function useDemoLogin() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (key: string) => unwrap(api.POST("/api/auth/demo/{key}", { params: { path: { key } } })),
    onSuccess: invalidate,
  });
}

export function useRegister() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: (body: Schemas["RegisterPayload"]) => unwrap(api.POST("/api/auth/register", { body })),
    onSuccess: invalidate,
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => unwrap(api.POST("/api/auth/logout")),
    onSuccess: () => queryClient.clear(),
  });
}

export function useRequestReset() {
  return useMutation({
    mutationFn: (email: string) => unwrap(api.POST("/api/auth/password-reset/request", { body: { email } })),
  });
}

export function useConfirmReset() {
  return useMutation({
    mutationFn: (body: Schemas["PasswordResetConfirmPayload"]) =>
      unwrap(api.POST("/api/auth/password-reset/confirm", { body })),
  });
}

export function yandexLoginUrl(next: string): string {
  return `/api/auth/yandex/login?next=${encodeURIComponent(next)}`;
}
