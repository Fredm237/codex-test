import { describe, expect, it } from "vitest";

import { catalogueSourceState } from "../lib/catalogue-source-state";

describe("catalogue source state", () => {
  it("does not describe a backend sync as fresh data", () => {
    expect(catalogueSourceState({ live: true, lastReading: "2026-08-16T10:00:00Z", readings24h: 0, drops24h: 0, dropsComparable: false, syncStatus: "syncing", lastSuccess: null, ageHours: 2 }, "fr")).toEqual({ label: "Synchronisation source en cours", tone: "pending" });
  });

  it("formats only an actual valid last reading", () => {
    const state = catalogueSourceState({ live: true, lastReading: "2026-08-14T21:33:44Z", readings24h: 0, drops24h: 0, dropsComparable: false, syncStatus: "idle", lastSuccess: null, ageHours: 2 }, "en", new Date("2026-08-14T22:00:00Z"));
    expect(state.label).toContain("Last reading");
    expect(state.tone).toBe("live");
  });

  it("expires the live source label after 24 hours", () => {
    const pulse = { live: true, lastReading: "2026-08-14T21:33:44Z", readings24h: 2, drops24h: 1, dropsComparable: true, syncStatus: "idle", lastSuccess: null, ageHours: 25 };
    expect(catalogueSourceState(pulse, "en", new Date("2026-08-15T22:00:00Z")).tone).toBe("muted");
  });
});
