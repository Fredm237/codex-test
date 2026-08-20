export const CATALOGUE_REFRESH_INTERVAL_MS = 120_000;
export const CATALOGUE_RESUME_COOLDOWN_MS = 15_000;

export type CatalogueRefreshReason = "launch" | "foreground" | "network" | "interval";

const LIVE_QUERY_PREFIXES = new Set([
  "filon-catalogue-navigation",
  "filon-offer-feed",
  "filon-offers",
  "filon-catalogue-pulse",
  "filon-catalogue-relief",
]);

export function isLiveFilonQueryKey(queryKey: readonly unknown[]) {
  return typeof queryKey[0] === "string" && LIVE_QUERY_PREFIXES.has(queryKey[0]);
}

export function shouldRefreshCatalogue({
  reason,
  now,
  lastRefreshAt,
}: {
  reason: CatalogueRefreshReason;
  now: number;
  lastRefreshAt: number | null;
}) {
  if (lastRefreshAt === null || reason === "launch") return true;
  const elapsed = now - lastRefreshAt;
  return reason === "interval"
    ? elapsed >= CATALOGUE_REFRESH_INTERVAL_MS
    : elapsed >= CATALOGUE_RESUME_COOLDOWN_MS;
}
