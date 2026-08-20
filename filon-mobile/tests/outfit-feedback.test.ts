import { describe, expect, it } from "vitest";

import { buildOutfitFeedbackKey, mergeOutfitFeedback, type OutfitFeedback } from "../lib/outfit-feedback";

describe("Outfit Studio feedback", () => {
  it("produit une clé stable quelle que soit la position des pièces", () => {
    expect(buildOutfitFeedbackKey(" Mariage simple ", [3, 1, 2])).toBe(buildOutfitFeedbackKey("mariage simple", [1, 2, 3]));
  });

  it("remplace le retour d’une même solution sans en conserver un doublon", () => {
    const existing: OutfitFeedback[] = [{ solutionKey: "a", value: "helpful", updatedAt: "2026-01-01T00:00:00.000Z" }, { solutionKey: "b", value: "needs_review", updatedAt: "2026-01-01T00:00:00.000Z" }];
    const merged = mergeOutfitFeedback(existing, { solutionKey: "a", value: "needs_review", updatedAt: "2026-02-01T00:00:00.000Z" });
    expect(merged).toEqual([{ solutionKey: "a", value: "needs_review", updatedAt: "2026-02-01T00:00:00.000Z" }, existing[1]]);
  });
});
