import { describe, expect, it } from "vitest";

import { shouldAutoRetryCollectionSync } from "../lib/collection-sync-retry";

describe("collection sync recovery", () => {
  it("retries only an authenticated pending change after internet is reachable", () => {
    expect(shouldAutoRetryCollectionSync({ authenticated: true, pendingSync: true, internetReachable: true, syncing: false })).toBe(true);
    expect(shouldAutoRetryCollectionSync({ authenticated: true, pendingSync: true, internetReachable: false, syncing: false })).toBe(false);
    expect(shouldAutoRetryCollectionSync({ authenticated: false, pendingSync: true, internetReachable: true, syncing: false })).toBe(false);
    expect(shouldAutoRetryCollectionSync({ authenticated: true, pendingSync: true, internetReachable: true, syncing: true })).toBe(false);
  });
});
