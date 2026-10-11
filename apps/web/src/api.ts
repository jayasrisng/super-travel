import type { components } from "./api.generated";
export type Schema = components["schemas"];
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  version?: number,
): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method === "POST" && !path.includes("/demo/session"))
    headers["Idempotency-Key"] = crypto.randomUUID();
  if (version !== undefined) headers["If-Match"] = `"${version}"`;
  const response = await fetch("/v1" + path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "same-origin",
  });
  if (response.status === 204) return undefined as T;
  const payload = await response.json();
  if (!response.ok)
    throw new Error(
      payload.error?.message || `Request failed (${response.status})`,
    );
  return payload.data as T;
}
export const consumer = "/consumer";
export const agents: Record<Schema["Task"]["assigned_agent"], string> = {
  plan_book: "Plan & Book",
  pack_shop: "Pack & Shop",
  explore_magic: "Explore & Experience",
  essentials: "Travel Essentials",
  recovery: "Manage & Recover",
};
