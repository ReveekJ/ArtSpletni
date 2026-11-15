import createClient from "openapi-fetch";

import type { components, paths } from "@/api/schema";
import { currentLanguage } from "@/i18n";

export type Schemas = components["schemas"];

export const api = createClient<paths>({ baseUrl: "", credentials: "include" });

api.use({
  onRequest({ request }) {
    request.headers.set("Accept-Language", currentLanguage());
    return request;
  },
});

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, detail: string) {
    super(detail);
    this.status = status;
    this.code = code;
  }
}

interface ErrorBody {
  detail?: string;
  code?: string;
}

function isErrorBody(value: unknown): value is ErrorBody {
  return typeof value === "object" && value !== null;
}

interface FetchResult<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

export async function unwrap<T>(request: Promise<FetchResult<T>>): Promise<T> {
  const { data, error, response } = await request;
  if (!response.ok) {
    const body = isErrorBody(error) ? error : {};
    throw new ApiError(
      response.status,
      body.code ?? `http_${response.status}`,
      body.detail ?? response.statusText,
    );
  }
  return data as T;
}

export function errorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null;
}
