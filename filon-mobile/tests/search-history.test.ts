import { describe, expect, it } from "vitest";

import { applyRecentSearch, normalizeSearchQuery } from "../lib/search-history";

describe("recent catalogue searches", () => {
  it("normalizes, deduplicates and keeps the latest six private queries", () => {
    const initial = [{ query: "Casque", at: "2026-01-01" }];
    const next = applyRecentSearch(initial, "  casque   bluetooth ", "2026-01-02");
    expect(next[0]).toEqual({ query: "casque bluetooth", at: "2026-01-02" });
    expect(normalizeSearchQuery("  ordinateur   portable ")).toBe("ordinateur portable");
    expect(applyRecentSearch(next, "CASQUE", "2026-01-03").map((item) => item.query)).toEqual(["CASQUE", "casque bluetooth"]);
  });
  it("does not persist a one-character query", () => {
    const initial = [{ query: "TV", at: "2026-01-01" }];
    expect(applyRecentSearch(initial, "x")).toBe(initial);
  });
});
