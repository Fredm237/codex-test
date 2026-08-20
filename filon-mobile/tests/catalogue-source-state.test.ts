import { describe, expect, it } from "vitest";

import { catalogueSourceState } from "../lib/catalogue-source-state";

describe("catalogue source state", () => {
  it("does not describe a backend sync as fresh data", () => {
    expect(catalogueSourceState({ live: true, lastReading: "2026-08-16T10:00:00Z", readings24h: 0, drops24h: 0, syncStatus: "syncing", lastSuccess: null, ageHours: 2 }, "fr")).toEqual({ label: "Synchronisation source en cours", tone: "pending" });
  });

  it("formats only an actual valid last reading", () => {
    const state = catalogueSourceState({ live: true, lastReading: "2026-08-14T21:33:44Z", readings24h: 0, drops24h: 0, syncStatus: "idle", lastSuccess: null, ageHours: 48 }, "en");
    expect(state.label).toContain("Last reading");
    expect(state.tone).toBe("live");
  });
});
