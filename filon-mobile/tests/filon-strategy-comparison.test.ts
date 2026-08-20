import { describe, expect, it } from "vitest";

import { compareOutfitStrategies } from "../lib/filon-strategy-comparison";

const strategy = (id: "safe" | "signature", total: number, confidenceScore: number, pieceCount: number) => ({ id, label: id, description: "", solution: { pieces: Array.from({ length: pieceCount }, (_, index) => ({ role: "base" as const, offer: { id: index, name: "Pièce", price: 10, currency: "EUR", merchantName: "Partenaire", link: "https://example.com", inStock: true, brand: null, category: null, imageUrl: null, merchantSlug: "partner" }, confidence: "medium" as const, provenance: "filon_inference" as const, explanation: "" })), total, styleScore: 70, confidenceScore, confidence: "medium" as const, scoreExplanation: "", constraints: [], relations: [], critique: { verdict: "approved" as const, findings: [], scorePenalty: 0 } } });

describe("Comparateur de stratégies FILON", () => {
  it("compare les compromis explicites sans créer de préférence cachée", () => {
    const comparison = compareOutfitStrategies([strategy("safe", 120, 78, 3), strategy("signature", 145, 82, 3)]);
    expect(comparison.totalDifference).toBe(25);
    expect(comparison.confidenceDifference).toBe(4);
    expect(comparison.coverageDifference).toBe(0);
  });

  it("reste neutre si une seule stratégie est disponible", () => {
    expect(compareOutfitStrategies([strategy("safe", 120, 78, 3)].sort()).totalDifference).toBeNull();
  });
});
