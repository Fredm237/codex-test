import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";

import { runSingleFlight, type SingleFlightRef } from "../lib/single-flight";

describe("saved reconciliation single-flight", () => {
  it("shares one operation across simultaneous manual and automatic triggers", async () => {
    let release: (() => void) | undefined;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    const operation = vi.fn(async () => { await gate; });
    const pendingStates: boolean[] = [];
    const ref: SingleFlightRef<void> = { current: null };

    const manual = runSingleFlight(ref, operation, (pending) => pendingStates.push(pending));
    const automatic = runSingleFlight(ref, operation, (pending) => pendingStates.push(pending));

    expect(automatic).toBe(manual);
    await Promise.resolve();
    expect(operation).toHaveBeenCalledTimes(1);
    expect(pendingStates).toEqual([true]);
    release?.();
    await Promise.all([manual, automatic]);
    expect(pendingStates).toEqual([true, false]);
    expect(ref.current).toBeNull();
  });

  it("releases the lock after failure so a later retry can start", async () => {
    const ref: SingleFlightRef<string> = { current: null };
    await expect(runSingleFlight(ref, async () => { throw new Error("offline"); })).rejects.toThrow("offline");
    await expect(runSingleFlight(ref, async () => "retried")).resolves.toBe("retried");
  });

  it("keeps the production effect and button behind the full-cycle lock", () => {
    const saved = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "app", "(tabs)", "saved.tsx"), "utf8");
    expect(saved).toContain("runSingleFlight(reconcileFlight");
    expect(saved).toContain("syncing: reconcilePending || autoRetrying");
    expect(saved).toContain("disabled={reconcilePending || syncMutation.isPending || collectionMutation.isPending}");
  });
});
