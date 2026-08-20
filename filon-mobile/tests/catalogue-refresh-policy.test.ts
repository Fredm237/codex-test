import { describe, expect, it } from "vitest";

import {
  CATALOGUE_REFRESH_INTERVAL_MS,
  isLiveFilonQueryKey,
  shouldRefreshCatalogue,
} from "../lib/catalogue-refresh-policy";

describe("catalogue automatic refresh policy", () => {
  it("targets only live catalogue query families", () => {
    expect(isLiveFilonQueryKey(["filon-offers", "laptop"])).toBe(true);
    expect(isLiveFilonQueryKey(["filon-catalogue-navigation"])).toBe(true);
    expect(isLiveFilonQueryKey(["trpc", "alerts"])).toBe(false);
  });

  it("refreshes on launch and throttles rapid foreground transitions", () => {
    expect(shouldRefreshCatalogue({ reason: "launch", now: 100, lastRefreshAt: null })).toBe(true);
    expect(shouldRefreshCatalogue({ reason: "foreground", now: 10_000, lastRefreshAt: 0 })).toBe(false);
    expect(shouldRefreshCatalogue({ reason: "foreground", now: 16_000, lastRefreshAt: 0 })).toBe(true);
  });

  it("revalidates active data on the controlled interval", () => {
    expect(shouldRefreshCatalogue({ reason: "interval", now: CATALOGUE_REFRESH_INTERVAL_MS - 1, lastRefreshAt: 0 })).toBe(false);
    expect(shouldRefreshCatalogue({ reason: "interval", now: CATALOGUE_REFRESH_INTERVAL_MS, lastRefreshAt: 0 })).toBe(true);
  });
});
