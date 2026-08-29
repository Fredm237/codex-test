import { describe, expect, it } from "vitest";

import { compareOutfitStrategies } from "../lib/filon-strategy-comparison";

const strategy = (id: "safe" | "signature", total: number, pieceCount: number, currency = "EUR") => ({ id, label: id, description: { code: (id === "safe" ? "strategy.safe" : "strategy.signature") as "strategy.safe" | "strategy.signature" }, solution: { pieces: Array.from({ length: pieceCount }, (_, index) => ({ role: "base" as const, offer: { id: index, name: "Pièce", price: 10, currency, merchantName: "Partenaire", link: "https://example.com", inStock: true, observedAt: "2026-08-28T12:00:00.000Z", brand: null, category: null, imageUrl: null, merchantSlug: "partner" }, confidence: "medium" as const, provenance: "filon_inference" as const, explanation: { code: "piece.role_inferred" as const } })), total, currency, styleScore: null, confidenceScore: null, confidence: "not_calibrated" as const, measurementStatus: "not_calibrated" as const, scoreExplanation: { code: "score.not_measured" as const }, constraints: [], relations: [], critique: { verdict: "approved" as const, findings: [], scorePenalty: 0 } } });

describe("Comparateur de stratégies FILON", () => {
  it("compare les compromis explicites sans créer de préférence cachée", () => {
    const comparison = compareOutfitStrategies([strategy("safe", 120, 3), strategy("signature", 145, 3)]);
    expect(comparison.totalDifference).toBe(25);
    expect(comparison.confidenceDifference).toBeNull();
    expect(comparison.coverageDifference).toBe(0);
  });

  it("reste neutre si une seule stratégie est disponible", () => {
    expect(compareOutfitStrategies([strategy("safe", 120, 3)].sort()).totalDifference).toBeNull();
  });

  it("ne compare pas les totaux de deux devises différentes", () => {
    expect(compareOutfitStrategies([strategy("safe", 120, 3, "EUR"), strategy("signature", 145, 3, "USD")]).totalDifference).toBeNull();
  });
});
