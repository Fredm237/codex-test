import { describe, expect, it } from "vitest";

import { buildLookbookSummary } from "../lib/filon-lookbook";
import type { SavedOutfit } from "../lib/filon-outfit-journal";

const outfit = (id: string): SavedOutfit => ({ id, title: id, mode: "create", total: 80, currency: "EUR", confidenceScore: null, measurementStatus: "not_calibrated", pieces: [], createdAt: "2026-08-16T00:00:00.000Z" });

describe("Lookbook FILON", () => {
  it("joint les occasions à leur tenue et garde les tenues sans occasion séparées", () => {
    const summary = buildLookbookSummary([outfit("one"), outfit("two")], [{ id: "p1", title: "Dîner", date: "2026-08-20", outfitId: "one", createdAt: "2026-08-16T00:00:00.000Z" }]);
    expect(summary.planned[0].outfit?.id).toBe("one");
    expect(summary.unplanned[0].id).toBe("two");
  });

  it("garde une occasion orpheline explicite au lieu d’inventer une tenue", () => {
    const summary = buildLookbookSummary([], [{ id: "p1", title: "Dîner", date: "2026-08-20", outfitId: "missing", createdAt: "2026-08-16T00:00:00.000Z" }]);
    expect(summary.planned[0].outfit).toBeNull();
  });
});
