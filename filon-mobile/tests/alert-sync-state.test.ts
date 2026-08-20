import { describe, expect, it } from "vitest";

import { resolveAlertSyncState } from "../lib/alert-sync-state";

describe("alert synchronization state", () => {
  it("requires a signed-in account before remote synchronization", () => {
    expect(resolveAlertSyncState({ hasAccount: false, hasAlerts: true, isSyncing: false, hasSucceeded: false, hasFailed: false })).toBe("needs-account");
  });

  it("shows a synchronized state only after a successful remote mutation", () => {
    expect(resolveAlertSyncState({ hasAccount: true, hasAlerts: true, isSyncing: false, hasSucceeded: true, hasFailed: false })).toBe("synced");
  });
});
