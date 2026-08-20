import { describe, expect, it } from "vitest";

import { filterLookbook, lookbookFilterCounts } from "../lib/filon-lookbook-filters";
import type { LookbookSummary } from "../lib/filon-lookbook";

const summary: LookbookSummary = { totalOutfits: 2, totalPlans: 2, unplanned: [{ id: "two", title: "Two", mode: "create", total: 80, confidenceScore: 70, pieces: [], createdAt: "2026-08-16T00:00:00.000Z" }], planned: [{ occasion: { id: "p1", title: "Dîner", date: "2026-08-20", outfitId: "one", createdAt: "2026-08-16T00:00:00.000Z" }, outfit: { id: "one", title: "One", mode: "create", total: 70, confidenceScore: 70, pieces: [], createdAt: "2026-08-16T00:00:00.000Z" } }, { occasion: { id: "p2", title: "Fête", date: "2026-08-21", outfitId: "missing", createdAt: "2026-08-16T00:00:00.000Z" }, outfit: null }] };

describe("Filtres Lookbook FILON", () => {
  it("sépare les occasions avec tenue, sans tenue et les propositions non planifiées", () => {
    expect(filterLookbook(summary, "planned").count).toBe(1);
    expect(filterLookbook(summary, "orphaned").count).toBe(1);
    expect(filterLookbook(summary, "unplanned").outfits[0].id).toBe("two");
  });

  it("produit des compteurs locaux cohérents", () => {
    expect(lookbookFilterCounts(summary)).toEqual({ all: 3, planned: 1, unplanned: 1, orphaned: 1 });
  });
});
