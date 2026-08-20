import { describe, expect, it } from "vitest";

import { clearSyncRetry, delayForSyncAttempt, emptySyncRetryQueue, isSyncRetryDue, scheduleSyncRetry } from "../lib/sync-retry-queue";

describe("sync retry queue", () => {
  it("uses bounded gradual delays after each failure", () => {
    expect(delayForSyncAttempt(1)).toBe(5_000);
    expect(delayForSyncAttempt(2)).toBe(10_000);
    expect(delayForSyncAttempt(20)).toBe(300_000);
  });
  it("schedules and clears a retry deterministically", () => {
    const scheduled = scheduleSyncRetry(emptySyncRetryQueue, "2026-08-13T10:00:00.000Z");
    expect(scheduled).toMatchObject({ attempts: 1, nextRetryAt: "2026-08-13T10:00:05.000Z" });
    expect(isSyncRetryDue(scheduled, "2026-08-13T10:00:04.999Z")).toBe(false);
    expect(isSyncRetryDue(scheduled, "2026-08-13T10:00:05.000Z")).toBe(true);
    expect(clearSyncRetry()).toEqual(emptySyncRetryQueue);
  });
});
