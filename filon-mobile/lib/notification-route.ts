export function notificationProductPath(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const value = (payload as Record<string, unknown>).ean;
  const ean = typeof value === "string" ? value.replace(/\D/g, "") : "";
  return /^\d{8,14}$/.test(ean) ? `/product/ean/${ean}` : null;
}

export function notificationOccasionPath(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const occasionId = (payload as Record<string, unknown>).occasionId;
  return typeof occasionId === "string" && /^[a-zA-Z0-9-]{1,80}$/.test(occasionId)
    ? `/outfit-studio?occasionId=${encodeURIComponent(occasionId)}`
    : null;
}
