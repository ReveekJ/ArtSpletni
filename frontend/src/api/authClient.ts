export interface User {
  id: number;
  email: string;
  display_name: string;
  is_admin: boolean;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...init, credentials: "include" });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new ApiError(res.status, body?.detail ?? `Request failed: ${res.status}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export async function register(
  email: string,
  password: string,
  displayName: string,
): Promise<User> {
  return request<User>("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

export async function login(email: string, password: string): Promise<User> {
  return request<User>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(): Promise<void> {
  await request<{ authenticated: boolean }>("/api/auth/session", { method: "DELETE" });
}

export async function getMe(): Promise<User | null> {
  try {
    const data = await request<User | null>("/api/auth/me");
    return data;
  } catch {
    return null;
  }
}

export async function getYandexLoginUrl(): Promise<string> {
  const data = await request<{ auth_url: string }>("/api/auth/yandex");
  return data.auth_url;
}
