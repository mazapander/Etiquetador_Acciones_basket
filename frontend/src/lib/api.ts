import { getAccessToken } from "./authSession";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export { API_BASE };

function buildHeaders(options?: RequestInit) {
  const headers = new Headers(options?.headers ?? {});
  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", "Bearer " + token);
  }
  return headers;
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE + path, {
    ...options,
    headers: buildHeaders(options),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    if (typeof detail === "string") {
      throw new Error(detail);
    }
    if (detail?.message) {
      throw new Error(detail.message);
    }
    throw new Error("HTTP " + response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}
